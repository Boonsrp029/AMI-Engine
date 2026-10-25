"""Offline scope propagation; synthetic values are not generated quality evidence."""

import json
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from src.pilot._evidence import build_span_catalog, project_draft, resolve_selection
from src.pilot._scope import explicit_periods, resolve_scope
from src.pilot.engine import Corpus, PilotEngine


QUESTION = "What was Elm Bay's capacity in March 2020, and what supported expansion?"
SOURCES = {"capacity": {"source_id": "capacity", "content": "Elm Bay capacity was 9 GWh in March 2020."},
    "cause": {"source_id": "cause", "content": "Expansion was supported by new links entering service."}}


def mapped(geography=""):
    catalog = build_span_catalog(SOURCES)
    ids = {span["source_id"]: sid for sid, span in catalog.items()}
    geo = ({"status": "known", "value": geography, "evidence": [ids["capacity"]], "reason": ""}
        if geography else {"status": "unresolved", "value": "", "evidence": [],
                           "reason": "Geographic scope is unresolved in this fixture."})
    value = {"geography": geo, "components": [
        {"component_id": "r1", "status": "supported",
         "short_answer": "9 GWh", "evidence": [ids["capacity"]]},
        {"component_id": "r2", "status": "supported",
         "short_answer": "New links entering service.", "evidence": [ids["cause"]]}]}
    return resolve_selection(value, catalog, QUESTION, SOURCES, "2026-10-25")


@pytest.mark.parametrize("text,expected", [
    ("March 2020 and march 2020", ["March 2020"]),
    ("2020-02-29 and 2021-02-29", ["2020-02-29"]),
    ("March 0000; March 20222; 2026-13-01", []),
    ("A March\n2020 release compared 2020-03-15", ["March 2020", "2020-03-15"]),
    ("May 2020 and June 2021", ["May 2020", "June 2021"]),
    ("2020, yesterday, Mar 2020, Q1 2020", []),
])
def test_explicit_period_recognition_is_narrow_and_validated(text, expected):
    assert explicit_periods(text) == expected


def test_fragment_answer_gains_source_backed_period_without_mutating_mapping():
    value = mapped()
    before = value.model_dump()
    revised, context = resolve_scope(value, QUESTION)
    assert value.model_dump() == before
    assert revised.period == "March 2020"
    assert revised.geography == ""  # No geographic inference from names or possessives.
    assert context["fields"]["period"]["evidence"][0]["source_id"] == "capacity"
    draft, restored = project_draft({"title": "Capacity", "claims": []}, revised, QUESTION, context)
    assert draft["claims"][0]["text"] == "March 2020: 9 GWh"
    assert draft["claims"][1]["text"] == "New links entering service."
    assert "March 2020" in draft["title"]
    assert restored == ["r1", "r2"]


def test_provided_geography_is_qualified_only_on_components_that_support_it():
    revised, context = resolve_scope(mapped("Elm Bay"), QUESTION)
    draft, _ = project_draft({"title": "Brief", "claims": [
        {"component_id": "r1", "text": "9 GWh"},
        {"component_id": "r2", "text": "New links entering service."}]},
        revised, QUESTION, context)
    assert draft["claims"][0]["text"] == "Elm Bay, March 2020: 9 GWh"
    assert draft["claims"][1]["text"] == "New links entering service."
    assert draft["title"].endswith("(Elm Bay, March 2020)")


def test_already_scoped_text_does_not_gain_duplicate_labels():
    revised, context = resolve_scope(mapped("Elm Bay"), QUESTION)
    text = "Elm Bay capacity in March 2020 was 9 GWh."
    draft, _ = project_draft({"title": "Elm Bay March 2020", "claims": [
        {"component_id": "r1", "text": text}]}, revised, QUESTION, context)
    assert draft["claims"][0]["text"] == text


def test_scope_qualification_keeps_the_scope_sources_in_the_claim_citations():
    mapping = mapped("Elm Bay")
    first = mapping.components[0].model_copy(update={"evidence": [
        mapping.components[0].evidence[0],
        mapping.components[0].evidence[0].model_copy(update={"source_id": "quantity", "quote": "Capacity was 9 GWh."})]})
    mapping = mapping.model_copy(update={"components": [first]})
    revised, context = resolve_scope(mapping, QUESTION)
    draft, _ = project_draft({"title": "Brief", "claims": [
        {"component_id": "r1", "text": "9 GWh"}]}, revised, QUESTION, context)
    assert draft["claims"][0] == {"text": "Elm Bay, March 2020: 9 GWh", "source_ids": ["capacity", "quantity"]}


def test_period_in_composed_claim_must_be_present_in_that_components_evidence():
    revised, context = resolve_scope(mapped(), QUESTION)
    with pytest.raises(ValueError, match="period absent"):
        project_draft({"title": "x", "claims": [
            {"component_id": "r1", "text": "9 GWh in March 2021."}]},
            revised, QUESTION, context)
    with pytest.raises(ValueError, match="period absent"):
        project_draft({"title": "x", "claims": [
            {"component_id": "r2", "text": "New links in March 2020."}]},
            revised, QUESTION, context)


