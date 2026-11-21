"""Compare mapper request and schema sizes with archived code and blocked sockets."""
import json
from pathlib import Path
import socket
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
PRIOR = ROOT.parent / "scoped-signed-table-development-2026-11-18"
sys.path.insert(0, str(PROJECT))
from scripts._llama_token_count import encoding
from src.pilot.subtasks import _fact_selection as facts
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


def read(path):
    return json.loads(Path(path).read_bytes())


def blocked(*args, **kwargs):
    raise AssertionError("Offline replay cannot open sockets")


class MappingCaptured(Exception):
    pass


def probe(contract, cid, counter, *, fixed_response=False):
    case = contract["cases"][cid]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    stages = {}

    def fixed(stage, schema, instruction, inputs):
        compact = lambda value: json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        shape = compact(schema.model_json_schema())
        reservation = len(counter.encode(instruction)) + len(counter.encode(compact(inputs))) + 1156
        assert reservation <= 4096
        stages[stage] = {"reserved": reservation, "schema_bytes": len(shape.encode()),
                         "schema_tokens": len(counter.encode(shape))}
        if not fixed_response:
            assert stage == "mapping"
            raise MappingCaptured
        if stage == "mapping":
            capture = PRIOR / "actual-cq1" / f"{cid}.mapping.raw.json"
            raw = read(capture)["raw"]
            try:
                schema.model_validate_json(raw)
            except ValueError:
                assert cid == "cq1-a40"
            else:
                assert cid == "cq1-a39"
            value = json.loads(raw)
            if cid == "cq1-a40":
                value["facts"][0]["alternatives"][0][0]["context"] = []
        else:
            unit, = inputs["units"]
            claim = {key: unit[key] for key in ("unit_id", "component_id")}
            if cid == "cq1-a40":
                claim["text"] = "EIA defines utility-scale generation as generation from power plants with at least one megawatt (1,000 kilowatts) of total generating capacity."
            value = {"title": "Analyst research brief", "claims": [claim]}
        return {"parsed": schema.model_validate_json(json.dumps(value)).model_dump()}

    try:
        result = prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
    except MappingCaptured:
        return stages["mapping"]
    assert result.draft["claims"] and not result.diagnostics["fallback_unit_ids"]
    return {"stages": stages, "fixed_response_draft": result.draft}


def main():
    socket.socket.connect = socket.create_connection = blocked
    contract = read(PRIOR / "qualification-contract.json")
    archive = PRIOR / "executed-input-snapshot"
    index = read(archive / "manifest.json")["files"]
    assert len(index) == len(contract["input_sha256"])
    assert all(digest(archive / item["file"]) == item["sha256"] for item in index.values())
    changed = [path for path, sha in contract["input_sha256"].items() if digest(path) != sha]
    assert changed == [str(PROJECT / "src/pilot/subtasks/_fact_selection.py")]
    old_file = archive / index[changed[0]]["file"]
    old = {"__name__": "src.pilot.subtasks._fact_selection_archived", "__package__": "src.pilot.subtasks"}
    exec(compile(old_file.read_bytes(), str(old_file), "exec"), old)
    tokenizer = Path(contract["tokenizer_path"])
    assert digest(tokenizer) == contract["tokenizer_sha256"]
    counter = encoding(read(tokenizer))
    with patch.object(facts, "_same_record_choices", old["_same_record_choices"]), \
         patch.object(facts, "SPAN_INSTRUCTION", old["SPAN_INSTRUCTION"]):
        before = {cid: probe(contract, cid, counter) for cid in contract["case_ids"]}
    after = {cid: probe(contract, cid, counter) for cid in contract["case_ids"]}
    replays = {cid: probe(contract, cid, counter, fixed_response=True) for cid in ("cq1-a40", "cq1-a39")}
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0,
        "verified_archived_inputs": len(index), "changed_runtime_inputs": changed,
        "before": before, "after": after, "fixed_responses": replays}, indent=2))


if __name__ == "__main__":
    main()
