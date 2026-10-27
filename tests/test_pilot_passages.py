"""Derived source records are reversible exact overlaps, never approximate text repair."""
import hashlib

import pytest
from pydantic import ValidationError

from src.pilot._choices import constrained_selection, geography_choices, period_choices
from src.pilot._evidence import EvidenceSelection, GeographySelection, build_span_catalog
from src.pilot._passages import assemble


def records():
    overlap = "a sufficiently long exact shared passage fragment "
    return [{"source_id": "doc:6:0", "doc_name": "doc", "page_num": 6, "url": "https://example.invalid/doc",
             "published": "2020-06-01", "content": "First sentence. " + overlap},
            {"source_id": "doc:6:1", "doc_name": "doc", "page_num": 6, "url": "https://example.invalid/doc",
             "published": "2020-06-01", "content": overlap + "completed without changing punctuation."}]


def test_exact_overlap_is_deterministic_and_original_members_resolve_by_offsets_and_hashes():
    original = records()
    context = assemble(original)
    assert context == assemble(list(reversed(original)))
    assert context["page_num"] == 6 and context["source_id"].startswith("context:")
    for member in context["provenance"]["members"]:
        source = next(r for r in original if r["source_id"] == member["source_id"])
        assert context["content"][member["context_start"]:member["context_end"]] == source["content"]
        assert member["content_sha256"] == hashlib.sha256(source["content"].encode()).hexdigest()
    changed = records()
    changed[-1]["content"] += " Updated."
    assert assemble(changed)["source_id"] != context["source_id"]


@pytest.mark.parametrize("change", ["no_overlap", "page", "document", "url", "publication", "gap", "oversize"])
def test_assembly_rejects_approximation_and_cross_source_boundaries(change):
    original = records()
    if change == "no_overlap": original[-1]["content"] = "No exact shared span."
    elif change == "page": original[-1]["page_num"] = 7
    elif change == "document": original[-1]["doc_name"] = "other"
    elif change == "url": original[-1]["url"] = "https://example.invalid/other"
    elif change == "publication": original[-1]["published"] = "2021-06-01"
    elif change == "gap": original[-1]["source_id"] = "doc:6:2"
    else: original[-1]["content"] += " word" * 1000
    assert assemble(original) is None


def test_decoder_cannot_copy_question_only_period_or_publication_date():
    catalog = build_span_catalog({"a": {"content": "Output was 14 MWh. Published in August 2026."}})
    periods = period_choices(catalog)
    assert periods == []
    schema = constrained_selection(EvidenceSelection, GeographySelection,
        geography_choices(catalog, "What changed in August 2026?", explicit_only=True), periods=periods)
    value = {"components": [{"component_id": "r1", "status": "supported", "short_answer": "14 MWh", "evidence": [next(iter(catalog))]}],
        "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "No place."}, "period": "August 2026"}
    with pytest.raises(ValidationError): schema.model_validate(value)
    value["period"] = ""
    assert schema.model_validate(value).period == ""
    actual = build_span_catalog({"a": {"content": "Output was 14 MWh in June 2019."}})
    assert period_choices(actual)[0]["value"] == "June 2019"
