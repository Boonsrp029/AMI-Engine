"""Synthetic ranking/provenance contracts, separate from actual corpus coverage diagnostics."""
import json
from pathlib import Path

import pytest

from src.pilot._evidence import EvidenceMap, build_span_catalog, project_draft
from src.pilot._retrieval_policy import effective_query, load_profile, select_catalog
from src.pilot._scope import resolve_scope, validate_claim_measure_and_numbers


def profile():
    return {"version": "synthetic", "corpus_sha256": "fixed", "ranking_metadata_phrases": ["Northbank Research Outlook 2020"],
        "stop_terms": ["what", "the", "in", "change"], "maximum_evidence_characters": 200, "maximum_evidence_spans": 2}


def test_profile_is_hash_pinned_and_query_normalization_preserves_scenario_horizon_and_measure(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text(json.dumps(profile()), encoding="utf-8")
    assert load_profile(path, "changed") is None
    p = load_profile(path, "fixed")
    query, removed = effective_query("What change in electricity demand in the Northbank Research Outlook 2020 STEPS 2035?", p)
    assert query == "electricity demand steps 2035" and removed == ["Northbank Research Outlook 2020"]
    assert effective_query("Northbank Research Outlook 2020", p)[0] == ""


def test_span_budget_is_deterministic_preserves_source_offsets_and_reports_omissions():
    catalog = build_span_catalog({"a": {"content": "Electricity demand increased by 4%. Unrelated topic. Another unrelated topic."},
                                  "b": {"content": "Electricity demand rises through 2035."}})
    chosen, trace = select_catalog(catalog, "electricity demand 2035", profile())
    assert (chosen, trace) == select_catalog(catalog, "electricity demand 2035", profile())
    assert len(chosen) <= 2 and trace["selected_characters"] <= 200
    assert len(chosen) + len(trace["omitted_span_ids"]) == len(catalog)
    assert all(chosen[sid] is catalog[sid] for sid in chosen)


def test_unbounded_heading_cannot_supply_document_period_without_section_proof():
    sources = {"heading": {"doc_name": "monthly", "url": "https://example.invalid/report", "published": "2019-06-01",
        "content": "Press Release on Economic and Monetary Conditions for May 2019."},
        "fact": {"doc_name": "monthly", "url": "https://example.invalid/report", "published": "2019-06-01", "content": "Output increased."}}
    mapping = EvidenceMap.model_validate({"components": [{"component_id": "r1", "question_anchor": "What changed in May 2019?",
        "status": "supported", "short_answer": "Output increased.", "evidence": [{"source_id": "fact", "quote": "Output increased."}]}]})
    updated, context = resolve_scope(mapping, "What changed in May 2019?", sources)
    assert updated.period == "" and not context["reporting_period_context"]
    assert context['unresolved_requested_periods'] == ['May 2019']
    with pytest.raises(ValueError, match='period absent'):
        project_draft({"title": "Brief", "claims": [{"component_id": "r1", "text": "Output increased in May 2019."}]}, updated,
                      "What changed in May 2019?", context)
    sources["heading"]["content"] = "Published in May 2019."
    updated, context = resolve_scope(mapping, "What changed in May 2019?", sources)
    assert updated.period == "" and not context["reporting_period_context"]
    sources["heading"]["content"] = "Economic Conditions for May 2019."
    sources["heading"]["doc_name"] = "other"
    assert resolve_scope(mapping, "What changed in May 2019?", sources)[0].period == ""


def test_period_context_cannot_authorize_an_unrelated_numeric_quantity():
    component = EvidenceMap.model_validate({"components": [{"component_id": "r1", "question_anchor": "What?", "status": "supported",
        "short_answer": "Output increased.", "evidence": [{"source_id": "a", "quote": "Output increased."}]}]}).components[0]
    validate_claim_measure_and_numbers("Output increased in May 2019.", component, scope_period="May 2019")
    with pytest.raises(ValueError, match="numeric"):
        validate_claim_measure_and_numbers("Output was 2019 TWh.", component, scope_period="May 2019")
    with pytest.raises(ValueError, match="Total energy"):
        validate_claim_measure_and_numbers("Total final energy consumption grows.", component, "How will electricity demand change?")


def test_complementary_views_bind_literal_subject_and_document_without_forcing_an_answer():
    from pydantic import ValidationError
    from src.pilot._choices import constrained_selection, geography_choices
    from src.pilot._evidence import EvidenceSelection, GeographySelection, resolve_selection
    from src.pilot._retrieval_policy import request_evidence_choices
    sources = {"overview": {"content": "KEY HIGHLIGHT Farm output increased, supported by irrigation.", "doc_name": "doc",
                            "url": "https://example.invalid/doc", "published": "2019-06-01"},
               "detail": {"content": "Farm output increased following new equipment. Retail spending increased.", "doc_name": "doc",
                          "url": "https://example.invalid/doc", "published": "2019-06-01"}}
    catalog = build_span_catalog(sources)
    requests = [{"component_id": "r1", "question_anchor": "farm output", "instruction": "Both change and activities"}]
    p = {**profile(), "overview_markers": ["KEY HIGHLIGHT"]}
    views = request_evidence_choices(catalog, sources, requests, p)
    assert [v["role"] for v in views["r1"]] == ["overview", "detail"]
    assert all("Retail spending" not in catalog[sid]["text"] for v in views["r1"] for sid in v["span_ids"])
    schema = constrained_selection(EvidenceSelection, GeographySelection, geography_choices(catalog, "What changed?"), requests,
                                   periods=[], request_views=views)
    ids = [v["span_ids"][0] for v in views["r1"]]
    value = {"components": [{"component_id": "r1", "status": "supported", "short_answer": "Farm output increased.", "evidence": ids}],
        "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "No place."}}
    assert schema.model_validate(value)
    value["components"][0]["evidence"] = ids[::-1]
    with pytest.raises(ValidationError): schema.model_validate(value)
    value["components"][0].update(status="missing", short_answer="", evidence=[])
    missing = schema.model_validate(value)
    assert resolve_selection(missing.model_dump(), catalog, "What changed?", sources, "2026-10-25").components[0].status == "missing"
    sources["detail"]["doc_name"] = "other"
    assert not request_evidence_choices(catalog, sources, requests, p)


def test_forecast_change_views_retain_rate_and_level_for_the_requested_horizon_and_scenario():
    from src.pilot._retrieval_policy import request_evidence_choices
    from src.pilot._requests import requested_components
    from src.pilot._choices import constrained_selection, geography_choices
    from src.pilot._evidence import EvidenceSelection, GeographySelection
    from pydantic import ValidationError
    source = {"a": {"content": "Electricity demand is projected to rise 8% annually to 2042 in STEPS. From 600 TWh today, electricity demand rises to 900 TWh by 2042 in STEPS. Renewable capacity doubles by 2042."}}
    catalog = build_span_catalog(source)
    q = "In STEPS, how is electricity demand projected to change by 2042?"
    requests = requested_components(q)
    views = request_evidence_choices(catalog, source, requests, profile())
    assert [v["role"] for v in views["r1"]] == ["annual_change", "level_projection"]
    assert all("Renewable capacity" not in catalog[sid]["text"] for view in views["r1"] for sid in view["span_ids"])
    ids = [view["span_ids"][0] for view in views["r1"]]
    schema = constrained_selection(EvidenceSelection, GeographySelection, geography_choices(catalog, q), requests, request_views=views)
    raw = {"components": [{"component_id": "r1", "status": "supported", "short_answer": "Demand rises.", "evidence": ids}],
           "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "No place."}}
    assert schema.model_validate(raw)
    raw["components"][0]["evidence"] = ids + ids[:1]
    with pytest.raises(ValidationError): schema.model_validate(raw)
