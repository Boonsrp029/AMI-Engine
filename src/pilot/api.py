"""Local browser/API entrypoint: uvicorn src.pilot.api:create_app --factory."""

import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from src.pilot.engine import Corpus, PilotEngine
from src.pilot.schemas import EditRequest, ResearchRequest, ReviewRequest
from src.pilot.store import Conflict, Store


def create_app(corpus_path=None, database_path=None, engine=None, run_inline=False):
    corpus_path = corpus_path or os.getenv("AMI_PILOT_CORPUS", "data/external/market_sources/prepared/market_chunks.json")
    database_path = database_path or os.getenv("AMI_PILOT_DB", "reports/workflow_pilot/pilot.sqlite3")
    corpus = engine.corpus if engine else Corpus(corpus_path)
    engine = engine or PilotEngine(corpus)
    store = Store(database_path)
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ami-pilot")
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
        if run_inline:
            execute(run_id)
        else:
            executor.submit(execute, run_id)

    @asynccontextmanager
    async def lifespan(_):
        store.recover()
        yield
        executor.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title="AMI Analyst Pilot", version="1.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store, app.state.token = store, token

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
        if request.url.path.startswith("/api/") and not secrets.compare_digest(request.headers.get("x-pilot-token", ""), token):
            return PlainTextResponse("Pilot session token required", status_code=403)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        return response

    @app.exception_handler(Conflict)
    async def conflict(_, exc):
        return PlainTextResponse(str(exc), status_code=409)

    @app.exception_handler(KeyError)
    async def missing(_, exc):
        return PlainTextResponse("Run not found", status_code=404)

    @app.get("/", response_class=HTMLResponse)
    def home():
        html = Path(__file__).with_name("index.html").read_text(encoding="utf-8")
        return html.replace("__PILOT_TOKEN__", token)

    @app.get("/health")
    def health():
        return {"status": "corpus-ready", "mode": "supervised-local", "corpus_sha256": corpus.sha,
                "model_readiness": "not-probed"}

    @app.get("/api/runs")
    def runs():
        return store.list()

    @app.post("/api/runs", status_code=202)
    def create(request: ResearchRequest):
        run_id, created = store.create(request, corpus.sha)
        if created:
            submit(run_id)
        return {"id": run_id, "created": created}

    @app.get("/api/runs/{run_id}")
    def get(run_id: str):
        return store.get(run_id)

    @app.post("/api/runs/{run_id}/retry", status_code=202)
    def retry(run_id: str):
        run = store.get(run_id)
        if run["corpus_sha"] != corpus.sha:
            raise Conflict("The corpus has changed; create a new task to preserve the old task's provenance")
        store.retry(run_id)
        submit(run_id)
        return {"id": run_id}

    @app.put("/api/runs/{run_id}/draft")
    def edit(run_id: str, request: EditRequest):
        run = store.get(run_id)
        try:
            revision = store.save_draft(run_id, request.draft.model_dump(), run["sources"], run["metrics"], request.revision)
        except ValueError as exc:
            if isinstance(exc, Conflict):
                raise
            raise HTTPException(422, str(exc)) from exc
        return {"revision": revision}

    @app.post("/api/runs/{run_id}/review")
    def review(run_id: str, request: ReviewRequest):
        store.review(run_id, request)
        return {"status": store.get(run_id)["status"]}

    @app.get("/api/runs/{run_id}/export")
    def export(run_id: str):
        content, revision = store.export(run_id)
        return PlainTextResponse(content, headers={"Content-Disposition": f'attachment; filename="ami-{run_id}-v{revision}.md"'})

    return app
