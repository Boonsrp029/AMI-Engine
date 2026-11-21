"""Offline checks for same-record table rows at reading boundaries."""
import hashlib
import json
import time
from types import SimpleNamespace

import pytest

from src.pilot._evidence import build_span_catalog, _resolve_span
from src.pilot.subtasks._request_focus import _conversion_focus, _table_focus, focused_text, request_focus, validate_focused_claims
from src.pilot.subtasks._table_spans import add_table_publication_spans, add_table_row_spans, table_us_scope


QUESTION = "What were tidal generation and its share of utility-scale generation in 2017?"
HEADER = "utility-scale electricity generation in 2017\nEnergy source\nBillion kWh\nShare of total\n"
ROW = "Tidal\n28\n7.0%"
TABLE = ("Synthetic table metadata\n" * 12 + HEADER + "Total - all sources\n400\n"
         + "Wind\n21\n5.2%\n" * 30 + ROW)


@pytest.mark.parametrize(("geography", "table_geography", "year", "expected"), [
    ("US", "U.S.", "2017", True),
    ("U.S.", "United States", "2017", True),
    ("United States", "U.S.", "2017", True),
    ("Canada", "U.S.", "2017", False),
    ("US", "Canada", "2017", False),
    ("US", "U.S.", "2018", False),
    ("US", "U.S. Energy Information Administration says Canada", "2017", False),
])
def test_table_geography_requires_the_requested_place_in_the_exact_heading(geography, table_geography, year, expected):
    heading = f"{table_geography} utility-scale electricity generation by source, amount, and share of total in {year}"
    content = heading + "\nEnergy source\nBillion kWh\nShare of total\n" + ROW
    start = len(heading) - len(year)
    span = {"text": content[start:], "start": start, "source_id": "grid",
            "content_sha256": hashlib.sha256(content.encode()).hexdigest()}
    anchor = f"What were tidal generation and its share of {geography} utility-scale generation in 2017?"
    scope = table_us_scope(anchor, span, {"content": content}, "2017")
    if expected:
        assert scope["label"] == "U.S."
        assert content[scope["start"]:scope["end"]] == scope["text"] == heading
    else:
        assert scope is None


def setup_table(text=TABLE, *, second=None, outcome="evidence", role="support"):
    records = {"synthetic-grid": {"content": text}}
    if second is not None:
        records["second-grid"] = {"content": second}
    sources = [SimpleNamespace(source_id=sid, role=role,
                              content_sha256=hashlib.sha256(record["content"].encode()).hexdigest())
               for sid, record in records.items()]
    report = SimpleNamespace(results=[SimpleNamespace(subtask_id="s01", outcome=outcome, sources=sources)])
    requests = [{"component_id": "r1", "question_anchor": QUESTION}]
    return requests, build_span_catalog(records), records, report, {"r1": ["s01"]}


def apply(data, existing=None):
    return add_table_row_spans(*data, existing or {})


@pytest.mark.parametrize("mode", ["complete", "other_year", "duplicate", "partial"])
def test_table_attribution_keeps_the_entire_source_title(mode):
    request = "Which publication does the 2017 table cite as its data source?"
    citation = "Data source: N.A. Grid Bureau,\nGrid Statistics Quarterly\n, March 2018; preliminary"
    text = HEADER + ROW + "\n" + citation
    if mode == "other_year":
        text = text.replace("2017", "2016")
    elif mode == "duplicate":
        text += "\n" + citation.replace("Quarterly", "Yearbook")
    elif mode == "partial":
        text = text.replace("Grid Statistics Quarterly\n", "")
    requests, catalog, sources, report, bindings = setup_table(text)
    requests[0]["question_anchor"] = request
    before = dict(catalog)
    focus = add_table_publication_spans(requests, catalog, sources, report, bindings, {})
    if mode != "complete":
        assert focus == {} and catalog == before
        return
    match = focus["r1"]
    span = catalog[match["span_id"]]
    assert text[span["start"]:span["end"]] == span["text"] == citation
    assert match["publication"] == "Grid Statistics Quarterly"
    validate_focused_claims([{"component_id": "r1", "text": focused_text(match)}], focus)
    with pytest.raises(ValueError, match="verified table publication"):
        validate_focused_claims([{"component_id": "r1", "text": "The table cites N.A. as its data source."}], focus)


