"""Atomic queue admission tests; no model or external services."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from src.pilot.api import create_app
from src.pilot.engine import Corpus
from src.pilot.schemas import ResearchRequest
from src.pilot.store import Conflict, QueueFull, Store


def request(index):
    return ResearchRequest(query=f"Synthetic request {index}", request_key=f"admission-request-{index}")


def test_concurrent_admission_is_bounded_and_duplicate_remains_idempotent(tmp_path):
    store = Store(tmp_path / "queue.sqlite3", queue_limit=2)
    def submit(index):
        try:
            return store.create(request(index), "corpus")[0]
        except QueueFull:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(submit, range(20)))
    accepted = [rid for rid in results if rid]
    assert len(accepted) == 2
    assert len(store.list()) == 2
    index = next(i for i, rid in enumerate(results) if rid)
    assert store.create(request(index), "corpus") == (results[index], False)
    with pytest.raises(Conflict, match="different input"):
        store.create(request(index), "changed-corpus")
    assert store.claim(accepted[0])
    store.create(request(99), "corpus")
    assert len(store.list()) == 3  # One running and two queued.


def test_full_queue_does_not_mutate_interrupted_task_on_retry(tmp_path):
    store = Store(tmp_path / "queue.sqlite3", queue_limit=2)
    rid, _ = store.create(request(0), "corpus")
    store.recover()
    before = store.get(rid)
    store.create(request(1), "corpus")
    store.create(request(2), "corpus")
    with pytest.raises(QueueFull):
        store.retry(rid)
    assert store.get(rid) == before
    with pytest.raises(Conflict, match="Only failed"):
        store.retry("unknown")
    active = next(r for r in store.list() if r["status"] == "queued")
    assert store.claim(active["id"])
    store.retry(rid)
    assert store.get(rid)["status"] == "queued"


def test_http_saturation_returns_429_without_creating_or_executing_excess_task(tmp_path):
    entered, release = Event(), Event()
    corpus = Corpus("tests/fixtures/release/smoke_corpus.json")
    def run(query, event):
        entered.set()
        assert release.wait(5), "Synthetic blocking engine was not released"
        return {"draft": {"title": "Synthetic empty draft", "claims": [], "warnings": []}, "sources": {}, "metrics": {}}
    app = create_app(engine=SimpleNamespace(corpus=corpus, run=run), database_path=tmp_path / "api.sqlite3")
    with TestClient(app, base_url="http://127.0.0.1", headers={"X-Pilot-Token": app.state.token}) as client:
        try:
            def post(index):
                return client.post("/api/runs", json=request(index).model_dump())
            assert post(0).status_code == 202
            assert entered.wait(3)
            assert post(1).status_code == post(2).status_code == 202
            duplicate = post(1)
            assert duplicate.status_code == 202 and duplicate.json()["created"] is False
            rejected = post(3)
            assert rejected.status_code == 429 and rejected.headers["retry-after"] == "5"
            assert len(app.state.store.list()) == 3
        finally:
            release.set()


@pytest.mark.parametrize("value", [0, -1, True, "2"])
def test_invalid_optional_store_limit_rejected(tmp_path, value):
    with pytest.raises(ValueError, match="positive integer"):
        Store(tmp_path / "not-created.sqlite3", queue_limit=value)
    assert not (tmp_path / "not-created.sqlite3").exists()
