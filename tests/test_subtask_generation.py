"""Fixed transport tests; never create a model client."""
import hashlib
import json
import time
import pytest

from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.generation import ConcurrentComposer
from src.pilot.subtasks._question_spans import QUESTION_WIRE_VERSION


class FixedTransport:
    def __init__(self, malformed=False, mode="supported"):
        self.stages = []
        self.malformed = malformed
        self.mode = mode

    def __call__(self, stage, schema, instruction, inputs):
        self.stages.append(stage)
        if self.malformed:
            return {"parsed": None, "raw": "invalid wire"}
        if stage == "mapping":
            request = inputs["requests"][0]
            spans = [s["span_id"] for r in inputs["evidence"] for s in r["spans"]]
            parsed = {"wire_version": QUESTION_WIRE_VERSION, "components": [{
                "component_id": request["component_id"], "status": "supported",
                "evidence": spans, "gap": None}], "geography": {
                "status": "unresolved", "value": "", "evidence": [], "reason": "Not established."}}
            if self.mode == "missing":
                parsed["components"][0].update(status="missing", evidence=[], gap=None)
            if self.mode == "invalid_span":
                parsed["components"][0]["evidence"] = ["not-an-existing-span"]
        else:
            parsed = {"title": "Analyst research brief", "claims": [{
                "component_id": u["component_id"], "unit_id": u["unit_id"],
                "text": u["evidence"][0]["quote"]} for u in inputs["units"]]}
        return {"parsed": parsed, "raw": json.dumps(parsed), "usage": None}


def fixture(tmp_path):
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps([{"feed_id": "observed", "clean_content":
        "Observed electricity demand grew 7.3% in 2014."}]), encoding="utf-8")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    plan = Plan(query="What was observed electricity demand growth in 2014?", corpus_sha256=sha,
        subtasks=(Subtask(subtask_id="s01", operation="retrieve", query="observed"),))
    report = run_plan(plan, "a"*32, "b"*32, LocalBM25Adapter(path))
    return plan, report


def test_fixed_transport_uses_budget_and_preserves_selection_trace(tmp_path):
    plan, report = fixture(tmp_path)
    transport = FixedTransport()
    access = ModelAccess(time.monotonic()+30)
    result = ConcurrentComposer(plan, {"r1": ("s01",)}, "2026-11-06", transport)(report, access)
    assert transport.stages == ["mapping", "composition"]
    assert access.calls == 2 and access.guards == 0 and not result.safety_passed
    assert result.diagnostics["span_catalog"] and result.diagnostics["application_extracts"]
    assert result.provenance[0]["origins"][0]["subtask_id"] == "s01"


def test_malformed_response_stops_without_repair_or_composer(tmp_path):
    plan, report = fixture(tmp_path)
    transport = FixedTransport(malformed=True)
    access = ModelAccess(time.monotonic()+30)
    with pytest.raises(ValueError, match="did not parse"):
        ConcurrentComposer(plan, {"r1": ("s01",)}, "2026-11-06", transport)(report, access)
    assert transport.stages == ["mapping"] and access.calls == 1 and access.guards == 0


def test_all_missing_skips_composition_and_leaves_safety_pending(tmp_path):
    plan, report = fixture(tmp_path)
    transport = FixedTransport(mode="missing")
    access = ModelAccess(time.monotonic()+30)
    result = ConcurrentComposer(plan, {"r1": ("s01",)}, "2026-11-06", transport)(report, access)
    assert result.draft["claims"] == [] and result.provenance == ()
    assert transport.stages == ["mapping"] and access.calls == 1 and access.guards == 0


def test_invalid_span_does_not_repair_or_compose(tmp_path):
    plan, report = fixture(tmp_path)
    transport = FixedTransport(mode="invalid_span")
    access = ModelAccess(time.monotonic()+30)
    with pytest.raises(ValueError):
        ConcurrentComposer(plan, {"r1": ("s01",)}, "2026-11-06", transport)(report, access)
    assert transport.stages == ["mapping"] and access.calls == 1


@pytest.mark.parametrize("mode", ["expired", "budget", "bindings"])
def test_admission_checks_do_not_reach_transport(tmp_path, mode):
    plan, report = fixture(tmp_path)
    transport = FixedTransport()
    access = ModelAccess(time.monotonic() + (-1 if mode == "expired" else 30))
    if mode == "budget":
        access.calls = 4
    bindings = {"r1": ("s05",)} if mode == "bindings" else {"r1": ("s01",)}
    with pytest.raises((ValueError, TimeoutError, RuntimeError)):
        ConcurrentComposer(plan, bindings, "2026-11-06", transport)(report, access)
    assert transport.stages == []


def test_supported_gap_rule_is_present_in_decoder_json_schema(tmp_path):
    from src.pilot._evidence import build_span_catalog
    from src.pilot.subtasks.generation import selection_schema
    plan, report = fixture(tmp_path)
    catalog = build_span_catalog({r.source.source_id:r.source.model_dump() for r in report.sources})
    schema = selection_schema(catalog, plan.query).model_json_schema()
    supported = schema["$defs"]["SupportedRequestSlot0"]["properties"]
    assert supported["gap"]["const"] is None
    assert supported["component_id"]["const"] == "r1"
    assert supported["kind"]["const"] == "unknown"
    assert supported["evidence"]["minItems"] == 1


@pytest.mark.parametrize("damage", ["gap", "request", "span", "missing"])
def test_invalid_state_or_identity_stops_before_composition(tmp_path, damage):
    class DamagedTransport(FixedTransport):
        def __call__(self, stage, schema, instruction, inputs):
            response = super().__call__(stage, schema, instruction, inputs)
            if stage == "mapping":
                c = response["parsed"]["components"][0]
                if damage == "gap":c["gap"] = {"start":0,"end":len(inputs["question"])+1}
                elif damage == "request":c["component_id"] = "r999"
                elif damage == "span":c["evidence"] = ["unknown-span"]
                else:c.update(status="missing", gap=None)
            return response
    plan, report = fixture(tmp_path)
    transport = DamagedTransport()
    access = ModelAccess(time.monotonic()+30)
    with pytest.raises(ValueError):
        ConcurrentComposer(plan, {"r1": ("s01",)}, "2026-11-06", transport)(report, access)
    assert transport.stages == ["mapping"] and access.calls == 1 and access.guards == 0
