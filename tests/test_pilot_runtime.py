"""Actual spawned synthetic workers; no local/hosted inference or human ratings."""
import hashlib
import importlib
import json
from pathlib import Path
import time
import threading

from fastapi.testclient import TestClient
import pytest

from src.pilot import api
from src.pilot._runtime import ProcessRuntime
from src.pilot.schemas import ResearchRequest, ReviewRequest
from src.pilot.store import Conflict, Store


def until(predicate, timeout=15):
    stop = time.monotonic() + timeout
    while time.monotonic() < stop:
        value = predicate()
        if value:
            return value
        time.sleep(0.02)
    raise AssertionError("Synthetic runtime condition did not complete within bound")


@pytest.fixture
def setup_runtime(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(Path("tests/fixtures/workers").resolve()))
    child = importlib.import_module("runtime_child")
    path = tmp_path / "corpus.json"
    path.write_bytes(Path("tests/fixtures/release/smoke_corpus.json").read_bytes())
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    store = Store(tmp_path / "reviews.sqlite3", queue_limit=2)
    runtime = ProcessRuntime(store, path, sha, deadline_seconds=2, worker=child.run)
    runtime.start()
    yield runtime, store, path
    runtime.shutdown()


def submit(runtime, store, query, key="synthetic-request"):
    rid, _ = store.create(ResearchRequest(query=query, request_key=key), runtime.corpus_sha)
    runtime.submit(rid)
    return rid


def finished(store, rid):
    return until(lambda: (row if (row := store.get(rid))["status"] not in {"queued", "running"} else None))


def test_clean_exit_is_required_and_approval_export_contract_survives(setup_runtime):
    runtime, store, _ = setup_runtime
    rid = submit(runtime, store, "valid success")
    row = finished(store, rid)
    assert row["status"] == "needs_review" and row["revision"] == 1
    assert row["metrics"]["execution_deadline_seconds"] == 2
    assert row["metrics"]["queue_wait_seconds"] >= 0
    with pytest.raises(Conflict):
        store.export(rid)
    store.review(rid, ReviewRequest(revision=1, decision="approve", reviewer="synthetic-test-only", support_confirmed=True))
    assert store.export(rid) == store.export(rid)
    with pytest.raises(Conflict):
        runtime.cancel(rid)


@pytest.mark.parametrize("query,reason", [("hang model", "deadline"), ("hang guard", "deadline"),
    ("result then hang", "deadline"), ("result then crash", "worker_exit"),
    ("malformed message", "invalid_message"), ("oversized message", "invalid_message"),
    ("event after result", "invalid_message")])
def test_failures_never_publish_candidate_and_next_job_can_run(setup_runtime, query, reason):
    runtime, store, _ = setup_runtime
    rid = submit(runtime, store, query)
    row = finished(store, rid)
    assert row["status"] == "failed" and row["draft"] is None and row["revision"] == 0
    assert row["metrics"]["failure_reason"] == reason
    assert row["metrics"]["token_usage_complete"] is False
    if query == "hang guard":
        assert row["metrics"]["guardrail_invocations"] == 1
        assert row["metrics"]["known_input_tokens"] == 7
    next_id = submit(runtime, store, "empty success", "next-synthetic-request")
    assert finished(store, next_id)["status"] == "needs_review"


def test_cancel_kills_owned_worker_and_cancels_queued_without_starting_it(setup_runtime):
    runtime, store, _ = setup_runtime
    rid = submit(runtime, store, "hang model")
    until(lambda: any(e["kind"] == "model_request_started" for e in store.get(rid)["events"]))
    with runtime.lock:
        worker = runtime.active["process"]
    queued = submit(runtime, store, "valid success", "queued-synthetic-request")
    runtime.cancel(queued)
    assert not any(e["kind"] == "worker_started" for e in store.get(queued)["events"])
    runtime.cancel(rid)
    assert not worker.is_alive()
    assert store.get(rid)["status"] == "interrupted" and store.get(rid)["revision"] == 0
    assert store.get(rid)["metrics"]["model_calls"] == 1


def test_no_automatic_retry_and_explicit_retry_creates_new_attempt(setup_runtime):
    runtime, store, _ = setup_runtime
    rid = submit(runtime, store, "fail once")
    assert finished(store, rid)["status"] == "failed"
    time.sleep(0.25)
    assert len([e for e in store.get(rid)["events"] if e["kind"] == "attempt_started"]) == 1
    store.retry(rid)
    runtime.submit(rid)
    assert finished(store, rid)["status"] == "needs_review"
    ids = [e["payload"]["attempt_id"] for e in store.get(rid)["events"] if e["kind"] == "attempt_started"]
    assert len(set(ids)) == 2


def test_changed_corpus_and_second_runtime_fail_without_corrupting_owner(setup_runtime):
    runtime, store, path = setup_runtime
    other = ProcessRuntime(Store(store.path), path, runtime.corpus_sha)
    with pytest.raises(RuntimeError, match="owns this database"):
        other.start()
    other.shutdown()
    assert runtime.thread.is_alive()
    path.write_text("[]", encoding="utf-8")
    rid = submit(runtime, store, "valid success")
    row = finished(store, rid)
    assert row["metrics"]["failure_reason"] == "corpus_changed"
    assert not any(e["kind"] == "worker_started" for e in row["events"])


