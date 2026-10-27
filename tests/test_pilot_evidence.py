"""Private mapping constraints and workflow integration with fixed model responses."""

import copy
import json
from datetime import date
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from src.pilot._evidence import (
    ComposedBrief, EvidenceMap, EvidenceSelection, NO_INFORMATION, evidence_gaps, project_draft,
    relative_dates, supported_components, validate_mapping,
)
from src.pilot._presentation import pdf_page_label
from src.pilot._requests import requested_components
from src.pilot.engine import Corpus, PilotEngine
from src.pilot.schemas import ResearchRequest, ReviewRequest
from src.pilot.store import Store


QUESTION = "What was Region A capacity in August 2026 and what was its share?"
TEXT = "Region A capacity was 12 GWh in August 2026."
SOURCES = {"a": {"content": TEXT}, "b": {"content": "Region A capacity was 15 GWh in August 2026."}}


def mapping_value():
    return {"geography": "Region A", "period": "August 2026", "components": [{
        "component_id": "capacity", "question_anchor": "capacity", "status": "supported",
        "short_answer": TEXT, "evidence": [{"source_id": "a", "quote": TEXT}],
        "measure": "capacity", "scenario": "", "kind": "actual",
    }]}


def validated(value=None):
    return validate_mapping(value or mapping_value(), QUESTION, SOURCES, "2026-10-24")


def test_whitespace_quotation_matching_and_requested_scope():
    value = mapping_value()
    value["components"][0]["evidence"][0]["quote"] = TEXT.replace(" ", "\n  ")
    assert validated(value).period == "August 2026"


@pytest.mark.parametrize("field,value", [
    ("question_anchor", "not asked"), ("question_anchor", "   "),
    ("gap_anchor", "unrequested country breakdown"), ("gap_anchor", "  "),
    ("short_answer", ""), ("evidence", []),
])
def test_invalid_supported_components_fail(field, value):
    candidate = mapping_value()
    candidate["components"][0][field] = value
    with pytest.raises(ValueError):
        validated(candidate)


@pytest.mark.parametrize("change", ["source", "quote", "scope", "duplicate", "empty", "excess", "malformed"])
def test_invalid_mapping_contracts(change):
    value = mapping_value()
    if change == "source":
        value["components"][0]["evidence"][0]["source_id"] = "unknown"
    elif change == "quote":
        value["components"][0]["evidence"][0]["quote"] = "Capacity was 900 GWh."
    elif change == "scope":
        value["geography"] = "Invented country"
    elif change == "duplicate":
        value["components"] *= 2
    elif change == "empty":
        value["components"] = []
    elif change == "excess":
        value["components"] *= 6
    else:
        value["unexpected"] = True
    with pytest.raises(ValueError):
        validated(value)


def test_partial_answer_has_only_requested_gap():
    value = mapping_value()
    value["components"][0].update(status="partial", gap_anchor="share")
    mapping = validated(value)
    draft, fallback = project_draft({"title": "Brief", "claims": []}, mapping)
    assert draft["claims"] == [{"text": TEXT, "source_ids": ["a"]}]
    assert draft["warnings"] == ["The retrieved documents do not establish the following: share"]
    assert fallback == ["capacity"]
    assert draft["title"] == "Brief (Region A, August 2026)"


def test_conflict_is_retained_for_review_without_selecting_one_value():
    value = mapping_value()
    component = value["components"][0]
    component.update(status="conflicting", short_answer="")
    component["evidence"].append({"source_id": "b", "quote": SOURCES["b"]["content"]})
    mapping = validated(value)
    assert supported_components(mapping) == []
    assert evidence_gaps(mapping) == ["The retrieved documents contain unresolved statements for: capacity"]


@pytest.mark.parametrize("status", ["missing", "conflicting"])
def test_unresolved_components_cannot_supply_answers(status):
    value = mapping_value()
    value["components"][0]["status"] = status
    with pytest.raises(ValueError):
        validated(value)


def test_conflict_requires_distinct_quotes_and_missing_has_no_evidence():
    for status in ["missing", "conflicting"]:
        value = mapping_value()
        value["components"][0].update(status=status, short_answer="")
        with pytest.raises(ValueError):
            validated(value)


