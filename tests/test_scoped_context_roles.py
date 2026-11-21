"""Prove decoder schema rejects self-context without changing the evidence wire."""
import json
from types import SimpleNamespace as Record

import pytest

from src.pilot._evidence import build_span_catalog
from src.pilot.subtasks._fact_selection import fact_schema, resolve_facts


def fixture_sources(single=False):
    sources = {"canal": {"content": "The canal covers 32 hectares. Its survey was completed in 2019. Maintenance is annual."},
               "reservoir": {"content": "The reservoir covers 48 hectares."}}
    if single:
        sources = {"canal": {"content": "The canal covers 32 hectares."}}
    catalog = build_span_catalog(sources)
    report = Record(results=[Record(subtask_id="s01", outcome="evidence",
        sources=[Record(source_id=sid, role="support") for sid in sources])])
    slot = {"fact_id": "r1.1", "component_id": "r1", "question_anchor": "What area does the canal cover?"}
    return sources, catalog, report, slot


def selection(direct, contexts):
    return {"wire_version": "cq-fact-span-selection-v1", "facts": [{"fact_id": "r1.1", "state": "supported",
        "alternatives": [[{"span_id": direct, "context": contexts}]]}],
        "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "No place requested."}}


@pytest.mark.parametrize("single", [False, True])
def test_generic_schema_rejects_self_context_for_every_direct_span(single):
    _, catalog, report, slot = fixture_sources(single)
    schema = fact_schema([slot], catalog=catalog, bindings={"r1": ["s01"]}, report=report)
    for sid in catalog:
        with pytest.raises(ValueError):
            schema.model_validate_json(json.dumps(selection(sid, [sid])))
        assert schema.model_validate_json(json.dumps(selection(sid, [])))
    definitions = schema.model_json_schema()["$defs"]
    branches = [item["properties"] for item in definitions.values() if "span_id" in item.get("properties", {})]
    assert branches
    for fields in branches:
        direct = fields["span_id"]["const"]
        context = fields["context"]
        allowed = context.get("items", {}).get("enum", [context.get("items", {}).get("const")])
        assert direct not in allowed
        assert context["maxItems"] <= 2


def test_schema_retains_valid_same_record_context_order_and_exact_quotes():
    sources, catalog, report, slot = fixture_sources()
    same = [sid for sid, span in catalog.items() if span["source_id"] == "canal"]
    direct, first, second = same
    schema = fact_schema([slot], catalog=catalog, bindings={"r1": ["s01"]}, report=report)
    value = schema.model_validate_json(json.dumps(selection(direct, [second, first]))).model_dump()
    assert value["facts"][0]["alternatives"][0][0] == {"span_id": direct, "context": [second, first]}
    _, resolved = resolve_facts(value, [slot], {"r1": ["s01"]}, catalog, sources, report, {})
    assert [item["span_id"] for item in resolved[0]["alternatives"][0][0]["context"]] == [second, first]


def test_wrong_record_context_and_unknown_direct_are_rejected():
    _, catalog, report, slot = fixture_sources()
    direct = next(sid for sid, span in catalog.items() if span["source_id"] == "canal")
    foreign = next(sid for sid, span in catalog.items() if span["source_id"] == "reservoir")
    schema = fact_schema([slot], catalog=catalog, bindings={"r1": ["s01"]}, report=report)
    for value in (selection(direct, [foreign]), selection("unknown", [])):
        with pytest.raises(ValueError):
            schema.model_validate_json(json.dumps(value))


def test_duplicate_context_remains_a_semantic_rejection():
    sources, catalog, report, slot = fixture_sources()
    direct, context, _ = [sid for sid, span in catalog.items() if span["source_id"] == "canal"]
    schema = fact_schema([slot], catalog=catalog, bindings={"r1": ["s01"]}, report=report)
    value = schema.model_validate_json(json.dumps(selection(direct, [context, context]))).model_dump()
    with pytest.raises(ValueError, match="Duplicate fact evidence role"):
        resolve_facts(value, [slot], {"r1": ["s01"]}, catalog, sources, report, {})
