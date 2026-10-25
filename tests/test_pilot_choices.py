"""Source-bound decoder labels remain untyped; semantic support still needs review."""
import pytest
from pydantic import ValidationError

from src.pilot._choices import constrained_selection, geography_choices
from src.pilot._evidence import EvidenceSelection, GeographySelection, build_span_catalog, project_draft, resolve_selection
from src.pilot._scope import resolve_scope


def raw(catalog, geography):
    return {"components": [{"component_id": "r1", "status": "supported", "short_answer": "12 MWh",
        "evidence": [next(iter(catalog))]}], "geography": geography}


def test_question_only_country_cannot_be_emitted_when_not_in_source_choices():
    sources = {"a": {"content": "Measured output was 12 MWh in June 2018."}}
    catalog = build_span_catalog(sources)
    choices = geography_choices(catalog, "What was output in Mossland in June 2018?")
    assert "Mossland" not in [label["value"] for label in choices["labels"]]
    schema = constrained_selection(EvidenceSelection, GeographySelection, choices)
    assert "geography" in schema.model_json_schema()["required"]
    value = raw(catalog, {"status": "known", "value": "Mossland", "evidence": list(catalog), "reason": ""})
    with pytest.raises(ValidationError):
        schema.model_validate(value)
    value["geography"] = {"status": "unresolved", "value": "", "evidence": [], "reason": "No source location."}
    assert schema.model_validate(value).geography.status == "unresolved"
    del value["geography"]
    with pytest.raises(ValidationError):
        schema.model_validate(value)


def test_label_and_its_span_references_are_constrained_together():
    sources = {"a": {"content": "The district of Cedar Bay had output of 12 MWh."},
               "b": {"content": "The region of Pine Cove had output of 20 MWh."}}
    catalog = build_span_catalog(sources)
    choices = geography_choices(catalog, "What was Cedar Bay output?")
    assert any(c["value"] == "Cedar Bay" for c in choices["labels"])
    schema = constrained_selection(EvidenceSelection, GeographySelection, choices)
    a, b = list(catalog)
    value = raw(catalog, {"status": "known", "value": "Cedar Bay", "evidence": [a], "reason": ""})
    assert schema.model_validate(value).geography.value == "Cedar Bay"
    value["geography"]["evidence"] = [b]
    with pytest.raises(ValidationError):
        schema.model_validate(value)


def test_capitalized_company_is_only_an_untyped_label_not_an_inferred_location():
    catalog = build_span_catalog({"a": {"content": "Atlas reported output of 12 MWh."}})
    choices = geography_choices(catalog, "Where was output measured?")
    assert any(c["value"] == "Atlas" for c in choices["labels"])
    assert "untyped" in choices["classification"]
    schema = constrained_selection(EvidenceSelection, GeographySelection, choices)
    value = raw(catalog, {"status": "unresolved", "value": "", "evidence": [], "reason": "Atlas is not established as a place."})
    assert schema.model_validate(value).geography.status == "unresolved"


