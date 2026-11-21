"""Project the saved conversion case with fixed responses on the current runtime."""
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


def blocked(*args, **kwargs):
    raise AssertionError("Offline replay cannot open a socket")


def main():
    socket.socket.connect = socket.create_connection = blocked
    contract = json.loads((ROOT / "qualification-contract.json").read_bytes())
    case = contract["cases"]["cq1-a22"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    capture = ROOT / "actual-cq1/cq1-a22.mapping.raw.json"
    mapping = json.loads(json.loads(capture.read_bytes())["raw"])
    text = "One megawatt is equivalent to 1,000 kilowatts or 1,000,000 watts."
    stages = []

    def fixed(stage, schema, instruction, inputs):
        stages.append(stage)
        if stage == "mapping":
            focus = inputs["request_focus"]["r1"]
            assert focus == {"kind": "unit_conversion", "span_id": "s_d1ad042cf9ed1c0a"}
            sid = focus["span_id"]
            saved_groups = mapping["facts"][0]["alternatives"]
            invalid = [saved_groups, [[{"span_id": sid, "context": [sid]}]]]
            for groups in invalid:
                mapping["facts"][0]["alternatives"] = groups
                try:
                    schema.model_validate_json(json.dumps(mapping))
                except ValidationError:
                    continue
                raise AssertionError("Invalid saved/role selection parsed")
            mapping["facts"][0]["alternatives"] = [[{"span_id": sid, "context": []}]]
            response = mapping
        else:
            assert "request_focus" not in inputs
            assert all("response_kind" not in unit for unit in inputs["units"])
            unit, = inputs["units"]
            response = {"title": "Analyst research brief", "claims": [
                {"unit_id": unit["unit_id"], "component_id": unit["component_id"], "text": text}]}
        return {"parsed": schema.model_validate_json(json.dumps(response)).model_dump()}

    result = prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
    assert stages == ["mapping", "composition"]
    assert result.draft["claims"] == [{"text": text, "source_ids": ["eia-measurement"]}]
    assert not result.diagnostics["fallback_unit_ids"]
    print(json.dumps({"model_calls": 0, "sockets_blocked": True, "saved_invalid_selection_rejected": True,
                      "focused_self_context_rejected": True, "capture_sha256": digest(capture),
                      "draft_from_fixed_model_prose": result.draft}, indent=2))


if __name__ == "__main__":
    main()
