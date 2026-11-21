"""Exercise focused requests through the scoped mapper and composer."""
import hashlib
import json
import time

import pytest

from src.pilot.subtasks._disclosures import DisclosureScopes, bindings_hash
from src.pilot.subtasks._request_focus import _capacity_focus, _table_focus, relevance_hints, validate_focused_claims
from src.pilot.subtasks._request_focus import _single_power_focus, focused_text
from src.pilot.subtasks._scoped_generation import (
    ScopedConcurrentComposer, WIRE_VERSION, _validate_explicit_subjects, table_composition_schema,
)
from src.pilot._evidence import EvidenceMap
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


TABLE = ("utility-scale electricity generation in 2018\nEnergy source\nBillion kWh\nShare of total\n"
         "Total - all sources\n510\nWind\n62\n12.2%\nHydropower\n2\n119\n23.3%\nBiomass\n35\n6.9%")
RATIO = "The delivery rate divides completed deliveries by all scheduled deliveries for the same week."


@pytest.mark.parametrize("claim", [
    "The minimum total payload capacity is 3 kilograms.",
    "The total payload capacity is 3 kilograms (3,000 grams).",
    "The minimum total payload capacity is 3,000 kilograms (3 grams).",
])
def test_capacity_claim_rejects_incomplete_or_misbound_equivalence(claim):
    question = "What minimum total payload capacity does the guide specify, in kilograms and grams?"
    source = "Eligible crates carry at least 3 kilograms (or 3,000 grams) of total payload capacity."
    focus, = _capacity_focus(question, source)
    assert _capacity_focus(question, source.replace("payload", "fuel")) == []
    assert _capacity_focus(question, source.replace("at least", "up to")) == []
    assert _capacity_focus(question, source.replace("grams)", "pounds)")) == []
    with pytest.raises(ValueError, match="minimum and both requested units"):
        validate_focused_claims([{"component_id": "r1", "text": claim}], {"r1": focus})
    validate_focused_claims(
        [{"component_id": "r1", "text": "The minimum total payload capacity is 3 kilograms (or 3,000 grams)."}],
        {"r1": focus},
    )


@pytest.mark.parametrize("claim", [
    "One terawatt is equivalent to 3,000,000,000 kilowatts.",
    "One megawatt is equivalent to 1,000,000,000 kilowatts.",
    "One terawatt is equivalent to 1,000,000,000 kilowatthours.",
    "One terawatt is equivalent to one billion kilowatts.",
])
def test_single_power_conversions_require_source_direction_and_exact_digits(claim):
    question = "How many kilowatts are equivalent to one terawatt in the guide?"
    quote = "Terawatts (TW): One TW is 1,000 GW, or 1,000,000,000 kW."
    focus, = _single_power_focus(question, quote)
    assert _single_power_focus(question, quote.replace("1,000,000,000 kW", "1,000,000,000 kWh")) == []
    assert _single_power_focus(question, quote.replace("Terawatts (TW)", "Megawatts (MW)")) == []
    assert focused_text(focus) == "One terawatt is equivalent to 1,000,000,000 kilowatts."
    validate_focused_claims([{"component_id": "r1", "text": focused_text(focus)}], {"r1": focus})
    with pytest.raises(ValueError, match="source base, digit value and requested unit"):
        validate_focused_claims([{"component_id": "r1", "text": claim}], {"r1": focus})


@pytest.mark.parametrize(("suffix", "valid"), [
    (" in the Thermal Grid Handbook.", True),
    (" in the EIA measurement guide.", False),
    (" in the Thermal Grid Handbook, with projected losses.", False),
])
def test_single_power_conversion_attribution_must_match_selected_record(suffix, valid):
    focus = {"kind": "single_power_conversion", "base": "terawatt",
             "value": "1,000,000,000", "target": "kilowatts"}
    claim = {"component_id": "r1", "text": focused_text(focus)[:-1] + suffix}
    source = {"title": "Thermal Grid Handbook", "url": "https://example.org/handbook"}
    if valid:
        validate_focused_claims([claim], {"r1": focus}, sources_by_component={"r1": source})
    else:
        with pytest.raises(ValueError, match="source base, digit value and requested unit"):
            validate_focused_claims([claim], {"r1": focus}, sources_by_component={"r1": source})


