"""Synthetic source review gates; no real authorization or model calls."""
from test_subtask_quality_review import fixture
from _qualification_fixtures import linked_ledger
from src.pilot.subtasks.qualification import digest
import pytest


def ledger(tmp_path):
    return linked_ledger(tmp_path)


def test_missing_or_changed_development_gate_blocks_start(tmp_path):
    l = ledger(tmp_path)
    rp = l.contract["development_gate"]["cases"][0]["result_path"]
    from pathlib import Path
    Path(rp).write_text("changed")
    with pytest.raises(ValueError):l.start(l.contract["case_ids"][0])


def test_nine_of_ten_allowance_controls_actual_admission(tmp_path):
    l = ledger(tmp_path)
    _, _, reviews = fixture()
    for i,cid in enumerate(l.contract["case_ids"][:2]):
        l.start(cid)
        l.finish(cid, {"technical_pass":True,"main_calls":2,"nemo_invocations":1,"elapsed_seconds":1})
        review = reviews[cid]
        review.update(result_sha256=digest(l.output/(cid+".result.json")),final_complete=False)
        l.assess(cid,review)
        if i==0:assert not (l.output/"stopped.json").exists()
    assert (l.output/"stopped.json").exists()
    with pytest.raises(ValueError):l.start(l.contract["case_ids"][2])
