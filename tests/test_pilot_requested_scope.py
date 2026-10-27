"""Scope-choice regression contracts, not generated semantic-quality evidence."""
import pytest
from pydantic import ValidationError

from src.pilot._choices import constrained_selection, geography_choices, period_choices
from src.pilot._evidence import EvidenceMap, EvidenceSelection, GeographySelection, build_span_catalog
from src.pilot._scope import measurement_periods, resolve_scope


def test_requested_geography_cannot_promote_unrequested_industry_or_market():
    catalog = build_span_catalog({"s": {"content":
        "Investment in Battery Storage increased. Output in Cedar Bay rose; trade in Willow Cove fell."}})
    choices = geography_choices(catalog, "What was investment in Cedar Bay?",
                                explicit_only=True, requested_only=True)
    assert [x["value"] for x in choices["labels"]] == ["Cedar Bay"]
    assert choices["requested_labels_only"]
    # Provenance is necessary, not a geographic ontology or entailment guarantee.


def test_requested_label_matching_is_case_insensitive_and_uses_word_boundaries():
    catalog = build_span_catalog({"s": {"content": "Output in Cedar Bay rose."}})
    assert geography_choices(catalog, "CEDAR BAY's output?", explicit_only=True,
                             requested_only=True)["labels"]
    assert not geography_choices(catalog, "Cedar Bayou output?", explicit_only=True,
                                 requested_only=True)["labels"]


def test_configured_names_cannot_bypass_requested_label_filter():
    catalog = build_span_catalog({"s": {"content": "Cedar Bay and Willow Cove output rose."}})
    values = geography_choices(catalog, "Cedar Bay output?", allowed_names=["Cedar Bay", "Willow Cove"],
                               requested_only=True)["labels"]
    assert [x["value"] for x in values] == ["Cedar Bay"]


def test_decoder_rejects_unrequested_industry_but_retains_explicit_unresolved_state():
    catalog = build_span_catalog({"s": {"content": "Investment in Battery Storage rose 6%."}})
    choices = geography_choices(catalog, "What happened in Cedar Bay?", explicit_only=True, requested_only=True)
    schema = constrained_selection(EvidenceSelection, GeographySelection, choices)
    value = {"components": [{"component_id": "r1", "status": "supported", "short_answer": "6%",
              "evidence": [next(iter(catalog))]}], "geography": {
              "status": "known", "value": "Battery Storage", "evidence": [next(iter(catalog))], "reason": ""}}
    with pytest.raises(ValidationError):
        schema.model_validate(value)
    value["geography"] = {"status": "unresolved", "value": "", "evidence": [], "reason": "No requested location."}
    assert schema.model_validate(value).geography.status == "unresolved"


@pytest.mark.parametrize("prefix", ["No. 18/2028 (M.2) 14 February 2028", "18/2028 (M.2) 14 February 2028",
                                   "18/2028 14 February 2028", "No 18/2028\n14 February 2028"])
def test_release_number_dateline_is_not_measurement_period(prefix):
    text = prefix + " Fictional 2027 orders rose 6%. Output in December 2027 reached 8 units."
    assert measurement_periods(text) == ["December 2027"]
    assert [x["value"] for x in period_choices({"s": {"text": text}})] == ["December 2027"]


def test_plain_dated_measurement_without_release_number_is_retained():
    assert measurement_periods("14 February 2028 output reached 8 units.") == ["February 2028"]
    assert measurement_periods("Output was 8 units. Published in February 2028.") == []


@pytest.mark.parametrize("question,expected", [
    ("What happened in December 2027?", ["December 2027"]),
    ("Compare 2027 with 2026.", ["December 2027", "November 2026"]),
    ("What happened in 2025?", []),
    ("What periods are stated?", ["December 2027", "November 2026", "February 2028"]),
])
def test_decoder_periods_are_bounded_by_explicit_requested_periods_or_years(question, expected):
    catalog = {"s": {"text": "Output in December 2027, November 2026 and February 2028 was reported."}}
    assert [p["value"] for p in period_choices(catalog, question)] == expected


def test_dateline_cannot_be_propagated_as_a_component_observation_period():
    quote = "18/2028 (M.2) 14 February 2028 Fictional annual orders in 2027 rose 6%."
    question = "What happened to annual orders in 2027?"
    mapping = EvidenceMap.model_validate({"period": "February 2028", "components": [{
        "component_id": "r1", "question_anchor": question, "status": "supported", "short_answer": "6%",
        "evidence": [{"source_id": "s", "quote": quote}]}]})
    with pytest.raises(ValueError, match="selected supporting quotations"):
        resolve_scope(mapping, question)
