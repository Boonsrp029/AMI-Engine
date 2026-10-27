"""Application-owned request identities and citations; no LLM-quality claims."""
import copy

import pytest
from pydantic import ValidationError

from src.pilot._evidence import ComposedBrief, EvidenceSelection, build_span_catalog, project_draft, resolve_selection
from src.pilot._requests import requested_components


@pytest.mark.parametrize("question,anchors", [
    ("What drove headline and core inflation?", ["What drove headline and core inflation?"]),
    ("What changed in exports, and what supported them?", ["What changed in exports", "what supported them?"]),
    ("How did investment and consumption change, and which activities supported them?",
     ["investment", "consumption"]),
    ("What was capacity? What was its share?", ["What was capacity?", "What was its share?"]),
    ("What was capacity, but what remained unknown?", ["What was capacity", "what remained unknown?"]),
    ("What did 'Rock and Roll' mean?", ["What did 'Rock and Roll' mean?"]),
])
def test_only_explicit_new_question_clauses_are_split_without_compound_subject_loss(question, anchors):
    requests = requested_components(question)
    assert [r["question_anchor"] for r in requests] == anchors
    assert [r["component_id"] for r in requests] == [f"r{i}" for i in range(1, len(anchors) + 1)]
    assert all(r["question_anchor"] in question for r in requests)


def test_many_requests_keep_the_complete_question_instead_of_dropping_subtasks():
    question = "What was a? " + " ".join(f"What was metric {i}?" for i in range(6))
    assert requested_components(question) == [{"component_id": "r1", "question_anchor": question}]
    with pytest.raises(ValueError):
        requested_components(" ")


def test_coordinated_change_and_activity_requests_keep_both_tasks_for_each_subject():
    question = "How did farm output and retail spending change in May 2019, and which activities supported them?"
    requests = requested_components(question)
    assert [r["question_anchor"] for r in requests] == ["farm output", "retail spending"]
    assert all("both the change" in r["instruction"] for r in requests)
    assert all(r["question_anchor"] in question for r in requests)


def payload():
    sources = {"a": {"content": "Output was 6 MWh in June 2019."}}
    catalog = build_span_catalog(sources)
    value = {"components": [{"component_id": "r1", "status": "supported", "short_answer": "6 MWh",
        "evidence": list(catalog)}, {"component_id": "r2", "status": "missing", "short_answer": "", "evidence": []}],
        "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "No location in source."}}
    return sources, catalog, value


@pytest.mark.parametrize("kind", ["missing", "extra", "duplicate", "invented"])
def test_mapping_requires_each_canonical_request_once_without_filling_or_dropping(kind):
    sources, catalog, value = payload()
    if kind == "missing":
        value["components"].pop()
    elif kind == "extra":
        value["components"].append(dict(value["components"][1], component_id="r3"))
    elif kind == "duplicate":
        value["components"][1]["component_id"] = "r1"
    else:
        value["components"][1]["component_id"] = "source heading"
    before = copy.deepcopy(value)
    with pytest.raises(ValueError, match="canonical request exactly once"):
        resolve_selection(value, catalog, "What was output in June 2019, and what was its share?", sources, "2026-10-25")
    assert value == before


def test_question_anchors_are_reconstructed_from_verbatim_request_slots():
    sources, catalog, value = payload()
    question = "What was output in June 2019, and what was its share?"
    mapping = resolve_selection(value, catalog, question, sources, "2026-10-25")
    assert [c.question_anchor for c in mapping.components] == ["What was output in June 2019", "what was its share?"]
    assert mapping.components[1].status == "missing" and mapping.components[1].evidence == []
    schema = EvidenceSelection.model_json_schema()["$defs"]["EvidenceSelectionComponent"]
    assert "question_anchor" not in schema["properties"]


def test_composition_returns_text_and_identity_but_cannot_supply_its_own_citations():
    sources, catalog, value = payload()
    mapping = resolve_selection(value, catalog, "What was output in June 2019, and what was its share?", sources, "2026-10-25")
    draft, _ = project_draft({"title": "Output", "claims": [{"component_id": "r1", "text": "6 MWh"}]}, mapping)
    assert draft["claims"] == [{"text": "6 MWh", "source_ids": ["a"]}]
    with pytest.raises(ValidationError):
        ComposedBrief.model_validate({"title": "Output", "claims": [{"component_id": "r1", "text": "6 MWh", "source_ids": ["invented"]}]})
    schema = ComposedBrief.model_json_schema()["$defs"]["ComposedClaim"]
    assert set(schema["properties"]) == {"component_id", "text"}