@pytest.mark.parametrize(("kind", "invalid"), [
    ("table", ""), ("aggregate", ""), ("table", "span"), ("table", "claim"), ("table", "omit"),
    ("table", "duplicate"), ("table", "forged"), ("table", "wrong_component"),
    ("ratio", ""), ("ratio", "claim"),
    *(("capacity", invalid) for invalid in ("", "span", "claim", "omit", "forged", "wrong_component")),
])
def test_scoped_request_focus_binds_exact_row_and_operand(tmp_path, kind, invalid):
    question, fact, expected = {
        "table": ("What were hydropower generation and its share of utility-scale generation in 2018?",
                  TABLE, "In 2018, the table gives Hydropower generation in Billion kWh as 119 and its share of total utility-scale electricity generation as 23.3%."),
        "aggregate": ("What were waste gases generation and its share of utility-scale generation in 2018?",
                      TABLE + "\nWaste gases (total)\n48\n9.4%\nLandfill gas\n19\n3.7%",
                      "In 2018, the table gives Waste gases (total) generation in Billion kWh as 48 and its share of total utility-scale electricity generation as 9.4%."),
        "ratio": ("What forms the denominator of the delivery rate?",
                  RATIO, "The denominator is all scheduled deliveries for the same week."),
        "capacity": ("What minimum total payload capacity does the guide specify, in kilograms and grams?",
                     "Eligible crates carry at least 3 kilograms (or 3,000 grams) of total payload capacity.",
                     "The minimum total payload capacity is 3 kilograms (or 3,000 grams)."),
    }[kind]
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([{"feed_id": "target", "clean_content": fact},
                                  {"feed_id": "distractor", "clean_content": question}]), encoding="utf-8")
    plan = Plan(query=question, corpus_sha256=hashlib.sha256(corpus.read_bytes()).hexdigest(),
                subtasks=(Subtask(subtask_id="s01", operation="retrieve", query=question),))
    bindings = {"r1": ["s01"]}
    scopes = DisclosureScopes.model_validate_json(json.dumps({
        "plan_id": plan.plan_id, "corpus_sha256": plan.corpus_sha256,
        "question_sha256": hashlib.sha256(question.encode()).hexdigest(),
        "bindings_sha256": bindings_hash(bindings), "declaration_ref": "Synthetic regression",
        "annotations": [{"component_id": "r1", "subtask_id": "s01",
                         "question_span": {"start": 0, "end": len(question)}}],
    }))
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(corpus))
    calls = []

    def fixed(stage, schema, instruction, inputs):
        calls.append(stage)
        if stage == "mapping":
            spans = {r["source_id"]: r["spans"][0]["span_id"] for r in inputs["evidence"]}
            assert inputs["request_focus"]["r1"]["span_id"] == spans["target"]
            parsed = {"wire_version": WIRE_VERSION, "components": [{"component_id": "r1",
                "status": "supported", "evidence": [spans["distractor" if invalid == "span" else "target"]]}],
                "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "No place."}}
            if kind == "capacity":
                from src.pilot.subtasks._fact_selection import SPAN_WIRE_VERSION
                parsed.pop("components")
                parsed.update(wire_version=SPAN_WIRE_VERSION, facts=[{"fact_id": "r1.1", "state": "supported",
                    "alternatives": [[{"span_id": spans["distractor" if invalid == "span" else "target"], "context": []}]]}])
        elif kind in {"table", "aggregate", "capacity"}:
            assert inputs["units"][0]["response_kind"] == ("capacity_threshold" if kind == "capacity" else "table_row")
            assert "request_focus" not in inputs
            selection = {"component_id": "r1", "unit_id": "u1"}
            claims = [selection]
            if invalid == "claim":
                claims = [{**selection, "text": expected}]
            elif invalid == "omit":
                claims = []
            elif invalid == "duplicate":
                claims = [selection, selection]
            elif invalid == "forged":
                claims = [{**selection, "unit_id": "u9"}]
            elif invalid == "wrong_component":
                claims = [{**selection, "component_id": "r2"}]
            parsed = {"title": "Analyst research brief", "claims": claims}
        else:
            assert inputs["request_focus"]["r1"]["claim_text"] == expected
            text = expected
            if invalid == "claim":
                text = text.replace("119", "62") if kind == "table" else "The numerator is completed deliveries."
            parsed = {"title": "Analyst research brief", "claims": [
                {"component_id": "r1", "unit_id": "u1", "text": text}]}
        return {"parsed": parsed}

    callback = ScopedConcurrentComposer(plan, bindings, "2026-11-12", fixed, scopes,
                                        complete_required_branches=bindings,
                                        fact_selection=kind == "capacity", whole_fact_spans=kind == "capacity")
    access = ModelAccess(time.monotonic() + 30)
    if invalid:
        with pytest.raises(ValueError):
            callback(report, access)
    else:
        result = callback(report, access)
        assert result.draft["claims"] == [{"text": expected, "source_ids": ["target"]}]
        assert result.diagnostics["fallback_unit_ids"] == []
        if kind in {"table", "aggregate", "capacity"}:
            assert result.diagnostics["raw_composer_output"]["claims"] == ({"component_id": "r1", "unit_id": "u1"},)
            key = ("application_rendered_capacity_thresholds" if kind == "capacity"
                   else "application_rendered_table_rows")
            rendered, = result.diagnostics[key]
            assert rendered["text"] == expected and rendered["source_id"] == "target"
            assert fact[rendered["start"]:rendered["end"]] == fact
    assert calls == (["mapping"] if invalid == "span" else ["mapping", "composition"])


@pytest.mark.parametrize(("text", "accepted"), [
    ("The denominator is all scheduled deliveries for the same week.", True),
    ("The denominator of the delivery rate is all scheduled deliveries for the same week.", True),
    ("The denominator of the completion rate is all scheduled deliveries for the same week.", False),
    ("The numerator of the delivery rate is all scheduled deliveries for the same week.", False),
    ("The denominator of the delivery rate is completed deliveries.", False),
    ("The denominator of the delivery rate is not all scheduled deliveries for the same week.", False),
    ("The denominator is all scheduled deliveries for the same week. Rates increased.", False),
])
def test_named_ratio_claim_preserves_requested_operand(text, accepted):
    focus = {"kind": "ratio_operand", "ratio": "The delivery rate", "role": "denominator",
             "operand": "all scheduled deliveries for the same week"}
    claims = [{"component_id": "r1", "text": text}]
    if accepted:
        validate_focused_claims(claims, {"r1": focus})
    else:
        with pytest.raises(ValueError, match="requested table row or ratio operand"):
            validate_focused_claims(claims, {"r1": focus})


def test_mixed_composition_requires_table_selection_and_preserves_prose_slot():
    mapping = EvidenceMap(components=[
        {"component_id": "r1", "question_anchor": "Hydropower generation", "status": "supported",
         "short_answer": "Table row", "evidence": [{"source_id": "target", "quote": TABLE}]},
        {"component_id": "r2", "question_anchor": "Delivery rate", "status": "supported",
         "short_answer": "Delivery rate", "evidence": [{"source_id": "ratio", "quote": RATIO}]},
    ])
    schema = table_composition_schema(mapping, {"u1": "r1"})
    table = {"unit_id": "u1", "component_id": "r1"}
    prose = {"unit_id": "u2", "component_id": "r2", "text": RATIO}
    for claims in ([table], [table, prose]):
        parsed = schema.model_validate({"title": "Analyst research brief", "claims": claims})
        assert parsed.model_dump(mode="json")["claims"] == claims
    for claims in ([prose], [prose, table], [table, {**prose, "text": None}]):
        with pytest.raises(ValueError):
            schema.model_validate({"title": "Analyst research brief", "claims": claims})


def test_mixed_composition_requires_conversion_fields_and_ordinary_table_ids():
    mapping = EvidenceMap(components=[
        {"component_id": cid, "question_anchor": "Request " + cid, "status": "supported",
         "short_answer": "Source answer", "evidence": [{"source_id": cid, "quote": quote}]}
        for cid, quote in (("r1", TABLE), ("r2", "One hour equals 60 minutes or 3,600 seconds."), ("r3", RATIO))
    ])
    schema = table_composition_schema(mapping, {"u1": "r1"}, {"u2": "r2"})
    table = {"unit_id": "u1", "component_id": "r1"}
    conversion = {"unit_id": "u2", "component_id": "r2", "targets": {
        "target_1": "One hour equals 60 minutes.", "target_2": "One hour equals 3,600 seconds."}}
    prose = {"unit_id": "u3", "component_id": "r3", "text": RATIO}
    for claims in ([table, conversion], [table, conversion, prose]):
        decoded = schema.model_validate({"title": "Analyst research brief", "claims": claims})
        assert decoded.model_dump(mode="json")["claims"] == claims
    for claims in ([table], [conversion], [table, conversion, conversion],
                   [table, {**conversion, "targets": {"target_1": conversion["targets"]["target_1"]}}]):
        with pytest.raises(ValueError):
            schema.model_validate({"title": "Analyst research brief", "claims": claims})


@pytest.mark.parametrize(("subject", "label"), [
    ("biofuel", "Biofuels (total)"),
    ("biofuels", "Biofuels (total)"),
    ("liquid biofuel", "Liquid biofuel"),
    ("solid biofuel", None),
    ("biofuel and coal", None),
    ("waste gases", "Waste gases (total)"),
    ("waste gases (total)", "Waste gases (total)"),
    ("waste gas", None),
    ("gases", None),
    ("landfill gas", "Landfill gas"),
    ("industrial gases", "Industrial gases (total)"),
    ("total - all sources", "Total - all sources"),
])
def test_aggregate_label_matching_keeps_child_rows_distinct(subject, label):
    table = ("Utility-scale electricity generation in 2018\nEnergy source\nBillion kWh\nShare of total\n"
             "Total - all sources\n500\n100%\nBiofuels (total)\n40\n8%\nLiquid biofuel\n12\n2.4%\n"
             "Waste gases (total)\n48\n9.6%\nLandfill gas\n19\n3.8%\nIndustrial gases (total)\n31\n6.2%")
    matches = _table_focus(f"What were {subject} generation and its share in 2018?", table)
    assert [match["label"] for match in matches] == ([label] if label else [])


def test_span_hints_rank_requested_capability_within_bound_retrieval():
    from types import SimpleNamespace as Record

    requests = [{"component_id": "r1", "question_anchor": "What can advanced thermostats adjust remotely?"}]
    catalog = {
        "intro": {"source_id": "manual", "text": "Thermostats control room temperature."},
        "exact": {"source_id": "manual", "text": "Advanced thermostats can remotely adjust temperature schedules."},
        "foreign": {"source_id": "other", "text": "Advanced thermostats remotely adjust commercial ventilation."},
    }
    report = Record(results=[
        Record(subtask_id="s01", outcome="evidence", sources=[Record(source_id="manual", role="support")]),
        Record(subtask_id="s02", outcome="evidence", sources=[Record(source_id="other", role="support")]),
    ])
    bindings = {"r1": ["s01"]}
    assert relevance_hints(requests, catalog, report, bindings, {}) == {"r1": ["exact"]}
    assert relevance_hints(requests, catalog, report, bindings, {"r1": {"span_id": "intro"}}) == {}


def test_dependent_question_hints_retain_prior_subject_within_current_branch():
    from types import SimpleNamespace as Record

    requests = [
        {"component_id": "r1", "question_anchor": "What did harbor couriers deliver weekly"},
        {"component_id": "r2", "question_anchor": "who received those deliveries?"},
    ]
    catalog = {
        "historical": {"source_id": "harbor", "text": "Harbor couriers delivered weekly cargo manifests to the port clerk."},
        "modern": {"source_id": "harbor", "text": "These deliveries are routed instantly."},
        "foreign": {"source_id": "other", "text": "Harbor couriers deliver weekly manifests to the customs office."},
    }
    report = Record(results=[
        Record(subtask_id="s01", outcome="evidence", sources=[Record(source_id="other", role="support")]),
        Record(subtask_id="s02", outcome="evidence", sources=[Record(source_id="harbor", role="support")]),
    ])
    hints = relevance_hints(requests, catalog, report, {"r1": ["s01"], "r2": ["s02"]}, {})
    assert hints == {"r1": ["foreign"], "r2": ["historical"]}


@pytest.mark.parametrize("text", ["These vans carried parcels.", " Those deliveries went to the port.", "Such pumps shut off."])
def test_concurrent_claim_cannot_start_with_dangling_demonstrative(text):
    with pytest.raises(ValueError, match="unresolved demonstrative subject"):
        _validate_explicit_subjects([{"text": text}])


def test_concurrent_claim_accepts_explicit_subject_and_subsequent_reference():
    _validate_explicit_subjects([{"text": "Harbor couriers delivered manifests. These went to the port clerk."}])


def test_scoped_composer_requests_direct_evidence_and_historical_modality(tmp_path):
    question = "What could the harbor transmitter send weekly?"
    evidence = "The harbor transmitter could send weekly cargo manifests."
    background = "The harbor office kept a separate record of tides."
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([{"feed_id": "harbor", "clean_content": f"{evidence} {background}"}]),
                      encoding="utf-8")
    plan = Plan(query=question, corpus_sha256=hashlib.sha256(corpus.read_bytes()).hexdigest(),
                subtasks=(Subtask(subtask_id="s01", operation="retrieve", query=question),))
    bindings = {"r1": ["s01"]}
    scopes = DisclosureScopes.model_validate_json(json.dumps({
        "plan_id": plan.plan_id, "corpus_sha256": plan.corpus_sha256,
        "question_sha256": hashlib.sha256(question.encode()).hexdigest(),
        "bindings_sha256": bindings_hash(bindings), "declaration_ref": "Synthetic regression",
        "annotations": [{"component_id": "r1", "subtask_id": "s01",
                         "question_span": {"start": 0, "end": len(question)}}],
    }))
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(corpus))
    stages = []

    def fixed(stage, schema, instruction, inputs):
        stages.append(stage)
        if stage == "mapping":
            assert "Exclude general background" in instruction
            spans = {span["text"]: span["span_id"] for span in inputs["evidence"][0]["spans"]}
            assert background in spans
            parsed = {"wire_version": WIRE_VERSION, "components": [
                {"component_id": "r1", "status": "supported", "evidence": [spans[evidence]]}],
                "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "No place."}}
        else:
            assert "Preserve the source's time and modality" in instruction
            unit, = inputs["units"]
            assert unit["evidence"] == [{"source_id": "harbor", "quote": evidence}]
            parsed = {"title": "Analyst research brief", "claims": [
                {"component_id": "r1", "unit_id": unit["unit_id"], "text": evidence}]}
        return {"parsed": schema.model_validate(parsed).model_dump()}

    composer = ScopedConcurrentComposer(plan, bindings, "2026-11-13", fixed, scopes)
    result = composer(report, ModelAccess(time.monotonic() + 30))
    assert stages == ["mapping", "composition"]
    assert result.draft["claims"] == [{"text": evidence, "source_ids": ["harbor"]}]
    assert result.diagnostics["fallback_unit_ids"] == []