def test_corpus_changed_during_execution_prevents_publication(setup_runtime):
    runtime, store, path = setup_runtime
    rid = submit(runtime, store, "wait then finish")
    until(lambda: any(e["kind"] == "model_call" for e in store.get(rid)["events"]))
    path.write_text("[]", encoding="utf-8")
    path.with_suffix(".release").write_text("release synthetic worker", encoding="utf-8")
    assert finished(store, rid)["metrics"]["failure_reason"] == "corpus_changed"


def test_shutdown_reaps_active_and_recovers_queued_without_drafts(setup_runtime):
    runtime, store, _ = setup_runtime
    rid = submit(runtime, store, "hang guard")
    until(lambda: any(e["kind"] == "guard_invocation_started" for e in store.get(rid)["events"]))
    queued = submit(runtime, store, "valid success", "queued-before-shutdown")
    runtime.shutdown()
    assert runtime.active is None and not runtime.thread.is_alive()
    assert all(store.get(i)["status"] == "interrupted" and store.get(i)["revision"] == 0 for i in [rid, queued])


def test_http_factory_uses_process_runtime_and_authenticated_cancellation(monkeypatch, tmp_path):
    monkeypatch.syspath_prepend(str(Path("tests/fixtures/workers").resolve()))
    child = importlib.import_module("runtime_child")
    monkeypatch.setattr(api, "ProcessRuntime", lambda store, path, sha: ProcessRuntime(store, path, sha, worker=child.run, deadline_seconds=3))
    app = api.create_app(corpus_path="tests/fixtures/release/smoke_corpus.json", database_path=tmp_path / "api.sqlite3")
    with TestClient(app, base_url="http://127.0.0.1", headers={"X-Pilot-Token": app.state.token}) as client:
        rid = client.post("/api/runs", json={"query": "hang model", "request_key": "http-synthetic-run"}).json()["id"]
        until(lambda: any(e["kind"] == "model_request_started" for e in app.state.store.get(rid)["events"]))
        assert client.post(f"/api/runs/{rid}/cancel", headers={"X-Pilot-Token": "wrong"}).status_code == 403
        canceled = client.post(f"/api/runs/{rid}/cancel")
        assert canceled.status_code == 200 and canceled.json()["status"] == "interrupted"
        assert client.get(f"/api/runs/{rid}/export").status_code == 409


def test_cancellation_and_dispatcher_never_poll_process_concurrently(setup_runtime, monkeypatch):
    runtime, store, _ = setup_runtime
    entered, release, cancel_started = threading.Event(), threading.Event(), threading.Event()
    lifecycle = threading.Lock()
    original = runtime.context.Process
    errors = []

    class CheckedProcess:
        def __init__(self, *args, **kwargs):
            self.child = original(*args, **kwargs)
            self.first_poll = True

        def __getattr__(self, name):
            return getattr(self.child, name)

        def is_alive(self):
            assert lifecycle.acquire(blocking=False), "Concurrent process lifecycle access"
            try:
                if self.first_poll:
                    self.first_poll = False
                    entered.set()
                    assert release.wait(5)
                return self.child.is_alive()
            finally:
                lifecycle.release()

    monkeypatch.setattr(runtime.context, "Process", CheckedProcess)
    rid = submit(runtime, store, "hang model")
    assert entered.wait(5)
    def cancel():
        cancel_started.set()
        try:
            runtime.cancel(rid)
        except Exception as exc:
            errors.append(type(exc).__name__)
    thread = threading.Thread(target=cancel)
    thread.start()
    assert cancel_started.wait(2)
    time.sleep(0.05)
    release.set()
    thread.join(timeout=5)
    assert not thread.is_alive() and not errors
    assert finished(store, rid)["status"] == "interrupted"
    assert runtime.thread.is_alive()


def test_actual_default_worker_rejects_scope_without_model_calls(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("NEMO_GUARDRAILS_NO_USAGE_STATS", "1")
    app = api.create_app(corpus_path="tests/fixtures/release/smoke_corpus.json", database_path=tmp_path / "actual.sqlite3")
    with TestClient(app, base_url="http://127.0.0.1", headers={"X-Pilot-Token": app.state.token}) as client:
        rid = client.post("/api/runs", json={"query": "Give me personal financial advice", "request_key": "actual-process-no-inference"}).json()["id"]
        row = until(lambda: (r if (r := app.state.store.get(rid))["status"] not in {"queued", "running"} else None), timeout=120)
        assert row["status"] == "needs_review" and row["draft"]["claims"] == []
        assert row["metrics"]["model_calls"] == row["metrics"]["guardrail_invocations"] == 0
        assert row["metrics"]["execution_deadline_seconds"] == 180
        assert client.get(f"/api/runs/{rid}/export").status_code == 409
