"""Offline parity of sequential/concurrent worker initialization; no NeMo calls."""
import asyncio
import sys
import pytest
from test_subtask_typed_runner import setup, operation, Composer
from src.pilot.subtasks.runner import run_stored_plan


def require_selector_policy(draft, sources):
    assert isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy)
    return True


@pytest.mark.skipif(sys.platform != "win32", reason="Windows worker policy contract")
def test_spawned_concurrent_child_uses_existing_selector_policy(tmp_path):
    store, rid, plan, corpus = setup(tmp_path)
    run_stored_plan(store, rid, plan, corpus, operation, Composer(plan), require_selector_policy)
    assert store.get(rid)["status"] == "needs_review"


def allow(draft, sources):
    return True


def fail_with_private_message(draft, sources):
    raise ValueError("SYNTHETIC_EXCEPTION_MESSAGE_DO_NOT_PERSIST")


@pytest.mark.parametrize("failed", [False, True])
def test_parent_records_bounded_worker_outcomes_without_error_text(tmp_path, failed):
    store, rid, plan, corpus = setup(tmp_path)
    if failed:
        with pytest.raises(ValueError):
            run_stored_plan(store, rid, plan, corpus, operation, Composer(plan), fail_with_private_message)
    else:
        run_stored_plan(store, rid, plan, corpus, operation, Composer(plan), allow)
    row = store.get(rid)
    if failed:
        event = next(e for e in row["events"] if e["kind"] == "subtask_worker_failure")
        assert event["payload"]["stage"] == "safety"
        assert event["payload"]["error_type"] == "ValueError"
        assert row["revision"] == 0
    else:
        event = next(e for e in row["events"] if e["kind"] == "subtask_worker_terminal")
        assert event["payload"]["exit_code"] == 0 and event["payload"]["candidate_received"] is True
    assert "SYNTHETIC_EXCEPTION_MESSAGE_DO_NOT_PERSIST" not in str(row["events"])
