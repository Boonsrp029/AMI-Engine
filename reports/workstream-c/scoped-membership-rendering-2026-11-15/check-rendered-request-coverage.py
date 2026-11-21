"""Replay the consumed CQ1 cases against source-field rendering with fixed responses."""
import json
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from pydantic import ValidationError
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


def read(path):
    return json.loads(path.read_bytes())


def blocked(*args, **kwargs):
    raise AssertionError("Offline replay cannot open a socket")


def probe(contract, cid, expected_scope, expected):
    case = contract["cases"][cid]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    paths = {stage: ROOT / "actual-cq1" / f"{cid}.{stage}.raw.json" for stage in ("mapping", "composition")}
    saved = {stage: json.loads(read(path)["raw"]) for stage, path in paths.items()}
    rejected = []

    def fixed(stage, schema, instruction, inputs):
        value = saved[stage]
        try:
            schema.model_validate_json(json.dumps(value))
        except ValidationError:
            rejected.append(stage)
        if stage == "mapping":
            focus = inputs["request_focus"][expected_scope]
            for item in value["facts"]:
                if item["fact_id"] == expected_scope + ".1":
                    item["alternatives"] = [[{"span_id": focus["span_id"], "context": []}]]
        else:
            unit, = [item for item in inputs["units"] if "required_source_fields" in item]
            assert unit["component_id"] == expected_scope and len(unit["required_source_fields"]) == 2
            retained_prose = [claim for claim in value["claims"] if claim["component_id"] != expected_scope]
            value = {**value, "claims": [*retained_prose, {"unit_id": unit["unit_id"],
                     "component_id": unit["component_id"], "targets": unit["required_source_fields"]}]}
        return {"parsed": schema.model_validate_json(json.dumps(value)).model_dump()}

    result = prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
    assert "composition" in rejected
    if cid == "cq1-a10":
        assert "mapping" in rejected
    assert [claim["text"] for claim in result.draft["claims"]] == expected
    assert all(claim["source_ids"] == ["eia-measurement"] for claim in result.draft["claims"])
    assert not result.diagnostics["fallback_unit_ids"] and not result.diagnostics["editorial_correction"]
    rendered, = result.diagnostics["application_rendered_source_fields"]
    assert rendered["text"] == expected[-1]
    return {"saved_response_rejected_stages": rejected, "draft": result.draft, "application_rendering": rendered,
            "archived_captures_sha256": {k: digest(v) for k, v in paths.items()}}


def main():
    socket.socket.connect = socket.create_connection = blocked
    contract = read(ROOT / "qualification-contract.json")
    result = {
        "cq1-a26": probe(contract, "cq1-a26", "r1", [
            "Some advanced smart meters can even track the electricity use of individual devices and allow "
            "the utility or customer to control electricity use remotely."]),
        "cq1-a10": probe(contract, "cq1-a10", "r2", [
            "A watt measures power, while a watthour measures energy.",
            "For example, if you use a 40-Watt (0.04 kW) light bulb for five hours, "
            "you have used 200 Wh, or 0.2 kWh, of electrical energy."]),
    }
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0, "cases": result}, indent=2))


if __name__ == "__main__":
    main()
