"""Mapper schema regressions independent of ignored local experiment files."""
import copy
import json

import pytest
from pydantic import ValidationError

from src.pilot._evidence import EvidenceMap, EvidenceSelection, MAPPING_INSTRUCTION, validate_mapping


def payload(status="supported"):
    return {"components": [{"component_id": "output", "question_anchor": "output",
        "status": status, "short_answer": "Output was 8 MWh.",
        "evidence": [{"source_id": "s", "quote": "Output was 8 MWh."}]}]}


def test_model_schema_requires_answers_and_quotations_without_defaults():
    component = EvidenceMap.model_json_schema()["$defs"]["EvidenceComponent"]
    for name in ["short_answer", "evidence"]:
        assert name in component["required"]
        assert "default" not in component["properties"][name]


@pytest.mark.parametrize("omitted", [["short_answer"], ["evidence"], ["short_answer", "evidence"]])
@pytest.mark.parametrize("status", ["supported", "partial", "missing", "conflicting"])
def test_omission_is_a_parse_failure_not_silent_defaulting(omitted, status):
    value = payload(status)
    for field in omitted:
        del value["components"][0][field]
    before = copy.deepcopy(value)
    with pytest.raises(ValidationError):
        EvidenceMap.model_validate(value)
    assert value == before


def test_explicit_empty_missing_information_remains_a_valid_abstention_map():
    value = payload("missing")
    value["components"][0].update(short_answer="", evidence=[])
    mapping = validate_mapping(value, "What was output?", {}, "2026-10-24")
    assert mapping.components[0].short_answer == ""
    assert mapping.components[0].evidence == []


@pytest.mark.parametrize("status", ["supported", "partial"])
def test_required_fields_do_not_allow_empty_supported_answers(status):
    value = payload(status)
    value["components"][0].update(short_answer="", evidence=[])
    with pytest.raises(ValueError, match="requires an answer and quotations"):
        validate_mapping(value, "What was output?", {}, "2026-10-24")


def test_prompt_examples_have_every_core_field_and_use_distinct_support_states():
    examples = [json.loads(line) for line in MAPPING_INSTRUCTION.splitlines() if line.startswith("{")]
    assert len(examples) == 3
    for example in examples:
        EvidenceSelection.model_validate(example)
    assert [e["components"][0]["status"] for e in examples] == ["supported", "missing", "supported"]
    assert "Geography, period and document headings are attributes" in MAPPING_INSTRUCTION