@pytest.mark.parametrize("kind", ["unknown_component", "unsupported_component", "wrong_source", "duplicate"])
def test_composition_rejects_invalid_component_links(kind):
    value = mapping_value()
    missing = {"component_id": "share", "question_anchor": "share", "status": "missing", "short_answer": "", "evidence": []}
    value["components"].append(missing)
    mapping = validated(value)
    claim = {"component_id": "capacity", "text": TEXT}
    if kind == "unknown_component":
        claim["component_id"] = "imaginary"
    elif kind == "unsupported_component":
        claim["component_id"] = "share"
    elif kind == "wrong_source":
        claim["source_ids"] = ["b"]
    claims = [claim] * (2 if kind == "duplicate" else 1)
    with pytest.raises(ValueError):
        project_draft({"title": "Brief", "claims": claims}, mapping)


def test_five_missing_composition_components_are_restored_within_public_limit():
    value = mapping_value()
    value["components"] = [dict(copy.deepcopy(value["components"][0]), component_id=f"c{i}") for i in range(5)]
    draft, restored = project_draft({"title": "x" * 160, "claims": []}, validated(value))
    assert len(draft["claims"]) == len(restored) == 5
    assert len(draft["title"]) <= 160
    assert draft["title"].endswith("(Region A, August 2026)")


def test_relative_dates_do_not_use_source_publication_as_observation_date():
    assert relative_dates("What was yesterday's price, compared with today?", "2026-10-24") == {
        "yesterday": "2026-10-23", "today": "2026-10-24"}
    candidate = mapping_value()
    candidate["period"] = "2026-10-24"
    with pytest.raises(ValueError, match="scope"):
        validated(candidate)


class WorkflowModel:
    def __init__(self, mapping, composed=None, fail=None):
        self.mapping = mapping
        self.composed = composed or {"title": "Analyst research brief", "claims": []}
        self.fail = fail
        self.stages = []
        self.messages = {}
        self.plans = iter([AIMessage(content="", tool_calls=[{
            "name": "search_sources", "args": {"query": "Region", "limit": 5}, "id": "1",
        }]), AIMessage(content="done")])

    def bind_tools(self, _):
        return SimpleNamespace(invoke=lambda _: next(self.plans))

    def with_structured_output(self, schema, **_):
        def invoke(messages):
            self.stages.append(schema.__name__)
            self.messages[schema.__name__] = messages
            if self.fail == schema.__name__:
                raise RuntimeError("synthetic model failure")
            value = copy.deepcopy(self.mapping) if issubclass(schema, EvidenceSelection) else self.composed
            if issubclass(schema, EvidenceSelection) and value is not None:
                sources = json.loads(messages[1].content)["evidence"]
                for component in value["components"]:
                    component["evidence"] = [next(
                        span["span_id"] for source in sources if source["source_id"] == quote["source_id"]
                        for span in source["spans"] if quote["quote"] in span["text"])
                        for quote in component["evidence"]]
                requests = requested_components(json.loads(messages[1].content)["question"])
                if value["components"]:
                    for component, request in zip(value["components"], requests):
                        component["component_id"] = request["component_id"]
                        component.pop("question_anchor", None)
                        # The local decoder no longer guesses optional classifications.
                        component.update(measure="", scenario="", kind="unknown")
                    for request in requests[len(value["components"]):]:
                        value["components"].append({"component_id": request["component_id"], "status": "missing",
                            "short_answer": "", "evidence": []})
                geography = value.get("geography", "")
                value["geography"] = ({"status": "known", "value": geography, "reason": "", "evidence": [
                    span["span_id"] for source in sources for span in source["spans"]
                    if geography in span["text"]][:1]} if geography else {
                    "status": "unresolved", "value": "", "evidence": [],
                    "reason": "This fixture does not establish geography."})
            return {"parsed": schema.model_validate(value) if value is not None else None,
                    "raw": AIMessage(content="", usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15})}
        return SimpleNamespace(invoke=invoke)


@pytest.fixture
def corpus(tmp_path):
    path = tmp_path / "public.json"
    path.write_text(json.dumps([{"feed_id": "a", "title": "Region A", "clean_content": TEXT,
        "page_num": 6, "published": "2026-10-01", "source": "https://example.invalid"}]), encoding="utf-8")
    return Corpus(path)


