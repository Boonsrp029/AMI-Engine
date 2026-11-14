"""Test evidence needed for an explicit provisional-or-final conflict."""
import hashlib
import json
import time
from types import SimpleNamespace

import pytest

from src.pilot._evidence import EvidenceComponent
from src.pilot.subtasks._disclosures import DisclosureScopes, bindings_hash
from src.pilot.subtasks._scoped_generation import ScopedConcurrentComposer, WIRE_VERSION
from src.pilot.subtasks._status_conflict import validate_publication_status_conflict
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


SUBJECT = "The 2017 Laos rice processing figures"
PROVISIONAL = f"{SUBJECT} are provisional."


@pytest.mark.parametrize(("second", "passes"), [
    ("In Laos, mills processed 14 tonnes of rice in 2017.", False),
    ("The 2016 Laos rice processing figures are final.", False),
    ("The 2017 Laos rice export figures are final.", False),
    (f"{SUBJECT} are not final.", False),
    (f"{SUBJECT} are preliminary.", False),
    (f"If {SUBJECT.lower()} are final", False),
    (f'"{SUBJECT} are final."', False),
    (f"{SUBJECT} are final.", True),
    (f"{SUBJECT} are not provisional.", True),
])
def test_publication_status_conflict_needs_opposed_same_subject_statements(second, passes):
    component = EvidenceComponent(
        component_id="r2", status="conflicting", short_answer="",
        question_anchor="were the figures provisional or final?",
        evidence=[{"source_id": "notice", "quote": PROVISIONAL},
                  {"source_id": "other", "quote": second}],
    )
    mapping = SimpleNamespace(components=[component])
    if passes:
        validate_publication_status_conflict(mapping)
    else:
        with pytest.raises(ValueError, match="opposed assertions"):
            validate_publication_status_conflict(mapping)


@pytest.mark.parametrize(("other", "conflict"), [
    ("In Laos, the 2017 rice processing counts are final.", True),
    ("In Laos, the 2016 rice processing counts are final.", False),
    ("In Cambodia, the 2017 rice processing counts are final.", False),
    ("In Laos, the 2017 rice export counts are final.", False),
    ("In Laos, the 2017 rice processing counts are not final.", False),
    ("Whether the 2017 rice processing counts are final is unknown.", False),
])
def test_scoped_composer_checks_unselected_bound_status_evidence(tmp_path, other, conflict):
    question = "Were the 2017 rice processing counts in Laos provisional or final?"
    fact = "In Laos, the 2017 rice processing counts are provisional."
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([
        {"feed_id": "notice", "clean_content": fact},
        {"feed_id": "other", "clean_content": other},
    ]), encoding="utf-8")
    plan = Plan(query=question, corpus_sha256=hashlib.sha256(corpus.read_bytes()).hexdigest(),
                subtasks=(Subtask(subtask_id="s01", operation="retrieve", query="rice counts"),))
    bindings = {"r1": ["s01"]}
    scopes = DisclosureScopes.model_validate_json(json.dumps({
        "plan_id": plan.plan_id, "corpus_sha256": plan.corpus_sha256,
        "question_sha256": hashlib.sha256(question.encode()).hexdigest(),
        "bindings_sha256": bindings_hash(bindings), "declaration_ref": "Synthetic regression",
        "annotations": [{"component_id": "r1", "subtask_id": "s01",
                         "question_span": {"start": 0, "end": len(question)}}],
    }))
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(corpus))
    stages = []

    def fixed(stage, schema, instruction, inputs):
        stages.append(stage)
        if stage == "mapping":
            spans = {record["source_id"]: record["spans"][0]["span_id"] for record in inputs["evidence"]}
            assert set(spans) == {"notice", "other"}
            parsed = {"wire_version": WIRE_VERSION, "components": [
                {"component_id": "r1", "status": "supported", "evidence": [spans["notice"]]}],
                "geography": {"status": "known", "value": "Laos", "evidence": [spans["notice"]], "reason": ""}}
        else:
            parsed = {"title": "Analyst research brief", "claims": [
                {"component_id": "r1", "unit_id": "u1", "text": fact}]}
        return {"parsed": parsed}

    callback = ScopedConcurrentComposer(plan, bindings, "2026-11-12", fixed, scopes)
    result = callback(report, ModelAccess(time.monotonic() + 30))
    assert result.diagnostics["scoped_mapper_raw_selection"]["components"][0]["status"] == "supported"
    if conflict:
        assert stages == ["mapping"] and result.draft["claims"] == []
        assert result.draft["title"] == "Conflicting evidence"
        assert result.diagnostics["application_source_selection"]["components"][0]["status"] == "conflicting"
        assert len(result.diagnostics["application_detected_status_conflicts"]) == 1
        evidence, = result.diagnostics["scoped_disclosures"]["selected_conflicts"]
        assert evidence["selected_statements"] == [
            {"source_id": "notice", "quote": fact}, {"source_id": "other", "quote": other}]
    else:
        assert stages == ["mapping", "composition"]
        assert result.draft["claims"] == [{"text": fact, "source_ids": ["notice"]}]
        assert result.diagnostics["application_detected_status_conflicts"] == []
