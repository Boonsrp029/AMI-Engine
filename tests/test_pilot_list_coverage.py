"""Synthetic literal-coverage checks are not a general completeness evaluation."""
import copy

import pytest
from pydantic import ValidationError

from src.pilot._choices import constrained_selection, geography_choices
from src.pilot._composition import project
from src.pilot._evidence import EvidenceMap, EvidenceSelection, GeographySelection, build_span_catalog, resolve_selection
from src.pilot._requests import requested_components
from src.pilot._retrieval_policy import contrast_evidence_choices


QUESTION = "Which export categories moved in opposite directions?"
TEXT = ("Exports declined from the previous month. These included 1) ceramics, mainly from lower orders, "
        "2) textiles, due to shipping delays and 3) glass products, due to reduced orders. "
        "However, exports of some products increased, such as pumps, fans, and lenses.")


def fixture():
    sources = {"synthetic": {"content": TEXT}}
    catalog = build_span_catalog(sources)
    views = contrast_evidence_choices(catalog, sources, requested_components(QUESTION))
    return sources, catalog, views


def test_contrast_views_keep_both_exact_passages_and_allow_unresolved_selection():
    sources, catalog, views = fixture()
    assert views == contrast_evidence_choices(catalog, sources, requested_components(QUESTION))
    assert [v["role"] for v in views["r1"]] == ["declining_categories", "increasing_categories"]
    selected = [v["span_ids"][0] for v in views["r1"]]
    assert [catalog[s]["text"] for s in selected] == [TEXT.split(". ")[1] + ".", TEXT.split(". ")[2]]
    schema = constrained_selection(EvidenceSelection, GeographySelection, geography_choices(catalog, QUESTION),
                                   requested_components(QUESTION), request_views=views)
    raw = {"components": [{"component_id": "r1", "status": "supported", "short_answer": "Directions differed.",
                            "evidence": selected}],
           "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "No place."}}
    assert schema.model_validate(raw)
    changed = copy.deepcopy(raw)
    changed["components"][0]["evidence"] = selected[:1]
    with pytest.raises(ValidationError):
        schema.model_validate(changed)
    changed["components"][0].update(status="missing", short_answer="", evidence=[])
    assert resolve_selection(schema.model_validate(changed).model_dump(), catalog, QUESTION, sources, "2026-10-27")


def test_contrast_does_not_join_sources_or_guess_ambiguous_records():
    sources, catalog, _ = fixture()
    sources["other"] = {"content": TEXT}
    assert not contrast_evidence_choices(build_span_catalog(sources), sources, requested_components(QUESTION))
    sources = {"down": {"content": TEXT.rsplit(". ", 1)[0] + "."},
               "up": {"content": TEXT.rsplit(". ", 1)[1]}}
    assert not contrast_evidence_choices(build_span_catalog(sources), sources, requested_components(QUESTION))
    assert not contrast_evidence_choices(catalog, {"synthetic": {"content": TEXT}}, requested_components("What happened to imports?"))
    sources = {"synthetic": {"content": TEXT.replace("Exports declined", "Imports declined")}}
    assert not contrast_evidence_choices(build_span_catalog(sources), sources, requested_components(QUESTION))


def mapping(quote):
    return EvidenceMap.model_validate({"components": [{"component_id": "r1", "question_anchor": QUESTION,
        "status": "supported", "short_answer": "An incomplete summary.",
        "evidence": [{"source_id": "synthetic", "quote": quote}]}]})


@pytest.mark.parametrize("quote,summary", [
    (TEXT.split(". ")[1] + ".", "Ceramics declined."),
    (TEXT.split(". ")[2], "Pumps and fans increased."),
])
def test_selected_list_omissions_retain_exact_excerpt(quote, summary):
    diagnostics = {}
    draft, fallbacks = project({"title": "Analyst research brief", "claims": [
        {"unit_id": "u1", "component_id": "r1", "text": summary}]}, mapping(quote), QUESTION, {}, diagnostics)
    assert fallbacks == ["u1"]
    assert draft["claims"][0]["text"] == quote
    assert diagnostics["fallback_reasons"] == {"u1": "requested_list_items_absent_from_synthesis"}
    assert draft["claims"][0]["source_ids"] == ["synthetic"]


def test_complete_selected_list_does_not_force_extract_or_expand_unselected_facts():
    quote = TEXT.split(". ")[2]
    summary = "Exports of pumps, fans and lenses increased."
    draft, fallbacks = project({"title": "Analyst research brief", "claims": [
        {"unit_id": "u1", "component_id": "r1", "text": summary}]}, mapping(quote), QUESTION, {})
    assert not fallbacks and draft["claims"][0]["text"] == summary
    assert "ceramics" not in str(draft)


def test_list_fallback_keeps_length_and_numeric_validation():
    quote = "Exports increased, such as pumps and lenses."
    with pytest.raises(ValueError, match="numeric"):
        project({"title": "Analyst research brief", "claims": [
            {"unit_id": "u1", "component_id": "r1", "text": "Pumps and lenses increased 98%."}]}, mapping(quote), QUESTION, {})
    value = mapping(quote)
    value.components[0].evidence[0].quote = "Exports increased, such as pumps, lenses and " + "detailed " * 100
    with pytest.raises(ValidationError, match="600 characters"):
        project({"title": "Analyst research brief", "claims": [
            {"unit_id": "u1", "component_id": "r1", "text": "Pumps increased."}]}, value, QUESTION, {})
