"""Replay capacity and table cases with all outbound sockets blocked."""
import hashlib
import json
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent
PRIOR = ROOT.parent / "scoped-context-role-development-2026-11-18"
sys.path.insert(0, str(ROOT.parents[2]))

from scripts._llama_token_count import encoding
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


def read(path):
    return json.loads(Path(path).read_bytes())


def blocked(*args, **kwargs):
    raise AssertionError("Replay cannot open sockets")


def main():
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = blocked
    contract = read(PRIOR / "development-contract.json")
    output = PRIOR / "actual-development-v1"
    cid = "cq1-a40"
    frozen = contract["cases"][cid]
    assessment = read(output / f"{cid}.assessment.json")
    assert assessment["verdict"] == "fail"
    assert hashlib.sha256((output / f"{cid}.result.json").read_bytes()).hexdigest() == assessment["result_sha256"]
    plan = Plan.model_validate_json(json.dumps(frozen["plan"]))
    assert hashlib.sha256(Path(frozen["corpus_path"]).read_bytes()).hexdigest() == plan.corpus_sha256
    tokenizer = Path(contract["tokenizer_path"])
    assert hashlib.sha256(tokenizer.read_bytes()).hexdigest() == contract["tokenizer_sha256"]
    counter = encoding(read(tokenizer))
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(frozen["corpus_path"]))
    metrics = {}
    replays = {}
    for mode in ("retained_mapping", "retained_composition", "complete_fixed_response"):
        def fixed(stage, schema, instruction, inputs):
            raw = json.loads(read(output / f"{cid}.{stage}.raw.json")["raw"])
            compact_inputs = json.dumps(inputs, ensure_ascii=False, separators=(",", ":"))
            reserved = len(counter.encode(instruction)) + len(counter.encode(compact_inputs)) + 1156
            assert reserved <= 4096
            metrics[stage] = reserved
            if stage == "mapping" and mode != "retained_mapping":
                raw["facts"][0]["alternatives"][0][0]["context"] = []
            if stage == "composition" and mode == "complete_fixed_response":
                raw["claims"][0]["text"] = inputs["request_focus"]["r1"]["claim_text"]
            return {"parsed": schema.model_validate_json(json.dumps(raw)).model_dump()}

        try:
            result = prepare_composer(contract, frozen, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
        except ValueError as error:
            assert mode != "complete_fixed_response"
            if mode == "retained_composition":
                assert "minimum and both requested units" in str(error)
            else:
                assert "context" in str(error)
            replays[mode] = "rejected"
        else:
            assert mode == "complete_fixed_response"
            assert not result.diagnostics["fallback_unit_ids"]
            replays[mode] = result.draft["claims"]
    cid = "cq1-a39"
    frozen = contract["cases"][cid]
    plan = Plan.model_validate_json(json.dumps(frozen["plan"]))
    assert hashlib.sha256(Path(frozen["corpus_path"]).read_bytes()).hexdigest() == plan.corpus_sha256
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(frozen["corpus_path"]))
    table_output = ROOT.parent / "scoped-signed-table-development-2026-11-18" / "actual-cq1"

    def table_fixed(stage, schema, instruction, inputs):
        raw = read(table_output / f"{cid}.{stage}.raw.json")["raw"]
        compact_inputs = json.dumps(inputs, ensure_ascii=False, separators=(",", ":"))
        reserved = len(counter.encode(instruction)) + len(counter.encode(compact_inputs)) + 1156
        assert reserved <= 4096
        metrics[f"table_{stage}"] = reserved
        return {"parsed": schema.model_validate_json(raw).model_dump()}

    result = prepare_composer(contract, frozen, plan, table_fixed, None)(report, ModelAccess(time.monotonic() + 30))
    assert result.diagnostics["application_rendered_table_rows"] and not result.diagnostics["fallback_unit_ids"]
    assert result.draft["claims"] == read(table_output / f"{cid}.result.json")["stored_run"]["draft"]["claims"]
    replays["retained_table"] = result.draft["claims"]
    print(json.dumps({"actual_model_calls": 0, "sockets_blocked": True, "replays": replays,
                      "reserved_tokens": metrics, "retained_result_sha256": assessment["result_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