@pytest.mark.parametrize("field,value", [("period", "April 2020"), ("geography", "Other Bay")])
def test_question_only_or_invented_scope_is_not_attached_to_evidence(field, value):
    mapping = mapped().model_copy(update={field: value})
    with pytest.raises(ValueError, match="selected supporting quotations|resolution does not match"):
        resolve_scope(mapping, QUESTION + " " + value)


def test_no_period_inference_from_source_publication_forecast_or_other_requested_dates():
    mapping = mapped()
    for question in ["What was capacity yesterday?", "What was capacity in 2026-10-25?",
                     "Compare March 2020 and April 2020 capacity."]:
        revised, context = resolve_scope(mapping, question)
        assert revised.period == ""
        assert revised.geography == ""
    _, context = resolve_scope(mapping, "What was capacity in 2026-10-25?")
    assert context["unresolved_requested_periods"] == ["2026-10-25"]


def test_publication_date_inside_a_quotation_does_not_establish_measurement_period():
    mapping = mapped()
    publication = mapping.components[0].evidence[0].model_copy(update={
        "quote": "Published March 2020, this report records historical capacity of 9 GWh."})
    component = mapping.components[0].model_copy(update={"evidence": [publication]})
    mapping = mapping.model_copy(update={"components": [component]})
    revised, context = resolve_scope(mapping, QUESTION)
    assert revised.period == ""
    assert context["unresolved_requested_periods"] == ["March 2020"]
    with pytest.raises(ValueError, match="selected supporting quotations"):
        resolve_scope(mapping.model_copy(update={"period": "March 2020"}), QUESTION)


def test_unrelated_date_in_another_selected_span_is_not_copied_onto_an_answer():
    mapping = mapped()
    evidence = mapping.components[0].evidence[0].model_copy(update={"quote": "A plan was considered in March 2020."})
    component = mapping.components[0].model_copy(update={"evidence": [evidence]})
    revised, context = resolve_scope(mapping.model_copy(update={"components": [component]}), QUESTION)
    assert revised.period == ""
    assert context["unresolved_requested_periods"] == ["March 2020"]


def test_missing_information_does_not_gain_scope_or_trigger_qualification():
    mapping = mapped()
    missing = [c.model_copy(update={"status": "missing", "short_answer": "", "evidence": []})
               for c in mapping.components]
    mapping = mapping.model_copy(update={"components": missing})
    revised, context = resolve_scope(mapping, QUESTION)
    assert revised == mapping
    assert context == {"fields": {}, "components": {}, "unresolved_requested_periods": [],
                       "geography_resolution": mapping.geography_resolution.model_dump()}


def test_long_claim_is_rejected_without_truncating_the_answer():
    revised, context = resolve_scope(mapped("Elm Bay"), QUESTION)
    with pytest.raises(ValueError, match="public text limit"):
        project_draft({"title": "x", "claims": [
            {"component_id": "r1", "text": "a" * 800}]},
            revised, QUESTION, context)


@pytest.mark.parametrize("guard_passes", [True, False])
def test_final_scope_qualification_reaches_guardrails_without_extra_model_calls(tmp_path, guard_passes):
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps([{"feed_id": "known", "clean_content": SOURCES["capacity"]["content"],
        "published": "2026-10-25"}]), encoding="utf-8")
    corpus = Corpus(path)
    tool_responses = iter([AIMessage(content="", tool_calls=[{
        "name": "search_sources", "args": {"query": "capacity", "limit": 5}, "id": "1"}]), AIMessage(content="done")])
    stages, checked, events = [], [], []
    def structured(schema, **_):
        def invoke(messages):
            stages.append(schema.__name__)
            if schema.__name__ == "EvidenceSelection":
                payload = json.loads(messages[1].content)
                sid = payload["evidence"][0]["spans"][0]["span_id"]
                value = {"geography": {"status": "known", "value": "Elm Bay", "evidence": [sid], "reason": ""},
                    "components": [{"component_id": "r1",
                    "status": "supported", "short_answer": "9 GWh",
                    "evidence": [sid]}, {"component_id": "r2", "status": "missing", "short_answer": "", "evidence": []}]}
            else:
                value = {"title": "Capacity", "claims": []}
            return {"parsed": schema.model_validate(value), "raw": AIMessage(content="")}
        return SimpleNamespace(invoke=invoke)
    model = SimpleNamespace(bind_tools=lambda _: SimpleNamespace(invoke=lambda _: next(tool_responses)),
                            with_structured_output=structured)
    guard = SimpleNamespace(validate_output=lambda **kwargs: checked.append(kwargs) or {"passed_guardrails": guard_passes})
    engine = PilotEngine(corpus, model, guard)
    if guard_passes:
        result = engine.run(QUESTION, lambda *e: events.append(e))
        assert result["metrics"]["model_calls"] == 4
        assert result["draft"]["claims"][0]["text"] == "Elm Bay, March 2020: 9 GWh"
        assert any(kind == "evidence_scope" for kind, _ in events)
    else:
        with pytest.raises(ValueError, match="guardrails"):
            engine.run(QUESTION)
    assert checked[0]["raw_report"] == "Elm Bay, March 2020: 9 GWh"
    assert stages == ["EvidenceSelection", "ComposedBrief"]
