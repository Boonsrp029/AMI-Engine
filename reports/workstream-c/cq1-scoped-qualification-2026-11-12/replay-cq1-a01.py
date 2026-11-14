"""Replay the stopped CQ1 attempt using the retained response and no network."""
import hashlib
import json
from pathlib import Path
import socket
import time
import traceback

from pydantic import ValidationError


def blocked(*args, **kwargs):
    raise AssertionError("Network disabled during retained-response replay")


socket.socket.connect = blocked
socket.create_connection = blocked

from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan

root = Path(__file__).resolve().parent
contract = json.loads((root / "qualification-contract.json").read_bytes())
assert all(hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected
           for name, expected in contract["input_sha256"].items())
output = Path(contract["output_directory"])
case = contract["cases"]["cq1-a01"]
stored = json.loads((output / "cq1-a01.result.json").read_bytes())["stored_run"]
record = json.loads((output / "cq1-a01.mapping.raw.json").read_bytes())
raw = json.loads(record["raw"])
plan_event = next(event for event in stored["events"] if event["kind"] == "subtask_plan")
plan = Plan.model_validate_json(json.dumps(plan_event["payload"]["plan"]))
report = run_plan(plan, stored["id"], stored["metrics"]["attempt_id"], LocalBM25Adapter(case["corpus_path"]))
details = {"actual_model_calls": 0, "nemo_invocations": 0, "sockets_blocked": True, "stages": []}


def fixed(stage, schema, instruction, inputs):
    assert stage == "mapping"
    details["stages"].append(stage)
    selected = {sid for component in raw["components"] for sid in component["evidence"]}
    geography = set(raw["geography"]["evidence"])
    details["selected_evidence"] = [
        {"source_id": source.get("source_id"), "span": span,
         "component_evidence": span["span_id"] in selected,
         "geography_evidence": span["span_id"] in geography}
        for source in inputs["evidence"] for span in source["spans"]
        if span["span_id"] in selected | geography
    ]
    try:
        parsed = schema.model_validate(raw)
    except ValidationError as error:
        details["schema_errors"] = error.errors(include_input=False, include_url=False, include_context=False)
        parsed = None
    return {"parsed": parsed, "raw": record["raw"], "usage": record["usage"]}


callback = prepare_composer(contract, case, plan, fixed, None)
try:
    callback(report, ModelAccess(time.monotonic() + 30))
except Exception as error:
    details.update(reproduced_failure=True, error_type=type(error).__name__,
                   message=str(error), traceback=traceback.format_exc())
else:
    raise AssertionError("Expected retained failure")

with (root / "cq1-a01-offline-replay-with-evidence.json").open("x", encoding="utf-8") as stream:
    json.dump(details, stream, indent=2)
print(json.dumps({key: details.get(key) for key in ("message", "stages", "schema_errors", "selected_evidence")}, indent=2))
