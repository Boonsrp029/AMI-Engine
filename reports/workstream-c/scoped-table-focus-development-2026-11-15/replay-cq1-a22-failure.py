import hashlib
import json
from pathlib import Path
import socket
import time

from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan

def blocked(*args, **kwargs):
    raise AssertionError("Offline replay cannot open a socket")

socket.socket.connect = socket.create_connection = blocked
root = Path("reports/workstream-c/scoped-table-focus-development-2026-11-15")
contract = json.loads((root / "qualification-contract.json").read_bytes())
case = contract["cases"]["cq1-a22"]
plan = Plan.model_validate_json(json.dumps(case["plan"]))
assert digest(case["corpus_path"]) == plan.corpus_sha256
assert all(digest(name) == expected for name, expected in contract["input_sha256"].items())
report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
capture = root / "actual-cq1/cq1-a22.mapping.raw.json"
raw = json.loads(capture.read_bytes())["raw"]
selections = json.loads(raw)["facts"][0]["alternatives"][0]
ids = {entry["span_id"] for entry in selections}
details = {}

def fixed(stage, schema, instruction, inputs):
    assert stage == "mapping", "Unexpected composition after rejected mapping"
    focus = inputs.get("request_focus", {}).get("r1", {})
    details.update(selection=selections, expected_focus=focus, selected_spans=[
        {"source_id": source["source_id"], "span_id": span["span_id"], "text": span["text"]}
        for source in inputs["evidence"] for span in source["spans"]
        if span["span_id"] in ids or "megawatt" in span["text"].casefold()])
    return {"raw": raw, "parsed": schema.model_validate_json(raw).model_dump()}

try:
    prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic()+30))
except ValueError as error:
    print(json.dumps({"sockets_blocked": True, "actual_calls": 0, "capture_sha256": digest(capture),
                      "rejection": str(error), **details}, indent=2))
else:
    raise AssertionError("The retained mapping passed")


