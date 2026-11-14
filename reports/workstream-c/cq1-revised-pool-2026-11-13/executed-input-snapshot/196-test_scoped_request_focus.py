"""Exercise focused requests through the scoped mapper and composer."""
import hashlib
import json
import time

import pytest

from src.pilot.subtasks._disclosures import DisclosureScopes, bindings_hash
from src.pilot.subtasks._request_focus import validate_focused_claims
from src.pilot.subtasks._scoped_generation import ScopedConcurrentComposer, WIRE_VERSION, table_composition_schema
from src.pilot._evidence import EvidenceMap
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


TABLE = ("utility-scale electricity generation in 2018\nEnergy source\nBillion kWh\nShare of total\n"
         "Total - all sources\n510\nWind\n62\n12.2%\nHydropower\n2\n119\n23.3%\nBiomass\n35\n6.9%")
RATIO = "The delivery rate divides completed deliveries by all scheduled deliveries for the same week."


@pytest.mark.parametrize(("kind", "invalid"), [
    ("table", ""), ("table", "span"), ("table", "claim"), ("table", "omit"),
    ("table", "duplicate"), ("table", "forged"), ("table", "wrong_component"),
    ("ratio", ""), ("ratio", "claim"),
])
def test_scoped_request_focus_binds_exact_row_and_operand(tmp_path, kind, invalid):
    question, fact, expected = {
        "table": ("What were hydropower generation and its share of utility-scale generation in 2018?",
                  TABLE, "In 2018, the table gives Hydropower generation in Billion kWh as 119 and its share of total utility-scale electricity generation as 23.3%."),
        "ratio": ("What forms the denominator of the delivery rate?",
                  RATIO, "The denominator is all scheduled deliveries for the same week."),
    }[kind]
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([{"feed_id": "target", "clean_content": fact},
                                  {"feed_id": "distractor", "clean_content": question}]), encoding="utf-8")
    plan = Plan(query=question, corpus_sha256=hashlib.sha256(corpus.read_bytes()).hexdigest(),
                subtasks=(Subtask(subtask_id="s01", operation="retrieve", query=question),))
    bindings = {"r1": ["s01"]}
    scopes = DisclosureScopes.model_validate_json(json.dumps({
        "plan_id": plan.plan_id, "corpus_sha256": plan.corpus_sha256,
        "question_sha256": hashlib.sha256(question.encode()).hexdigest(),
        "bindings_sha256": bindings_hash(bindings), "declaration_ref": "Synthetic regression",
        "annotations": [{"component_id": "r1", "subtask_id": "s01",
                         "question_span": {"start": 0, "end": len(question)}}],
    }))
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(corpus))
    calls = []

    def fixed(stage, schema, instruction, inputs):
        calls.append(stage)
        if stage == "mapping":
            spans = {r["source_id"]: r["spans"][0]["span_id"] for r in inputs["evidence"]}
            assert inputs["request_focus"]["r1"]["span_id"] == spans["target"]
            parsed = {"wire_version": WIRE_VERSION, "components": [{"component_id": "r1",
                "status": "supported", "evidence": [spans["distractor" if invalid == "span" else "target"]]}],
                "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "No place."}}
        elif kind == "table":
            assert inputs["units"][0]["response_kind"] == "table_row"
            assert "request_focus" not in inputs
            selection = {"component_id": "r1", "unit_id": "u1"}
            claims = [selection]
            if invalid == "claim":
                claims = [{**selection, "text": expected}]
            elif invalid == "omit":
                claims = []
            elif invalid == "duplicate":
                claims = [selection, selection]
            elif invalid == "forged":
                claims = [{**selection, "unit_id": "u9"}]
            elif invalid == "wrong_component":
                claims = [{**selection, "component_id": "r2"}]
            parsed = {"title": "Analyst research brief", "claims": claims}
        else:
            assert inputs["request_focus"]["r1"]["claim_text"] == expected
            text = expected
            if invalid == "claim":
                text = text.replace("119", "62") if kind == "table" else "The numerator is completed deliveries."
            parsed = {"title": "Analyst research brief", "claims": [
                {"component_id": "r1", "unit_id": "u1", "text": text}]}
        return {"parsed": parsed}

    callback = ScopedConcurrentComposer(plan, bindings, "2026-11-12", fixed, scopes,
                                        complete_required_branches=bindings)
    access = ModelAccess(time.monotonic() + 30)
    if invalid:
        with pytest.raises(ValueError):
            callback(report, access)
    else:
        result = callback(report, access)
        assert result.draft["claims"] == [{"text": expected, "source_ids": ["target"]}]
        assert result.diagnostics["fallback_unit_ids"] == []
        if kind == "table":
            assert result.diagnostics["raw_composer_output"]["claims"] == ({"component_id": "r1", "unit_id": "u1"},)
            rendered, = result.diagnostics["application_rendered_table_rows"]
            assert rendered["text"] == expected and rendered["source_id"] == "target"
            assert fact[rendered["start"]:rendered["end"]] == fact
    assert calls == (["mapping"] if invalid == "span" else ["mapping", "composition"])


@pytest.mark.parametrize(("text", "accepted"), [
    ("The denominator is all scheduled deliveries for the same week.", True),
    ("The denominator of the delivery rate is all scheduled deliveries for the same week.", True),
    ("The denominator of the completion rate is all scheduled deliveries for the same week.", False),
    ("The numerator of the delivery rate is all scheduled deliveries for the same week.", False),
    ("The denominator of the delivery rate is completed deliveries.", False),
    ("The denominator of the delivery rate is not all scheduled deliveries for the same week.", False),
    ("The denominator is all scheduled deliveries for the same week. Rates increased.", False),
])
def test_named_ratio_claim_preserves_requested_operand(text, accepted):
    focus = {"kind": "ratio_operand", "ratio": "The delivery rate", "role": "denominator",
             "operand": "all scheduled deliveries for the same week"}
    claims = [{"component_id": "r1", "text": text}]
    if accepted:
        validate_focused_claims(claims, {"r1": focus})
    else:
        with pytest.raises(ValueError, match="requested table row or ratio operand"):
            validate_focused_claims(claims, {"r1": focus})


def test_mixed_composition_requires_table_selection_and_preserves_prose_slot():
    mapping = EvidenceMap(components=[
        {"component_id": "r1", "question_anchor": "Hydropower generation", "status": "supported",
         "short_answer": "Table row", "evidence": [{"source_id": "target", "quote": TABLE}]},
        {"component_id": "r2", "question_anchor": "Delivery rate", "status": "supported",
         "short_answer": "Delivery rate", "evidence": [{"source_id": "ratio", "quote": RATIO}]},
    ])
    schema = table_composition_schema(mapping, {"u1": "r1"})
    table = {"unit_id": "u1", "component_id": "r1"}
    prose = {"unit_id": "u2", "component_id": "r2", "text": RATIO}
    for claims in ([table], [table, prose]):
        parsed = schema.model_validate({"title": "Analyst research brief", "claims": claims})
        assert parsed.model_dump(mode="json")["claims"] == claims
    for claims in ([prose], [prose, table], [table, {**prose, "text": None}]):
        with pytest.raises(ValueError):
            schema.model_validate({"title": "Analyst research brief", "claims": claims})
