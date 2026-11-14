"""Exercise request-bound geography against separate retrieved documents."""
import hashlib
import json
import time

import pytest
from pydantic import ValidationError

from src.pilot._choices import geography_choices
from src.pilot.subtasks._disclosures import DisclosureScopes, bindings_hash
from src.pilot.subtasks._scoped_generation import ScopedConcurrentComposer, WIRE_VERSION
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


@pytest.mark.parametrize(("question", "labels"), [
    ("What was output in Laos?", ["Laos"]),
    ("What was output in Laos in Tonne Equivalents?", ["Laos"]),
    ("What was output in Lao PDR?", []),
])
def test_scope_choices_require_requested_literal_geography(question, labels):
    catalog = {
        "output": {"text": "In Laos, output rose by 2 tonnes."},
        "method": {"text": "Output is measured in Tonne Equivalents."},
    }
    choices = geography_choices(catalog, question, explicit_only=True, requested_only=True,
                                exclude_measurement_context=True)
    assert [choice["value"] for choice in choices["labels"]] == labels


@pytest.mark.parametrize("selection", ["supported", "unit", "unrelated_document"])
def test_scoped_mapper_keeps_geography_bound_to_factual_sources(tmp_path, selection):
    question = "How much rice did mills process in Laos in 2017?"
    fact = "In Laos, mills processed 14 tonnes of rice in 2017."
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([
        {"feed_id": "fact", "title": "Mills report", "clean_content": fact},
        {"feed_id": "unit", "title": "Methods", "clean_content": "Rice processing is measured in Metric Tonnes."},
        {"feed_id": "other", "title": "Inspection note", "clean_content": "In Laos, rice quality inspections use random sampling."},
    ]), encoding="utf-8")
    plan = Plan(query=question, corpus_sha256=hashlib.sha256(corpus.read_bytes()).hexdigest(),
                subtasks=(Subtask(subtask_id="s01", operation="retrieve", query="rice"),))
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
            assert set(spans) == {"fact", "unit", "other"}
            geo_source = {"supported": "fact", "unit": "unit", "unrelated_document": "other"}[selection]
            parsed = {"wire_version": WIRE_VERSION, "components": [
                {"component_id": "r1", "status": "supported", "evidence": [spans["fact"]]}],
                "geography": {"status": "known", "value": "Metric Tonnes" if selection == "unit" else "Laos",
                              "evidence": [spans[geo_source]], "reason": ""}}
        else:
            parsed = {"title": "Analyst research brief", "claims": [
                {"component_id": "r1", "unit_id": "u1", "text": fact}]}
        return {"parsed": parsed}

    callback = ScopedConcurrentComposer(plan, bindings, "2026-11-12", fixed, scopes)
    access = ModelAccess(time.monotonic() + 30)
    if selection == "unit":
        with pytest.raises(ValidationError):
            callback(report, access)
    elif selection == "unrelated_document":
        with pytest.raises(ValueError, match="supported component's retrieved source"):
            callback(report, access)
    else:
        result = callback(report, access)
        assert result.draft["claims"] == [{"text": fact, "source_ids": ["fact"]}]
        assert result.draft["title"] == "Analyst research brief (Laos)"
    assert stages == (["mapping", "composition"] if selection == "supported" else ["mapping"])
