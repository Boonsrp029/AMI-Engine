"""Pinned document context and source-preserving fallback; no model quality claims."""
import copy

import pytest

from src.pilot._composition import project
from src.pilot._evidence import EvidenceMap, build_span_catalog, resolve_selection
from src.pilot._scope import resolve_scope


def geographic_case():
    shared = {"doc_name": "monthly", "url": "https://example.invalid/monthly", "published": "2020-05-01", "corpus_sha256": "a" * 64}
    sources = {"fact": {**shared, "content": "Output increased by 7%."},
               "context": {**shared, "content": "The region of Cedar Bay is covered by this report."}}
    catalog = build_span_catalog(sources)
    ids = {s["source_id"]: sid for sid, s in catalog.items()}
    value = {"components": [{"component_id": "r1", "status": "supported", "short_answer": "Output increased by 7%.", "evidence": [ids["fact"]]}],
        "geography": {"status": "known", "value": "Cedar Bay", "evidence": [ids["context"]], "reason": ""}}
    return sources, catalog, value


def test_geography_from_another_page_requires_pinned_membership_and_is_flagged_for_review():
    sources, catalog, value = geographic_case()
    mapping = resolve_selection(value, catalog, "What changed?", sources, "2026-10-26")
    assert mapping.geography_resolution.document_context_bindings[0]["factual_source_ids"] == ["fact"]
    mapping, scope = resolve_scope(mapping, "What changed?", sources)
    draft, _ = project({"title": "Analyst research brief", "claims": [{"unit_id": "u1", "component_id": "r1", "text": "Output increased by 7%."}]},
                       mapping, "What changed?", scope)
    assert draft["claims"][0]["source_ids"] == ["fact", "context"]
    assert any("another page of the same pinned document" in w for w in draft["warnings"])


@pytest.mark.parametrize("change", ["corpus", "missing_corpus", "url", "document", "date", "fabricated_quote"])
def test_unrelated_or_unpinned_geographic_context_still_fails(change):
    sources, catalog, value = geographic_case()
    if change == "corpus": sources["context"]["corpus_sha256"] = "b" * 64
    elif change == "missing_corpus": sources["context"].pop("corpus_sha256")
    elif change == "url": sources["context"]["url"] += "/other"
    elif change == "document": sources["context"]["doc_name"] = "other"
    elif change == "date": sources["context"]["published"] = "2021-05-01"
    else: sources["context"]["content"] = "Fabricated replacement."
    with pytest.raises(ValueError): resolve_selection(value, catalog, "What changed?", sources, "2026-10-26")


def test_lost_requested_cause_uses_exact_evidence_with_an_explicit_reason():
    quote = "Exports remained high, supported by global technology and artificial intelligence demand."
    mapping = EvidenceMap.model_validate({"components": [{"component_id": "r1", "question_anchor": "What supported exports?",
        "status": "supported", "short_answer": quote, "evidence": [{"source_id": "a", "quote": quote}]}]})
    raw = {"title": "Analyst research brief", "claims": [{"unit_id": "u1", "component_id": "r1", "text": "Exports remained high."}]}
    before = copy.deepcopy(raw)
    trace = {}
    draft, fallback = project(raw, mapping, "What supported exports?", {}, trace)
    assert draft["claims"][0]["text"] == quote and fallback == ["u1"]
    assert trace["fallback_reasons"] == {"u1": "requested_cause_absent_from_synthesis"}
    assert raw == before and any("verbatim source excerpts" in w for w in draft["warnings"])
    # Partial lexical cause overlap now conservatively retains the excerpt.
    raw["claims"][0]["text"] = "Global technology demand kept exports high."
    assert project(raw, mapping, "What supported exports?", {})[1] == ["u1"]
    # A paraphrase retaining all explicit causal terms still needs no fallback.
    raw["claims"][0]["text"] = "Global technology and artificial intelligence demand kept exports high."
    assert not project(raw, mapping, "What supported exports?", {})[1]
    assert not project(before, mapping, "What level did exports maintain?", {})[1]


def test_parallel_energy_cause_is_not_lost_when_food_cause_is_retained():
    quote = "Inflation increased, driven by fresh food costs and adverse weather, as well as energy prices following global crude oil increases."
    mapping = EvidenceMap.model_validate({"components": [{"component_id": "r1", "question_anchor": "What drove inflation?",
        "status": "supported", "short_answer": quote, "evidence": [{"source_id": "a", "quote": quote}]}]})
    raw = {"title": "Analyst research brief", "claims": [{"unit_id": "u1", "component_id": "r1", "text": "Inflation increased with fresh food costs and adverse weather."}]}
    draft, fallback = project(raw, mapping, "What drove inflation?", {})
    assert fallback == ["u1"] and draft["claims"][0]["text"] == quote


def test_core_cost_pass_through_cannot_be_reduced_to_a_direction_only():
    quote = "Core inflation increased, as businesses gradually pass-through higher costs to consumer prices."
    mapping = EvidenceMap.model_validate({"components": [{"component_id": "r1", "question_anchor": "What drove core inflation?",
        "status": "supported", "short_answer": quote, "evidence": [{"source_id": "a", "quote": quote}]}]})
    raw = {"title": "Analyst research brief", "claims": [{"unit_id": "u1", "component_id": "r1", "text": "Core inflation increased."}]}
    draft, fallback = project(raw, mapping, "What drove core inflation?", {})
    assert fallback == ["u1"] and draft["claims"][0]["text"] == quote


def test_scenario_and_report_relative_baseline_are_preserved_without_assigning_a_year():
    mapping = EvidenceMap.model_validate({"components": [{"component_id": "r1", "question_anchor": "What change in STEPS?",
        "status": "supported", "short_answer": "Demand rises.", "evidence": [
        {"source_id": "a", "quote": "Electricity demand rises 8% annually by 2042 in STEPS."},
        {"source_id": "a", "quote": "From 600 TWh today, electricity demand rises to 900 TWh by 2042 in STEPS."}]}]})
    mapping, context = resolve_scope(mapping, "What change in STEPS?")
    raw = {"title": "Analyst research brief", "claims": [
        {"unit_id": "u1", "component_id": "r1", "text": "Electricity demand rises 8% annually by 2042."},
        {"unit_id": "u2", "component_id": "r1", "text": "From 600 TWh today, electricity demand rises to 900 TWh by 2042."}]}
    trace = {}
    draft, _ = project(raw, mapping, "What change in STEPS?", context, trace)
    assert all("STEPS" in c["text"] for c in draft["claims"]) and "STEPS" in draft["title"]
    assert "source report's baseline" in draft["claims"][1]["text"] and "today" not in draft["claims"][1]["text"]
    assert trace["source_baseline_normalizations"] and "2026" not in str(draft)
    mapping.components[0].evidence[0].quote += " APS is also discussed."
    _, ambiguous = resolve_scope(mapping, "What change in STEPS?")
    assert "scenario" not in ambiguous["components"].get("r1", {})
    assert ambiguous["unresolved_requested_scenarios"] == ["STEPS"]