def test_split_row_keeps_exact_offsets_stable_identity_and_existing_spans():
    data = setup_table()
    requests, catalog, sources, report, bindings = data
    old = dict(catalog)
    assert request_focus(requests, catalog, report, bindings) == {}
    focus = apply(data)["r1"]
    span = catalog[focus["span_id"]]
    assert span["text"].startswith("2017\nEnergy source\nBillion kWh\nShare of total")
    assert span["text"].endswith(ROW)
    assert len(span["text"]) <= 600
    assert sources[span["source_id"]]["content"][span["start"]:span["end"]] == span["text"]
    assert focus["amount"] == "28" and focus["share"] == "7.0%"
    assert focus["year"] == "2017" and focus["unit"] == "Billion kWh"
    assert all(catalog[sid] == value for sid, value in old.items())
    assert apply(setup_table())["r1"] == focus
    assert _resolve_span(focus["span_id"], catalog, sources)["quote"] == span["text"]


@pytest.mark.parametrize("outcome,role", [("conflicting", "support"), ("failed", "support"),
                                         ("evidence", "context")])
def test_ineligible_branch_does_not_gain_focus(outcome, role):
    data = setup_table(outcome=outcome, role=role)
    before = dict(data[1])
    assert apply(data) == {}
    assert data[1] == before


@pytest.mark.parametrize("second", [TABLE, TABLE.replace(ROW, "Tidal\n31\n7.8%")])
def test_multiple_source_matches_are_ambiguous(second):
    data = setup_table(second=second)
    before = dict(data[1])
    assert apply(data) == {}
    assert data[1] == before


@pytest.mark.parametrize("text", [TABLE + "\n" + ROW,
                                TABLE.replace("in 2017", "in 2016"),
                                TABLE.replace("Billion kWh", "MW"),
                                TABLE.replace(ROW, "Tidal\n28\nOther\n7.0%")])
def test_incomplete_wrong_period_or_ambiguous_row_has_no_focus(text):
    assert apply(setup_table(text)) == {}


def test_header_and_values_in_different_records_cannot_form_row():
    data = setup_table(HEADER + "Tidal", second="28\n7.0%")
    assert apply(data) == {}


def test_multiple_bound_branches_and_existing_focus_are_untouched():
    data = setup_table()
    data[4]["r1"] = ["s01", "s02"]
    assert apply(data) == {}
    data = setup_table()
    before = dict(data[1])
    assert apply(data, {"r1": {"span_id": "existing"}}) == {}
    assert data[1] == before


def test_mutated_content_is_rejected():
    data = setup_table()
    data[2]["synthetic-grid"]["content"] += "\nChanged."
    with pytest.raises(ValueError, match="content hash changed"):
        apply(data)


def test_crlf_unicode_and_footnote_are_preserved():
    data = setup_table(TABLE.replace(ROW, "Tidal\n3\n28\n7.0%").replace("\n", "\r\n") + "\r\nCafé")
    focus = apply(data)["r1"]
    assert data[1][focus["span_id"]]["text"].endswith("Tidal\r\n3\r\n28\r\n7.0%")


def test_overlong_row_has_no_added_span():
    label = "Tidal " + "a" * 600
    data = setup_table(TABLE.replace(ROW, label + "\n28\n7.0%"))
    data[0][0]["question_anchor"] = QUESTION.replace("tidal", label)
    assert apply(data) == {}


