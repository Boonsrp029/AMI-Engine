"""Offline comparison of whole-span IDs and the existing phrase-retention gate."""
import json
from pathlib import Path
import socket
import time
from unittest.mock import patch

from src.pilot.subtasks import _fact_selection
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


ROOT = Path(__file__).resolve().parent


def blocked(*args, **kwargs):
    raise AssertionError("Network disabled")


def main():
    socket.socket.connect = socket.create_connection = blocked
    old = ROOT.parent / "scoped-fact-selection-development-2026-11-14"
    contract = json.loads((old / "development-contract.json").read_bytes())
    case = contract["cases"]["cq1-a20"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    outcomes = {}
    for name, claim in {
        "paraphrase": "Earlier automated electricity meters could periodically report electricity use to the utility.",
        "present_tense": "Automated electricity meters periodically report electricity use to the utility.",
    }.items():
        captured = {}

        def fixed(stage, schema, instruction, inputs):
            if stage == "mapping":
                spans = {item["span_id"]: item["text"]
                         for source in inputs["evidence"] for item in source["spans"]}
                span_id = "s_6af27ac482a98ade"
                part = {"span_id": span_id, "start": 0, "end": len(spans[span_id]), "context": []}
                value = {"wire_version": _fact_selection.WIRE_VERSION, "facts": [
                    {"fact_id": slot["fact_id"], "state": "supported", "alternatives": [[part]]}
                    for slot in inputs["facts"]],
                    "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "No geography requested."}}
            else:
                unit, = inputs["units"]
                value = {"title": "Analyst research brief", "claims": [
                    {"unit_id": unit["unit_id"], "component_id": unit["component_id"], "text": claim}]}
            return {"parsed": schema.model_validate(value).model_dump()}

        original = _fact_selection.check_fact_claims

        def observe(result, facts, rows):
            captured["draft_before_fact_gate"] = result.draft
            captured["source_contains_could"] = all(
                "could" in fact["alternatives"][0][0]["quote"] for fact in facts)
            original(result, facts, rows)

        try:
            with patch.object(_fact_selection, "check_fact_claims", observe):
                prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
        except ValueError as error:
            captured["fact_gate_error"] = str(error)
        else:
            raise AssertionError("Expected the existing phrase-retention gate to reject whole-span input")
        assert captured["draft_before_fact_gate"]["claims"][0]["text"] == claim
        assert captured["fact_gate_error"] == "Projected claim loses a selected fact literal or capability qualifier"
        outcomes[name] = captured
    print(json.dumps({"actual_model_calls": 0, "sockets_blocked": True, "runtime_changed": False,
                      "whole_span_emulation": outcomes}, indent=2))


if __name__ == "__main__":
    main()
