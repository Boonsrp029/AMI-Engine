"""Count current scoped mapping request tokens without sending any requests."""
import json
from pathlib import Path
import socket
import time

from scripts._llama_token_count import encoding
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


class RequestCaptured(Exception):
    pass


def blocked(*args, **kwargs):
    raise AssertionError("Network disabled during request inspection")


def main():
    socket.socket.connect = blocked
    socket.create_connection = blocked
    root = Path(__file__).resolve().parent
    contract = json.loads((root / "qualification-contract.json").read_bytes())
    tokenizer = encoding(json.loads(Path(contract["tokenizer_path"]).read_bytes()))
    rows = []

    def count_request(stage, schema, instruction, inputs):
        assert stage == "mapping"
        content_tokens = len(tokenizer.encode(instruction)) + len(tokenizer.encode(
            json.dumps(inputs, ensure_ascii=False, separators=(",", ":"))))
        rows.append({
            "case_id": case_id,
            "content_tokens": content_tokens,
            "framing_reserved": 256,
            "completion_reserved": 900,
            "total_reserved": content_tokens + 256 + 900,
            "format_schema_tokens": len(tokenizer.encode(json.dumps(schema.model_json_schema()))),
        })
        raise RequestCaptured

    for case_id in contract["case_ids"]:
        case = contract["cases"][case_id]
        plan = Plan.model_validate_json(json.dumps(case["plan"]))
        report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
        callback = prepare_composer(contract, case, plan, count_request, None)
        try:
            callback(report, ModelAccess(time.monotonic() + 30))
        except RequestCaptured:
            continue
        raise AssertionError(f"Expected one mapping request for {case_id}")

    result = {"cases": rows, "limit": 4096, "all_fit": all(row["total_reserved"] <= 4096 for row in rows),
              "actual_calls": 0, "sockets_blocked": True}
    with (root / "mapping-context-check.json").open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
    print(json.dumps({"cases": len(rows), "all_fit": result["all_fit"],
                      "max_total_reserved": max(row["total_reserved"] for row in rows)}))
    return 0 if result["all_fit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