@pytest.mark.parametrize("duplicate", [False, True])
@pytest.mark.parametrize("negative_before", [False, True])
@pytest.mark.parametrize("negative_requested", [False, True])
def test_scoped_mapper_composer_selects_complete_bound_row(tmp_path, duplicate, negative_before, negative_requested):
    from src.pilot.subtasks._disclosures import DisclosureScopes, bindings_hash
    from src.pilot.subtasks._scoped_generation import ScopedConcurrentComposer
    from src.pilot.subtasks.contracts import Plan, Subtask
    from src.pilot.subtasks.retrieval import LocalBM25Adapter
    from src.pilot.subtasks.runner import ModelAccess
    from src.pilot.subtasks.scheduler import run_plan

    corpus = tmp_path / "corpus.json"
    requested_row = "Tidal\n-9\n-2.25%" if negative_requested else ROW
    preceding_row = "Storage balancing\n7\n-17\n-4.25%\n" if negative_before else ""
    text = TABLE.replace(ROW, preceding_row + requested_row)
    corpus.write_text(json.dumps([{"feed_id": "synthetic-grid", "clean_content": text}]), encoding="utf-8")
    plan = Plan(query=QUESTION, corpus_sha256=hashlib.sha256(corpus.read_bytes()).hexdigest(),
                subtasks=(Subtask(subtask_id="s01", operation="retrieve", query=QUESTION),))
    bindings = {"r1": ["s01"]}
    scopes = DisclosureScopes.model_validate({
        "plan_id": plan.plan_id, "corpus_sha256": plan.corpus_sha256,
        "question_sha256": hashlib.sha256(QUESTION.encode()).hexdigest(),
        "bindings_sha256": bindings_hash(bindings), "declaration_ref": "Synthetic boundary regression",
        "annotations": [{"component_id": "r1", "subtask_id": "s01",
                         "question_span": {"start": 0, "end": len(QUESTION)}}]})
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(corpus))
    stages = []

    def fixed(stage, schema, instruction, inputs):
        stages.append(stage)
        if stage == "mapping":
            focus = inputs["request_focus"]["r1"]
            sid = focus["span_id"]
            span, = [part for record in inputs["evidence"] for part in record["spans"]
                     if part["span_id"] == sid]
            assert span["text"].startswith("2017\nEnergy source") and span["text"].endswith(requested_row)
            value = {"wire_version": "cq-fact-span-selection-v1", "facts": [{"fact_id": "r1.1",
                "state": "supported", "alternatives": [[{"span_id": sid, "context": []}] * (5 if duplicate else 1)]}],
                "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "No place stated."}}
        else:
            assert inputs["units"][0]["response_kind"] == "table_row"
            value = {"title": "Analyst research brief", "claims": [{"component_id": "r1", "unit_id": "u1"}]}
        return {"parsed": schema.model_validate(value).model_dump()}

    callback = ScopedConcurrentComposer(plan, bindings, "2026-11-17", fixed, scopes,
                                       complete_required_branches=bindings, fact_selection=True,
                                       whole_fact_spans=True)
    if duplicate:
        with pytest.raises(ValueError):
            callback(report, ModelAccess(time.monotonic() + 30))
        assert stages == ["mapping"]
    else:
        result = callback(report, ModelAccess(time.monotonic() + 30))
        assert stages == ["mapping", "composition"]
        amount, share = ("-9", "-2.25%") if negative_requested else ("28", "7.0%")
        assert result.draft["claims"] == [{"text": f"In 2017, the table gives Tidal generation in Billion kWh as {amount} "
            f"and its share of total utility-scale electricity generation as {share}.", "source_ids": ["synthetic-grid"]}]


@pytest.mark.parametrize("marker", ["", "7\n"])
def test_requested_negative_row_keeps_signs_and_footnote_distinct(marker):
    text = TABLE.replace(ROW, "Tidal\n" + marker + "-9\n-2.25%")
    data = setup_table(text)
    focus = apply(data)["r1"]
    assert focus["amount"] == "-9" and focus["share"] == "-2.25%"
    span = data[1][focus["span_id"]]
    assert span["text"].endswith("Tidal\n" + marker + "-9\n-2.25%")


@pytest.mark.parametrize("amount,share", [("--9", "-2.5%"), ("-9", "--2.5%"),
                                         ("9-", "2.5%"), ("-", "-2.5%")])
def test_malformed_signed_row_is_not_skipped_to_offer_later_focus(amount, share):
    text = TABLE.replace(ROW, f"Storage balancing\n{amount}\n{share}\n" + ROW)
    assert _table_focus(QUESTION, text) == []
    assert apply(setup_table(text)) == {}


def test_signed_table_parsing_does_not_admit_negative_conversion_pairs():
    question = "How many kilowatts and watts are equivalent to one megawatt?"
    positive = "One megawatt is 1,000 kilowatts and 1,000,000 watts."
    assert _conversion_focus(question, positive)[0]["targets"] == {"kw": "1000", "w": "1000000"}
    assert _conversion_focus(question, positive.replace("1,000", "-1,000")) == []
