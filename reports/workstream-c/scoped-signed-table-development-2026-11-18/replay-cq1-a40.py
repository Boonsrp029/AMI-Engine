"""Reproduce a retained self-context selection with sockets blocked."""
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
    raise AssertionError("Offline replay cannot open sockets")


def main():
    socket.socket.connect = socket.create_connection = blocked
    contract = read(ROOT / "qualification-contract.json")
    assert all(digest(path) == sha for path, sha in contract["input_sha256"].items())
    case = contract["cases"]["cq1-a40"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    capture = ROOT / "actual-cq1/cq1-a40.mapping.raw.json"
    raw = read(capture)["raw"]
    details = {}

    def fixed(stage, schema, instruction, inputs):
        assert stage == "mapping"
        value = schema.model_validate_json(raw).model_dump()
        part = value["facts"][0]["alternatives"][0][0]
        spans = {span["span_id"]: {**span, "source_id": record["source_id"]}
                 for record in inputs["evidence"] for span in record["spans"]}
        details.update(schema_valid=True, direct_span_id=part["span_id"], context_span_ids=part["context"],
                       selected_spans=[spans[sid] for sid in dict.fromkeys([part["span_id"], *part["context"]])])
        assert part["span_id"] in part["context"]
        return {"raw": raw, "parsed": value}

    try:
        prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
    except ValueError as error:
        assert str(error) == "Duplicate fact evidence role"
        rejection = str(error)
    else:
        raise AssertionError("Retained invalid mapping unexpectedly passed")
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0, "nemo_invocations": 0,
        "capture_sha256": digest(capture), "rejection": rejection, **details,
        "diagnosis": "Generic same-record schema allows a selected direct span in its own context list. "
            "The resolver prohibits that duplicate role. The selected direct quote contains the requested "
            "one-megawatt/1000-kilowatt minimum definition. Composition never ran."}, indent=2))


if __name__ == "__main__":
    main()
