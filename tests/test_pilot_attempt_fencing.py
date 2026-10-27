"""No-schema-change attempt fencing; no inference or human approval."""
import pytest

from src.pilot.schemas import ResearchRequest
from src.pilot.store import Conflict, Store


def job(tmp_path):
    store = Store(tmp_path / "attempts.sqlite3")
    rid, _ = store.create(ResearchRequest(query="Synthetic request?", request_key="synthetic-attempt"), "corpus")
    return store, rid


def empty():
    return {"title": "Synthetic empty draft", "claims": [], "warnings": []}


def test_canceled_then_retried_attempt_rejects_late_events_and_draft(tmp_path):
    store, rid = job(tmp_path)
    assert store.claim(rid, "first")
    assert store.attempt_event(rid, "first", "model_call", {"usage": {"input_tokens": 7}})
    assert store.cancel(rid) == "first"
    store.retry(rid)
    assert store.claim(rid, "second")
    assert not store.attempt_event(rid, "first", "late", {})
    assert not store.finish_attempt(rid, "first", "deadline")
    with pytest.raises(Conflict, match="no longer current"):
        store.save_draft(rid, empty(), {}, {}, attempt_id="first")
    store.save_draft(rid, empty(), {}, {}, attempt_id="second")
    assert store.get(rid)["status"] == "needs_review"
    assert store.get(rid)["revision"] == 1
    with pytest.raises(Conflict):
        store.cancel(rid)


def test_timeout_preserves_partial_usage_without_fabricating_zero_cost(tmp_path):
    store, rid = job(tmp_path)
    assert store.claim(rid, "current")
    store.attempt_event(rid, "current", "model_call", {"usage": {"input_tokens": 7, "output_tokens": 3}})
    assert store.finish_attempt(rid, "current", "deadline", 180)
    result = store.get(rid)
    assert result["status"] == "failed" and result["revision"] == 0
    assert result["metrics"]["known_input_tokens"] == 7 and result["metrics"]["known_output_tokens"] == 3
    assert result["metrics"]["inflight_usage_unknown"] and result["metrics"]["monetary_cost"] is None
    assert not store.finish_attempt(rid, "current", "worker_exit")


def test_queued_cancellation_and_recovery_do_not_create_drafts(tmp_path):
    store, rid = job(tmp_path)
    assert store.next_queued()["id"] == rid
    assert store.cancel(rid) is None and store.next_queued() is None
    assert not store.claim(rid, "late")
    store.retry(rid)
    store.recover()
    assert store.get(rid)["status"] == "interrupted"
    assert store.get(rid)["draft"] is None