def test_label_budget_is_bounded_and_truncation_is_visible():
    # Distinct literal labels, without assigning any geographic classification.
    sources = {str(i): {"content": chr(65 + i // 26) + chr(65 + i % 26) + "vale has output."} for i in range(30)}
    choices = geography_choices(build_span_catalog(sources), "Where was output?", limit=5)
    assert len(choices["labels"]) == 5 and choices["truncated"]
    assert choices["total_labels"] == 30


def test_no_literal_labels_still_requires_explicit_unresolved_state():
    catalog = build_span_catalog({"a": {"content": "output was twelve units."}})
    choices = geography_choices(catalog, "Where was output measured?")
    assert choices["labels"] == []
    schema = constrained_selection(EvidenceSelection, GeographySelection, choices)
    value = raw(catalog, {"status": "unresolved", "value": "", "evidence": [], "reason": "No source location."})
    assert schema.model_validate(value).geography.status == "unresolved"
    value["geography"] = {"status": "known", "value": "Atlas", "evidence": list(catalog), "reason": ""}
    with pytest.raises(ValidationError):
        schema.model_validate(value)


def test_decoder_slots_reject_extra_missing_repeated_or_reordered_requests():
    from src.pilot._requests import requested_components
    catalog = build_span_catalog({"a": {"content": "output was twelve units."}})
    question = "What was output, and what was its share?"
    schema = constrained_selection(EvidenceSelection, GeographySelection,
        geography_choices(catalog, question), requested_components(question))
    value = raw(catalog, {"status": "unresolved", "value": "", "evidence": [], "reason": "No place."})
    second = {"component_id": "r2", "status": "missing", "short_answer": "", "evidence": []}
    value["components"].append(second)
    assert schema.model_validate(value).components[1].component_id == "r2"
    spec = schema.model_json_schema()["properties"]["components"]
    assert spec["minItems"] == spec["maxItems"] == 2
    import copy
    for mode in ("extra", "missing", "repeat", "reorder"):
        changed = copy.deepcopy(value)
        if mode == "extra": changed["components"].append(second)
        elif mode == "missing": changed["components"].pop()
        elif mode == "repeat": changed["components"][1]["component_id"] = "r1"
        else: changed["components"].reverse()
        with pytest.raises(ValidationError):
            schema.model_validate(changed)


def test_date_mentions_are_not_places_but_an_independent_same_word_place_is_available():
    catalog = build_span_catalog({"a": {"content": "The town of May is covered. Output was 12 MWh in May 2020."}})
    choices = geography_choices(catalog, "What was output in May 2020?")
    may = next(label for label in choices["labels"] if label["value"] == "May")
    assert may["span_ids"] == [next(iter(catalog))]
    assert any(row["value"] == "May" for row in choices["excluded_temporal_mentions"])
    anonymous = build_span_catalog({"a": {"content": "Measured output was 12 MWh in October 2015."}})
    choices = geography_choices(anonymous, "What was output in Westmere?")
    assert choices["labels"] == []
    assert choices["excluded_temporal_mentions"][0]["value"] == "October"


def test_same_source_context_is_retained_separately_and_flagged_before_approval():
    sources = {"a": {"content": "The district of Cedar Bay is covered. Output was 12 MWh in June 2018."}}
    catalog = build_span_catalog(sources)
    context_id, fact_id = list(catalog)
    value = {"components": [{"component_id": "r1", "status": "supported", "short_answer": "12 MWh", "evidence": [fact_id]}],
        "geography": {"status": "known", "value": "Cedar Bay", "evidence": [context_id], "reason": ""}}
    question = "What was output in June 2018?"
    mapping = resolve_selection(value, catalog, question, sources, "2026-10-25")
    mapping, scope = resolve_scope(mapping, question)
    assert mapping.geography_resolution.context_only
    assert mapping.geography_resolution.evidence[0].quote == catalog[context_id]["text"]
    draft, _ = project_draft({"title": "Output", "claims": []}, mapping, question, scope)
    assert draft["claims"] == [{"text": "Cedar Bay, June 2018: 12 MWh", "source_ids": ["a"]}]
    assert "Geographic scope uses source context" in draft["warnings"][0]


def test_geographic_context_does_not_establish_a_measurement_period():
    sources = {"a": {"content": "The district of Cedar Bay published this in 2026-10-01. Output was 12 MWh in June 2018."}}
    catalog = build_span_catalog(sources)
    context_id, fact_id = list(catalog)
    value = {"components": [{"component_id": "r1", "status": "supported", "short_answer": "12 MWh", "evidence": [fact_id]}],
        "geography": {"status": "known", "value": "Cedar Bay", "evidence": [context_id], "reason": ""}, "period": "2026-10-01"}
    with pytest.raises(ValueError, match="scope"):
        resolve_selection(value, catalog, "What was output?", sources, "2026-10-25")
