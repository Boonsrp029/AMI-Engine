"""Replay a rejected answer against the frozen modal composer with networking disabled."""
import json
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from run_case import inspect
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


def blocked(*args, **kwargs):
    raise AssertionError("Offline replay cannot open a socket")


def main():
    contract = inspect(ROOT, sys.argv[1])
    socket.socket.connect = socket.create_connection = blocked
    case = contract["cases"]["cq1-a20"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    assert not Path(contract["output_directory"]).exists()
    retained = ROOT.parent / "scoped-fact-span-development-2026-11-15/actual-development-v1"
    capture_paths = {stage: retained / f"cq1-a20.{stage}.raw.json" for stage in ("mapping", "composition")}
    captures = {stage: json.loads(path.read_bytes())["raw"] for stage, path in capture_paths.items()}
    observed = []

    def fixed(stage, schema, instruction, inputs):
        observed.append(stage)
        if stage == "composition":
            assert all(fact["required_source_modal"] == "could" for fact in inputs["units"][0]["selected_facts"])
            assert "clause stating the supported fact" in instruction
        raw = captures[stage]
        return {"raw": raw, "parsed": schema.model_validate_json(raw).model_dump()}

    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    compose = prepare_composer(contract, case, plan, fixed, None)
    try:
        compose(report, ModelAccess(time.monotonic() + 30))
    except ValueError as error:
        assert "capability qualifier" in str(error), str(error)
        rejection = str(error)
    else:
        raise AssertionError("The rejected composer response passed the v6 gate")
    assert observed == ["mapping", "composition"]
    assert not Path(contract["output_directory"]).exists()
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "sockets_blocked": True,
        "model_calls": 0, "retained_response_hashes": {stage: digest(path) for stage, path in capture_paths.items()},
        "fixed_stages": observed, "rejection": rejection, "actual_output_created": False}, indent=2))


if __name__ == "__main__":
    main()
