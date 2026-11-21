"""Replay the actual incomplete response against the updated runtime offline."""
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


def blocked(*args, **kwargs):
    raise AssertionError("Offline replay cannot open a socket")


def main():
    socket.socket.connect = socket.create_connection = blocked
    contract = json.loads((ROOT / "development-contract.json").read_bytes())
    case = contract["cases"]["cq1-a22"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    raw_dir = ROOT / "actual-development-v1"
    capture = {stage: raw_dir / f"cq1-a22.{stage}.raw.json" for stage in ("mapping", "composition")}
    saved = {stage: json.loads(json.loads(path.read_bytes())["raw"]) for stage, path in capture.items()}

    def project(replacement=None):
        def fixed(stage, schema, instruction, inputs):
            value = saved[stage]
            if stage == "composition":
                unit, = inputs["units"]
                assert unit["required_conversion"] == {"base_unit": "mw", "targets": {"kw": "1000", "w": "1000000"}}
                assert "Do not omit either target" in instruction
                if replacement:
                    value = {**value, "claims": [{**value["claims"][0], "text": replacement}]}
            return {"parsed": schema.model_validate_json(json.dumps(value)).model_dump()}

        return prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))

    try:
        project()
    except ValueError as error:
        assert "both value-unit pairs" in str(error)
    else:
        raise AssertionError("Saved incomplete draft passed")
    complete = "One megawatt is equivalent to 1,000 kilowatts or 1,000,000 watts."
    result = project(complete)
    assert result.draft["claims"] == [{"text": complete, "source_ids": ["eia-measurement"]}]
    assert not result.diagnostics["fallback_unit_ids"]
    print(json.dumps({"actual_model_calls": 0, "sockets_blocked": True,
                      "saved_incomplete_rejected": True, "capture_sha256": {k: digest(v) for k, v in capture.items()},
                      "complete_fixed_prose_projected": result.draft}, indent=2))


if __name__ == "__main__":
    main()
