"""Bounded source reading and prompt separation; no model-quality claims."""
import json

import pytest

from src.pilot._choices import constrained_selection, geography_choices
from src.pilot._evidence import EvidenceSelection, GeographySelection, build_span_catalog
from src.pilot.engine import Corpus


@pytest.mark.parametrize("text,allowed,rejected", [
    ("Bank of Thailand. Private Consumption Private Investment. The Thai economy improved in August.", [],
     ["Bank of Thailand", "Private Consumption", "The Thai", "August"]),
    ("Output in Cedar Bay was 16 MWh. The district of Pine Cove reports 4 GWh.",
     ["Cedar Bay", "Pine Cove"], []),
    ("Output was 16 MWh in October 2015. The town of May is covered.", ["May"], ["October"]),
    ("Atlas announced a capacity plan.", [], ["Atlas"]),
])
def test_runtime_geography_choices_require_literal_location_cues(text, allowed, rejected):
    catalog = build_span_catalog({"a": {"content": text}})
    choices = geography_choices(catalog, "What happened?", explicit_only=True)
    names = [row["value"] for row in choices["labels"]]
    assert all(name in names for name in allowed)
    assert not any(name in names for name in rejected)
    assert choices["explicit_location_cues_only"]
    # Even an empty candidate list requires the model to state unresolved explicitly.
    schema = constrained_selection(EvidenceSelection, GeographySelection, choices)
    assert "geography" in schema.model_json_schema()["required"]


def test_adjacent_inspection_preserves_records_and_never_crosses_page_document_or_url(tmp_path):
    rows = [{"feed_id": f"doc:0:{i}", "doc_name": "doc", "page_num": 0,
             "source": "https://example.invalid/doc", "clean_content": text}
            for i, text in enumerate(["First exact fragment.", "Next fragment - punctuation preserved.", "Third fragment."])]
    rows += [{"feed_id": "doc:0:3", "doc_name": "other", "page_num": 0, "clean_content": "Wrong document."},
             {"feed_id": "doc:1:0", "doc_name": "doc", "page_num": 1, "clean_content": "Different page."},
             {"feed_id": "other", "clean_content": "No ordinal."}]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    corpus = Corpus(path)
    before = json.dumps(corpus.sources, sort_keys=True)
    records = corpus.inspect("doc:0:1")
    assert [r["source_id"] for r in records] == ["doc:0:1", "doc:0:0", "doc:0:2"]
    assert [r["source_id"] for r in corpus.inspect("doc:0:2")] == ["doc:0:2", "doc:0:1"]
    assert corpus.inspect("other") == [corpus.sources["other"]]
    assert json.dumps(corpus.sources, sort_keys=True) == before
    for record in records:
        assert record is corpus.sources[record["source_id"]]
    corpus.sources["doc:0:0"]["url"] = "https://example.invalid/other"
    assert "doc:0:0" not in [r["source_id"] for r in corpus.inspect("doc:0:1")]
    with pytest.raises(KeyError):
        corpus.inspect("../../unknown")


def test_composition_schema_rejects_repeated_ids_and_title_scope_but_preserves_fallback():
    from src.pilot._choices import constrained_composition
    from src.pilot._evidence import EvidenceMap
    from pydantic import ValidationError
    mapping = EvidenceMap.model_validate({"components": [{"component_id": cid, "question_anchor": "What?",
        "status": "supported", "short_answer": "A supported answer.", "evidence": [{"source_id": cid, "quote": "A supported answer."}]} for cid in ["r1", "r2"]]})
    schema = constrained_composition(mapping)
    first = {"component_id": "r1", "unit_id": "u1", "text": "One."}
    second = {"component_id": "r2", "unit_id": "u2", "text": "Two."}
    for claims in [[], [first], [second], [first, second]]:
        assert schema.model_validate({"title": "Analyst research brief", "claims": claims})
    for claims in [[first, {**first, "text": "Another."}],
                   [{"component_id": "r3", "unit_id": "u1", "text": "Unrequested."}]]:
        with pytest.raises(ValidationError):
            schema.model_validate({"title": "Analyst research brief", "claims": claims})
    with pytest.raises(ValidationError):
        schema.model_validate({"title": "Global, 2026", "claims": []})


def test_numeric_and_peak_measure_regressions_fail_without_model_repair():
    from src.pilot._evidence import EvidenceComponent
    from src.pilot._scope import validate_claim_measure_and_numbers
    component = EvidenceComponent(component_id="r1", question_anchor="What?", status="supported",
        short_answer="12 MWh", evidence=[{"source_id": "a", "quote": "Output was 12.0 MWh; demand was 1 300 TWh."}])
    validate_claim_measure_and_numbers("Output: 12 MWh; demand: 1,300 TWh.", component)
    with pytest.raises(ValueError, match="numeric"):
        validate_claim_measure_and_numbers("Output: 13 MWh.", component)
    with pytest.raises(ValueError, match="Peak demand"):
        validate_claim_measure_and_numbers("Peak demand increases.", component, "How does regional electricity demand change?")
    validate_claim_measure_and_numbers("Peak demand increases.", component, "How does peak electricity demand change?")


def test_local_decoder_does_not_invent_optional_semantic_classifications():
    from src.pilot._requests import requested_components
    from pydantic import ValidationError
    catalog = build_span_catalog({"a": {"content": "Output increased."}})
    question = "What changed?"
    schema = constrained_selection(EvidenceSelection, GeographySelection,
        geography_choices(catalog, question), requested_components(question))
    value = {"components": [{"component_id": "r1", "status": "supported", "short_answer": "Output increased.", "evidence": list(catalog)}],
        "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "No place."}}
    assert schema.model_validate(value).components[0].kind == "unknown"
    value["components"][0]["kind"] = "projection"
    with pytest.raises(ValidationError):
        schema.model_validate(value)


def test_single_location_decoder_cannot_repeat_its_geographic_citation():
    from pydantic import ValidationError
    catalog = build_span_catalog({"a": {"content": "Output in Cedar Bay increased."}})
    schema = constrained_selection(EvidenceSelection, GeographySelection, geography_choices(catalog, "Cedar Bay"))
    sid = next(iter(catalog))
    value = {"components": [{"component_id": "r1", "status": "supported", "short_answer": "Output increased.", "evidence": [sid]}],
        "geography": {"status": "known", "value": "Cedar Bay", "evidence": [sid, sid], "reason": ""}}
    with pytest.raises(ValidationError): schema.model_validate(value)
    value["geography"]["evidence"] = [sid]
    assert schema.model_validate(value).geography.value == "Cedar Bay"
