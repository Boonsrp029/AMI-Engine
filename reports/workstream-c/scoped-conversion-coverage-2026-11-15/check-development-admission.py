"""Check the two consumed development cases using fixed JSON and no sockets."""
import json
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / "scoped-table-focus-development-2026-11-15"
OLDER = ROOT.parent / "scoped-fact-span-development-2026-11-15"
sys.path.insert(0, str(OLDER))

from check_and_freeze import blocked, digest, encoding, read
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


def main():
    socket.socket.connect = socket.create_connection = blocked
    contract = read(PRIOR / "qualification-contract.json")
    tokenizer = Path(contract["tokenizer_path"])
    assert digest(tokenizer) == contract["tokenizer_sha256"]
    counter = encoding(read(tokenizer))
    result = {}
    for cid in ("cq1-a22", "cq1-a21"):
        case = contract["cases"][cid]
        plan = Plan.model_validate_json(json.dumps(case["plan"]))
        assert digest(case["corpus_path"]) == plan.corpus_sha256
        report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
        requests = {}

        def fixed(stage, schema, instruction, inputs):
            reserved = len(counter.encode(instruction)) + len(counter.encode(
                json.dumps(inputs, ensure_ascii=False, separators=(",", ":")))) + 1156
            assert reserved <= 4096
            requests[stage] = {"reserved": reserved, "format_schema_tokens":
                               len(counter.encode(json.dumps(schema.model_json_schema())))}
            if cid == "cq1-a22" and stage == "composition":
                unit, = inputs["units"]
                value = {"title": "Analyst research brief", "claims": [
                    {"unit_id": unit["unit_id"], "component_id": unit["component_id"],
                     "text": "One megawatt is equivalent to 1,000 kilowatts or 1,000,000 watts."}]}
            else:
                value = json.loads(read(PRIOR / "actual-cq1" / f"{cid}.{stage}.raw.json")["raw"])
                if cid == "cq1-a22":
                    sid = inputs["request_focus"]["r1"]["span_id"]
                    value["facts"][0]["alternatives"] = [[{"span_id": sid, "context": []}]]
            return {"parsed": schema.model_validate_json(json.dumps(value)).model_dump()}

        draft = prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
        assert len(draft.draft["claims"]) == 1 and not draft.diagnostics["fallback_unit_ids"]
        assert set(requests) == {"mapping", "composition"}
        result[cid] = {"requests": requests, "fixed_response_projection": draft.draft}
    print(json.dumps({"generation": 0, "sockets_blocked": True, "cases": result}, indent=2))


if __name__ == "__main__":
    main()