def test_final_fallback_claims_are_checked_by_real_guardrail_boundary(corpus):
    checked, events = [], []
    guard = SimpleNamespace(validate_output=lambda **kwargs: checked.append(kwargs) or {"passed_guardrails": True})
    model = WorkflowModel(mapping_value())
    result = PilotEngine(corpus, model, guard).run(QUESTION, lambda *e: events.append(e))
    assert result["metrics"]["model_calls"] == 4
    assert result["metrics"]["known_input_tokens"] == 20
    assert checked[0]["raw_report"] == TEXT
    assert result["draft"]["claims"][0]["text"] == TEXT
    assert any(kind == "component_coverage" and data["fallback_component_ids"] == ["r1"] for kind, data in events)
    assert json.loads(model.messages["EvidenceSelection"][1].content)["as_of"] == json.loads(model.messages["ComposedBrief"][1].content)["as_of"]


def test_guardrail_rejection_cannot_be_bypassed_by_fallback(corpus):
    with pytest.raises(ValueError, match="guardrails"):
        PilotEngine(corpus, WorkflowModel(mapping_value()), SimpleNamespace(
            validate_output=lambda **_: {"passed_guardrails": False})).run(QUESTION)


def test_genuine_absence_returns_exact_message_and_skips_composer(corpus):
    value = {"components": [{"component_id": "price", "question_anchor": "yesterday's price",
                            "status": "missing", "short_answer": "", "evidence": []}]}
    model = WorkflowModel(value)
    result = PilotEngine(corpus, model).run("What was yesterday's price?")
    assert result["draft"]["warnings"] == [NO_INFORMATION,
        "The retrieved documents do not establish an answer to: What was yesterday's price?"]
    assert result["draft"]["claims"] == []
    assert result["metrics"]["model_calls"] == 2
    assert result["metrics"]["guardrail_invocations"] == 0
    assert model.stages == []


@pytest.mark.parametrize("value", [None, {"components": []}])
def test_malformed_mapping_fails_without_composition_or_retry(corpus, value):
    model = WorkflowModel(value)
    events = []
    with pytest.raises(ValueError):
        PilotEngine(corpus, model).run(QUESTION, lambda *event: events.append(event))
    assert model.stages == ["EvidenceSelection"]
    assert any(e[0] == "evidence_mapping_failure" for e in events) == (value is None)


@pytest.mark.parametrize("stage", ["EvidenceSelection", "ComposedBrief"])
def test_model_failure_is_not_retried(corpus, stage):
    model = WorkflowModel(mapping_value(), fail=stage)
    with pytest.raises(RuntimeError, match="synthetic"):
        PilotEngine(corpus, model).run(QUESTION)
    assert model.stages.count(stage) == 1


@pytest.mark.parametrize("index,label", [(0, "PDF page 1"), (6, "PDF page 7"),
    (None, "PDF page unavailable"), (-1, "PDF page unavailable"), ("6", "PDF page unavailable"),
    (False, "PDF page unavailable"), (1.5, "PDF page unavailable")])
def test_pdf_pages_are_reader_facing_without_coercing_invalid_indexes(index, label):
    assert pdf_page_label(index) == label


def test_new_export_pages_and_cached_export_bytes_are_stable(tmp_path, corpus):
    store = Store(tmp_path / "history.db")
    run_id, _ = store.create(ResearchRequest(query=QUESTION, request_key="unique-key"), corpus.sha)
    store.claim(run_id)
    draft, _ = project_draft({"title": "Analyst research brief", "claims": []}, validated())
    store.save_draft(run_id, draft, corpus.sources, {})
    store.review(run_id, ReviewRequest(revision=1, decision="approve", reviewer="owner", support_confirmed=True))
    content, _ = store.export(run_id)
    assert "PDF page 7" in content
    assert store.get(run_id)["sources"]["a"]["page_num"] == 6
    with store.connection() as db:
        db.execute("UPDATE exports SET content=? WHERE run_id=?", ("historical export bytes; PDF page 6\n", run_id))
    assert store.export(run_id)[0] == "historical export bytes; PDF page 6\n"
