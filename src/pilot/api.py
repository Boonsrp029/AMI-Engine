"""Local browser/API entrypoint: uvicorn src.pilot.api:create_app --factory."""

import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import ValidationError

from src.pilot.engine import Corpus, PilotEngine
from src.pilot.schemas import EditRequest, ResearchRequest, ReviewRequest, SubtaskResearchRequest
from src.pilot.store import Conflict, QueueFull, Store
from src.pilot._readiness import readiness
from src.pilot._runtime import ProcessRuntime
from src.pilot._identity import allowed, authenticate, load_principals
from src.pilot._request_body import RequestBodyLimit
from src.pilot._validation_errors import public_validation_details
from src.pilot.subtasks.api_runtime import OwnedSubtaskExecutor


def create_app(corpus_path=None, database_path=None, engine=None, run_inline=False, *, subtask_executor=None):
    principals = load_principals(os.getenv("AMI_PILOT_IDENTITY_FILE"))
    corpus_path = corpus_path or os.getenv("AMI_PILOT_CORPUS", "data/external/market_sources/prepared/market_chunks.json")
    database_path = database_path or os.getenv("AMI_PILOT_DB", "reports/workflow_pilot/pilot.sqlite3")
    corpus = engine.corpus if engine else Corpus(corpus_path)
    controlled_engine = engine is not None or run_inline
    if (subtask_executor is not None and not controlled_engine
            and not isinstance(subtask_executor, OwnedSubtaskExecutor)):
        raise ValueError("Production subtask capability requires OwnedSubtaskExecutor")
    engine = (engine or PilotEngine(corpus)) if controlled_engine else None
    store = Store(database_path, queue_limit=2)
    if controlled_engine:
        runtime = None
    elif subtask_executor is None:
        # Keep the default sequential constructor call compatible with existing
        # runtime adapters and test doubles that implement the original API.
        runtime = ProcessRuntime(store, corpus.path, corpus.sha)
    else:
        runtime = ProcessRuntime(store, corpus.path, corpus.sha,
                                 subtask_executor=subtask_executor)
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ami-pilot") if controlled_engine else None
    token = secrets.token_hex(24)

    def execute(run_id):
        if not store.claim(run_id):
            return
        try:
            run = store.get(run_id)
            result = engine.run(run["query"], lambda kind, payload: store.event(run_id, kind, payload))
            store.save_draft(run_id, result["draft"], result["sources"], result["metrics"])
        except Exception as exc:
            # Never expose API keys, provider response bodies or raw exception text.
            store.event(run_id, "run_failure", {"type": type(exc).__name__})
            store.fail(run_id, f"Workflow failed ({type(exc).__name__}); inspect the event history and retry safely")

    def submit(run_id):
        if runtime is not None:
            try:
                runtime.submit(run_id)
            except RuntimeError:
                store.cancel(run_id)
                raise HTTPException(503, "Analyst runtime is stopping") from None
        elif run_inline:
            execute(run_id)
        else:
            executor.submit(execute, run_id)

    def execute_subtasks(run_id):
        try:
            plan = store.subtask_plan(run_id)
            subtask_executor.execute(store, run_id, plan, corpus.path)
        except Conflict as exc:
            # A cancellation, retry, or active duplicate owns the persisted state.
            try:
                if store.get(run_id)["status"] == "queued":
                    store.fail_queued(run_id, type(exc).__name__)
            except (KeyError, Conflict):
                pass
            return
        except Exception as exc:
            # A claimed runner records its own failed attempt. This covers only a
            # plan that could not be loaded/started while still queued.
            store.fail_queued(run_id, type(exc).__name__)

    def submit_subtasks(run_id):
        if subtask_executor is None:
            raise Conflict("Bounded subtask workflow is disabled")
        if runtime is not None:
            try:
                runtime.submit(run_id)
            except RuntimeError:
                store.cancel(run_id)
                raise HTTPException(503, "Analyst runtime is stopping") from None
        elif run_inline:
            execute_subtasks(run_id)
        else:
            executor.submit(execute_subtasks, run_id)

    @asynccontextmanager
    async def lifespan(_):
        if runtime is not None:
            runtime.start()
        else:
            store.recover()
        try:
            yield
        finally:
            if runtime is not None:
                runtime.shutdown()
            else:
                executor.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title="AMI Analyst Pilot", version="1.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store, app.state.token = store, token
    app.state.runtime = runtime
    # Registered before the browser/auth middleware so denied requests are not
    # buffered. The inner boundary counts received bytes, including chunked data.
    app.add_middleware(RequestBodyLimit)

    @app.middleware("http")
    async def local_browser_boundary(request: Request, call_next):
        host = request.headers.get("host", "").split(":")[0].lower()
        if host not in {"127.0.0.1", "localhost"}:
            return PlainTextResponse("Local pilot host required", status_code=403)
        try:
            if int(request.headers.get("content-length", "0")) > 100_000:
                return PlainTextResponse("Pilot request is too large", status_code=413)
        except ValueError:
            return PlainTextResponse("Invalid content length", status_code=400)
        origin = request.headers.get("origin")
        if origin and origin != f"{request.url.scheme}://{request.headers.get('host')}":
            return PlainTextResponse("Cross-origin requests are disabled", status_code=403)
        if request.url.path.startswith("/api/"):
            supplied = request.headers.get("x-pilot-token", "")
            if principals is not None:
                principal = authenticate(supplied, principals)
                if principal is None or not allowed(principal.role, request.method, request.url.path):
                    return PlainTextResponse("Pilot access denied", status_code=403)
                request.state.principal = principal
            elif not secrets.compare_digest(supplied, token):
                return PlainTextResponse("Pilot session token required", status_code=403)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_, exc):
        # The default handler echoes rejected input, including PII and arbitrary
        # extra-field names. Preserve status/envelope without those values.
        return JSONResponse({"detail": public_validation_details(exc.errors())}, status_code=422)

    @app.exception_handler(Conflict)
    async def conflict(_, exc):
        return PlainTextResponse(str(exc), status_code=409)

    @app.exception_handler(QueueFull)
    async def queue_full(_, exc):
        return PlainTextResponse(str(exc), status_code=429, headers={"Retry-After": "5"})

    @app.exception_handler(KeyError)
    async def missing(_, exc):
        return PlainTextResponse("Run not found", status_code=404)

    @app.get("/", response_class=HTMLResponse)
    def home():
        html = Path(__file__).with_name("index.html").read_text(encoding="utf-8")
        return html.replace("__PILOT_TOKEN__", token if principals is None else "")

    @app.get("/api/session")
    def session(request: Request):
        principal = getattr(request.state, "principal", None)
        execution_mode = ("disabled" if subtask_executor is None else
                          "owned_runner" if isinstance(subtask_executor, OwnedSubtaskExecutor) else
                          "synthetic_test")
        return {"mode": "principal-tokens" if principal else "supervised-bootstrap",
                "identity": principal.identity if principal else None, "role": principal.role if principal else "operator",
                "capabilities": {"sequential": True, "bounded_subtasks": subtask_executor is not None},
                "workflow_modes": {"sequential": "sequential", "bounded_subtasks": execution_mode}}

    def audit(http, run_id, action):
        principal = getattr(http.state, "principal", None)
        if principal is not None:
            # This records an authorized attempt, never an inferred success.
            # Review identity itself is saved atomically in the decision payload.
            store.event(run_id, "authorized_action_attempt", {"identity": principal.identity,
                "role": principal.role, "action": action})

    @app.get("/health")
    def health():
        return {"status": "corpus-ready", "mode": "supervised-local", "corpus_sha256": corpus.sha,
                "model_readiness": "not-probed"}

    @app.get("/ready")
    def ready():
        result = readiness(store.path)
        if runtime is not None:
            healthy = runtime.thread is not None and runtime.thread.is_alive() and not runtime.stopping.is_set()
            result["checks"]["runtime"] = "ready" if healthy else "unavailable"
            if not healthy:
                result["status"] = "unavailable"
        return JSONResponse(result, status_code=200 if result["status"] == "ready" else 503)

    @app.get("/api/runs")
    def runs():
        return store.list()

    @app.post("/api/runs", status_code=202)
    def create(request: ResearchRequest, http: Request):
        run_id, created = store.create(request, corpus.sha)
        if created:
            audit(http, run_id, "create")
            submit(run_id)
        return {"id": run_id, "created": created}

    @app.post("/api/runs/subtasks", status_code=202)
    def create_subtasks(request: SubtaskResearchRequest, http: Request):
        if subtask_executor is None:
            raise Conflict("Bounded subtask workflow is disabled")
        try:
            plan = request.make_plan(corpus.sha)
        except ValidationError:
            raise HTTPException(422, "Invalid bounded subtask plan") from None
        run_id, created = store.create_subtask(request, plan)
        if created:
            audit(http, run_id, "create_bounded_subtasks")
            submit_subtasks(run_id)
        return {"id": run_id, "created": created, "workflow": "bounded_subtasks"}

    @app.get("/api/runs/by-request/{request_key}")
    def by_request(request_key: str):
        return store.workflow_for_request(request_key)

    @app.get("/api/runs/{run_id}")
    def get(run_id: str):
        return store.get(run_id)

    @app.get("/api/runs/{run_id}/progress")
    def progress(run_id: str):
        from src.pilot.subtasks.persistence import progress_view
        run = store.get(run_id)
        return {"run": run, "progress": progress_view(run, detailed=True),
                "sequence": max((event["seq"] for event in run["events"]), default=0)}

    @app.post("/api/runs/{run_id}/retry", status_code=202)
    def retry(run_id: str, http: Request):
        run = store.get(run_id)
        workflow = "bounded_subtasks" if any(event["kind"] in {
            "subtask_submission", "subtask_plan", "subtask_progress", "subtask_result"}
            for event in run["events"]) else "sequential"
        if workflow == "bounded_subtasks" and subtask_executor is None:
            raise Conflict("Bounded subtask workflow is disabled; the stored task was not changed")
        if run["corpus_sha"] != corpus.sha:
            raise Conflict("The corpus has changed; create a new task to preserve the old task's provenance")
        audit(http, run_id, "retry")
        store.retry(run_id)
        submit_subtasks(run_id) if workflow == "bounded_subtasks" else submit(run_id)
        return {"id": run_id}

    @app.post("/api/runs/{run_id}/cancel")
    def cancel(run_id: str, http: Request):
        run = store.get(run_id)
        is_subtasks = any(event["kind"] in {
            "subtask_submission", "subtask_plan", "subtask_progress", "subtask_result"}
            for event in run["events"])
        if runtime is None and not (is_subtasks and subtask_executor is not None):
            raise Conflict("Owned-process cancellation is unavailable for an injected test engine")
        audit(http, run_id, "cancel")
        if runtime is None:
            store.cancel(run_id)
        else:
            runtime.cancel(run_id)
        return {"id": run_id, "status": store.get(run_id)["status"]}

    @app.put("/api/runs/{run_id}/draft")
    def edit(run_id: str, request: EditRequest, http: Request):
        run = store.get(run_id)
        audit(http, run_id, "edit")
        try:
            revision = store.save_draft(run_id, request.draft.model_dump(), run["sources"], run["metrics"], request.revision)
        except ValueError as exc:
            if isinstance(exc, Conflict):
                raise
            raise HTTPException(422, str(exc)) from exc
        return {"revision": revision}

    @app.post("/api/runs/{run_id}/review")
    def review(run_id: str, request: ReviewRequest, http: Request):
        principal = getattr(http.state, "principal", None)
        if principal is not None and request.reviewer != principal.identity:
            raise HTTPException(403, "Reviewer must match the authenticated identity")
        store.get(run_id)
        audit(http, run_id, "review")
        store.review(run_id, request)
        return {"status": store.get(run_id)["status"]}

    @app.get("/api/runs/{run_id}/export")
    def export(run_id: str, http: Request):
        store.get(run_id)
        audit(http, run_id, "export")
        content, revision = store.export(run_id)
        return PlainTextResponse(content, headers={"Content-Disposition": f'attachment; filename="ami-{run_id}-v{revision}.md"'})

    return app
