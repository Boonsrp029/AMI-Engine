"""Replay the actual membership response and capture the exact offline rejection."""
import json
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

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


def main():
    socket.socket.connect = socket.create_connection = blocked
    contract = read(ROOT / "development-contract.json")
    assert all(digest(path) == sha for path, sha in contract["input_sha256"].items())
    case = contract["cases"]["cq1-a24"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    stages = []
    raw_paths = {stage: ROOT / "actual-development-v1" / f"cq1-a24.{stage}.raw.json"
                 for stage in ("mapping", "composition")}

    def fixed(stage, schema, instruction, inputs):
        stages.append(stage)
        raw = read(raw_paths[stage])["raw"]
        parsed = schema.model_validate_json(raw).model_dump()
        if stage == "composition":
            unit, = inputs["units"]
            claim, = parsed["claims"]
            assert claim["targets"] == unit["required_membership"]["targets"]
        return {"raw": raw, "parsed": parsed}

    try:
        prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
    except ValueError as error:
        assert str(error) == "Membership sentence must retain the requested category and complete source member"
        reason = str(error)
    else:
        raise AssertionError("The archived response unexpectedly passed")
    assert stages == ["mapping", "composition"]
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0, "stages": stages,
                      "both_required_phrases_exact": True, "rejection": reason,
                      "capture_sha256": {stage: digest(path) for stage, path in raw_paths.items()}}, indent=2))


if __name__ == "__main__":
    main()
