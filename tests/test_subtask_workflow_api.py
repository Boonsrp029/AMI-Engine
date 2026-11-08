import json
import threading

import pytest
from fastapi.testclient import TestClient

from src.pilot.api import create_app
from src.pilot.engine import Corpus
from src.pilot._identity import allowed


class SyntheticExecutor:
    """Only records API dispatch; lifecycle execution belongs to owned-runner tests."""

    def __init__(self):
        self.calls = []
        self.called = threading.Event()

    def execute(self, store, run_id, plan, corpus_path, *, lease=None):
        self.calls.append((run_id, plan.plan_id, str(corpus_path), lease))
        self.called.set()


@pytest.fixture
def corpus(tmp_path):
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps([{"feed_id": "f1", "title": "Exports",
        "clean_content": "Fictional exports increased in the test corpus."}]), encoding="utf-8")
    return Corpus(path)


def payload(request_key="bounded-test-key-01", query="Compare export growth"):
    return {"query": query, "request_key": request_key,
        "subtasks": [{"subtask_id": "s01", "operation": "retrieve", "query": "export growth"}],
        "retrieval_concurrency": 2, "deadline_seconds": 30}


def test_default_session_disables_bounded_workflow_and_preserves_sequential_route(corpus, tmp_path):
    app = create_app(engine=type("Engine", (), {"corpus": corpus})(),
        database_path=tmp_path / "pilot.db")
    with TestClient(app, base_url="http://127.0.0.1", headers={"X-Pilot-Token": app.state.token}) as client:
        session = client.get("/api/session").json()
        assert session["capabilities"] == {"sequential": True, "bounded_subtasks": False}
        assert session["workflow_modes"]["bounded_subtasks"] == "disabled"
        response = client.post("/api/runs/subtasks", json=payload())
        assert response.status_code == 409
        sequential = client.post("/api/runs", json={"query": "Compare export growth",
            "request_key": "sequential-test-key-01"})
        assert sequential.status_code == 202
        assert set(sequential.json()) == {"id", "created"}
        assert client.get("/api/runs/by-request/sequential-test-key-01").json() == {
            "id": sequential.json()["id"], "workflow": "sequential"}


def test_submit_is_plan_bound_atomic_and_lookup_is_minimal(corpus, tmp_path):
    worker = SyntheticExecutor()
    app = create_app(engine=type("Engine", (), {"corpus": corpus})(),
        database_path=tmp_path / "pilot.db", subtask_executor=worker)
    with TestClient(app, base_url="http://127.0.0.1", headers={"X-Pilot-Token": app.state.token}) as client:
        session = client.get("/api/session").json()
        assert session["capabilities"] == {"sequential": True, "bounded_subtasks": True}
        assert session["workflow_modes"]["bounded_subtasks"] == "synthetic_test"
        first = client.post("/api/runs/subtasks", json=payload())
        assert first.status_code == 202
        assert first.json()["workflow"] == "bounded_subtasks"
        assert worker.called.wait(2)
        run_id = first.json()["id"]
        assert len(worker.calls) == 1 and worker.calls[0][0] == run_id
        assert client.get("/api/runs/by-request/bounded-test-key-01").json() == {
            "id": run_id, "workflow": "bounded_subtasks"}
        replay = client.post("/api/runs/subtasks", json=payload())
        assert replay.status_code == 202
        assert replay.json() == {"id": run_id, "created": False, "workflow": "bounded_subtasks"}
        assert len(worker.calls) == 1
        progress = client.get(f"/api/runs/{run_id}/progress").json()["progress"]
        assert progress["mode"] == "subtasks" and progress["phase"] == "queued"
        assert progress["branches"][0]["subtask_id"] == "s01"
        assert progress["branches"][0]["child_attempt_id"] is None
        assert set(client.get(f"/api/runs/{run_id}").json()["events"][-1]["payload"]) == {
            "workflow", "plan_id", "plan"}


def test_request_key_rejects_changed_plan_query_or_workflow(corpus, tmp_path):
    worker = SyntheticExecutor()
    app = create_app(engine=type("Engine", (), {"corpus": corpus})(),
        database_path=tmp_path / "pilot.db", subtask_executor=worker)
    with TestClient(app, base_url="http://127.0.0.1", headers={"X-Pilot-Token": app.state.token}) as client:
        first = client.post("/api/runs/subtasks", json=payload())
        assert first.status_code == 202
        assert worker.called.wait(2)
        changed_query = client.post("/api/runs/subtasks", json=payload(query="Different question"))
        assert changed_query.status_code == 409
        changed_plan_body = payload()
        changed_plan_body["subtasks"][0]["query"] = "a different subtask"
        assert client.post("/api/runs/subtasks", json=changed_plan_body).status_code == 409
        assert client.post("/api/runs", json={"query": "Compare export growth",
            "request_key": "bounded-test-key-01"}).status_code == 409
        assert len(worker.calls) == 1


def test_route_permissions():
    assert allowed("analyst", "GET", "/api/runs/by-request/some-key-123")
    assert not allowed("reader", "GET", "/api/runs/by-request/some-key-123")
    assert allowed("operator", "POST", "/api/runs/subtasks")
    assert not allowed("reviewer", "POST", "/api/runs/subtasks")


def test_invalid_explicit_plan_is_rejected_without_dispatch(corpus, tmp_path):
    worker = SyntheticExecutor()
    app = create_app(engine=type("Engine", (), {"corpus": corpus})(),
        database_path=tmp_path / "pilot.db", subtask_executor=worker)
    invalid = payload()
    invalid["subtasks"].append({"subtask_id": "s02", "operation": "retrieve",
        "query": "bad dependency", "dependencies": ["unknown"]})
    with TestClient(app, base_url="http://127.0.0.1", headers={"X-Pilot-Token": app.state.token}) as client:
        assert client.post("/api/runs/subtasks", json=invalid).status_code == 422
        assert not worker.calls


def test_unknown_request_key_lookup_returns_404(corpus, tmp_path):
    app = create_app(engine=type("Engine", (), {"corpus": corpus})(),
        database_path=tmp_path / "pilot.db")
    with TestClient(app, base_url="http://127.0.0.1", headers={"X-Pilot-Token": app.state.token}) as client:
        assert client.get("/api/runs/by-request/missing-key-0001").status_code == 404


