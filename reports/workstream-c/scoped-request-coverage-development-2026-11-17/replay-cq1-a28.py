"""Reproduce the failed geothermal selection without calling a model."""
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
    contract = read(ROOT / "qualification-contract.json")
    assert all(digest(path) == expected for path, expected in contract["input_sha256"].items())
    case = contract["cases"]["cq1-a28"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    capture = ROOT / "actual-cq1/cq1-a28.mapping.raw.json"
    raw = read(capture)["raw"]
    details = {}

    def fixed(stage, schema, instruction, inputs):
        assert stage == "mapping"
        value = schema.model_validate_json(raw).model_dump()
        parts = value["facts"][0]["alternatives"][0]
        ids = [item["span_id"] for item in parts]
        right = ids[0]
        rows = [{"source_id": source["source_id"], "span_id": span["span_id"], "text": span["text"]}
                for source in inputs["evidence"] for span in source["spans"]
                if span["span_id"] == right or span["text"].rstrip().endswith("Geothermal")]
        details.update(saved_response_schema_valid=True, selected_direct_ids=ids,
                       deterministic_focus=inputs.get("request_focus", {}).get("r1"), related_spans=rows)
        return {"raw": raw, "parsed": value}

    try:
        prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
    except ValueError as error:
        assert str(error) == "Duplicate fact evidence role"
        reason = str(error)
    else:
        raise AssertionError("Saved response passed")
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0, "rejection": reason,
                      "capture_sha256": digest(capture), **details}, indent=2))


if __name__ == "__main__":
    main()
