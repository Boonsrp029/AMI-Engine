"""Replay retained v6 responses offline; never invoke a model or safety client."""
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.generation import ConcurrentComposer
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "actual-development-v5"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SavedTransport:
    def __init__(self):
        self.inputs = {}

    def __call__(self, stage, schema, instruction, inputs):
        self.inputs[stage] = inputs
        saved = json.loads((OUTPUT / f"cq-p01.{stage}.raw.json").read_text())
        return {**saved, "parsed": json.loads(saved["raw"])}


def main():
    paths = list(OUTPUT.glob("*.json"))
    original = {p.name: sha(p) for p in paths}
    result = json.loads((OUTPUT / "cq-p01.result.json").read_text())
    stored = result["stored_run"]
    event = next(e for e in stored["events"] if e["kind"] == "subtask_plan")
    plan = Plan.model_validate_json(json.dumps(event["payload"]["plan"]))
    contract = json.loads((ROOT / "development-contract-v6.json").read_text())
    case = contract["cases"]["cq-p01"]
    report = run_plan(plan, stored["id"], stored["metrics"]["attempt_id"], LocalBM25Adapter(case["corpus_path"]))
    transport = SavedTransport()
    access = ModelAccess(time.monotonic()+30)
    try:
        ConcurrentComposer(plan, case["bindings"], contract["as_of"], transport,
            complete_required_branches=case["complete_required_branches"])(report, access)
    except ValueError as exc:
        failure = {"error_type":type(exc).__name__, "message":str(exc),
                   "traceback":traceback.format_exc()}
    else:
        raise AssertionError("Retained unsafe composition must fail")
    assert set(transport.inputs) == {"mapping", "composition"}
    assert all(sha(OUTPUT / name) == value for name, value in original.items())
    audit = {"live_model_calls":0, "fixed_responses_replayed":access.calls,
        "failure":failure, "composition_inputs":transport.inputs["composition"],
        "actual_json_sha256":original, "original_actual_files_unchanged":True,
        "regrading":False}
    with (ROOT / "v6-offline-replay.json").open("x", encoding="utf-8") as stream:
        json.dump(audit, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"live_model_calls":0, "fixed_responses_replayed":access.calls, "failure":failure["message"]}))


if __name__ == "__main__":
    main()
