"""Pinned, fixed-response pre-safety capture; these checks never infer quality."""
import json

import pytest
from test_subtask_generation import fixture

from scripts._concurrent_composer_capture import capture_composer, sha
from src.pilot._evidence import build_span_catalog


def frozen(tmp_path):
    plan, report = fixture(tmp_path)
    sources = {r.source.source_id:r.source.model_dump() for r in report.sources}
    spans = list(build_span_catalog(sources))
    mapping = {"wire_version":"source-selection-v1", "components":[{
        "component_id":"r1", "status":"supported", "evidence":spans, "gap_anchor":""}],
        "geography":{"status":"unresolved", "value":"", "evidence":[], "reason":"Not established."}}
    mapping_path = tmp_path / "mapper.json"
    mapping_path.write_text(json.dumps({"stage":"mapping", "raw":json.dumps(mapping)}), encoding="utf-8")
    contract_path = tmp_path / "contract.json"
    corpus = tmp_path / "corpus.json"
    contract_path.write_text(json.dumps({"as_of":"2026-11-06", "cases":{"p01":{
        "plan":plan.model_dump(mode="json"), "bindings":{"r1":["s01"]},
        "corpus_path":str(corpus)}}}), encoding="utf-8")
    expected = {"contract":sha(contract_path), "mapping":sha(mapping_path), "corpus":sha(corpus)}
    return contract_path, mapping_path, expected


def response(text="Observed electricity demand increased 7.3% in 2014."):
    return {"title":"Analyst research brief", "claims":[{
        "component_id":"r1", "unit_id":"u1", "text":text}]}


def test_capture_creates_no_model_and_no_safety_or_draft(tmp_path, monkeypatch):
    from src.pilot.subtasks.generation import OllamaStructuredTransport
    def forbidden(*args, **kwargs):
        raise AssertionError("Offline replay must not start inference")
    monkeypatch.setattr(OllamaStructuredTransport, "__call__", forbidden)
    contract, mapping, expected = frozen(tmp_path)
    result = capture_composer(contract,"p01",mapping,expected=expected)
    assert result["status"] == "captured without inference"
    assert result["actual_model_calls"] == result["nemo_invocations"] == 0
    assert result["frozen_mapper_replays"] == 1 and result["fixed_composer_validations"] == 0
    assert [m["type"] for m in result["captured"]["messages"]] == ["system","human"]
    assert "draft" not in result


def test_fixed_paraphrase_validates_without_claiming_safety(tmp_path):
    contract, mapping, expected = frozen(tmp_path)
    result = capture_composer(contract,"p01",mapping,expected=expected,response=response())
    assert result["status"].startswith("composition validated")
    assert result["safety_passed"] is False
    assert result["draft"]["claims"][0]["text"] == response()["claims"][0]["text"]
    assert result["diagnostics"]["fallback_unit_ids"] == []
    assert result["actual_model_calls"] == 0 and result["logical_access_slots"] == 2


@pytest.mark.parametrize("damage", ["number", "unit"])
def test_invalid_fixed_composer_is_explicit_failure(tmp_path, damage):
    contract, mapping, expected = frozen(tmp_path)
    invalid = response("Observed electricity demand grew 54.2% in 2014.") if damage == "number" else response()
    if damage == "unit":
        invalid["claims"][0]["unit_id"] = "invented"
    result = capture_composer(contract,"p01",mapping,expected=expected,response=invalid)
    assert result["status"] == "composition validation failed" and result["error"]
    assert "draft" not in result and result["nemo_invocations"] == 0


@pytest.mark.parametrize("target", ["contract", "mapping", "corpus"])
def test_identity_drift_refuses_capture_before_replay(tmp_path, target):
    contract, mapping, expected = frozen(tmp_path)
    path = {"contract":contract,"mapping":mapping,"corpus":tmp_path/"corpus.json"}[target]
    path.write_bytes(path.read_bytes()+b" ")
    with pytest.raises(ValueError, match="changed"):
        capture_composer(contract,"p01",mapping,expected=expected)
