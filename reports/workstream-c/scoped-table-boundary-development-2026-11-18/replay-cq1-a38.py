"""Reproduce the stopped actual response using fixed captures and blocked sockets."""
import json
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks._request_focus import _table_focus
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
    assert all(digest(path) == expected for path, expected in contract["input_sha256"].items())
    cid = "cq1-a38"
    case = contract["cases"][cid]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    stages = {}

    def fixed(stage, schema, instruction, inputs):
        path = ROOT / "actual-cq1" / f"{cid}.{stage}.raw.json"
        raw = read(path)["raw"]
        value = schema.model_validate_json(raw).model_dump()
        stages[stage] = {"capture_sha256": digest(path), "schema_valid": True}
        if stage == "mapping":
            part = value["facts"][0]["alternatives"][0][0]
            span, = [span for source in inputs["evidence"] for span in source["spans"]
                     if span["span_id"] == part["span_id"]]
            stages[stage].update(focus=inputs.get("request_focus", {}).get("r1"), selected_span=span)
        else:
            stages[stage]["raw_claims"] = value["claims"]
        return {"raw": raw, "parsed": value}

    try:
        prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
    except ValueError as error:
        failure = str(error)
    else:
        raise AssertionError("The retained response unexpectedly passed")
    sources = {row["feed_id"]: row for row in read(Path(case["corpus_path"]))}
    source = sources["eia-generation-2023"]
    tail = "Pumped storage hydropower\n4\n-6\n-0.1%\nOther sources\n5\n10\n0.2%"
    assert tail in source["clean_content"]
    start = source["clean_content"].index(tail)
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0, "nemo_calls": 0,
        "rejection": failure, "stages": stages, "full_source_focus": _table_focus(plan.query, source["clean_content"]),
        "source_id": "eia-generation-2023", "source_url": source["url"],
        "table_tail": {"quote": tail, "start": start, "end": start + len(tail)},
        "diagnosis": "The positive-only table parser stops at the preceding negative pumped-storage row. "
            "No complete focus is offered for Other sources. The mapper selected a fragment without year/header. "
            "The raw composer answered a different row and mixed a footnote marker with another row's share."}, indent=2))


if __name__ == "__main__":
    main()
