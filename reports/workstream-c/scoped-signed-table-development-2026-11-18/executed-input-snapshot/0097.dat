"""Replay consumed table facts with fixed responses and blocked sockets."""
import json
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from scripts._llama_token_count import encoding
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
    previous = ROOT.parent / "scoped-request-coverage-development-2026-11-17"
    contract = {**read(previous / "qualification-contract.json"), "as_of": "2026-11-18"}
    counter = encoding(read(Path(contract["tokenizer_path"])))
    assert digest(contract["tokenizer_path"]) == contract["tokenizer_sha256"]
    results = {}
    for cid in ("cq1-a28", "cq1-a27"):
        case = contract["cases"][cid]
        plan = Plan.model_validate_json(json.dumps(case["plan"]))
        assert digest(case["corpus_path"]) == plan.corpus_sha256
        report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
        retained_path = previous / "actual-cq1" / f"{cid}.mapping.raw.json"
        retained = json.loads(read(retained_path)["raw"])
        stages = {}

        def fixed(stage, schema, instruction, inputs):
            reserved = len(counter.encode(instruction)) + len(counter.encode(
                json.dumps(inputs, ensure_ascii=False, separators=(",", ":")))) + 1156
            assert reserved <= 4096, (stage, reserved)
            stages[stage] = {"reserved_tokens": reserved}
            if stage == "mapping":
                try:
                    schema.model_validate_json(json.dumps(retained))
                    old_valid = True
                except ValueError:
                    old_valid = False
                focus = inputs["request_focus"]["r1"]
                assert focus["label"] == ("Geothermal" if cid == "cq1-a28" else "Municipal solid waste (biogenic)")
                value = {**retained, "facts": [{**retained["facts"][0],
                    "alternatives": [[{"span_id": focus["span_id"], "context": []}]]}]}
                span, = [span for record in inputs["evidence"] for span in record["spans"]
                         if span["span_id"] == focus["span_id"]]
                stages[stage].update(saved_response_schema_valid=old_valid, focus=focus, selected_span=span)
            else:
                value = {"title": "Analyst research brief", "claims": [{"unit_id": "u1", "component_id": "r1"}]}
            return {"parsed": schema.model_validate_json(json.dumps(value)).model_dump()}

        result = prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
        text = result.draft["claims"][0]["text"]
        assert ("16" in text and "0.4%" in text) if cid == "cq1-a28" else ("6" in text and "0.1%" in text)
        results[cid] = {"fixed_response_only": True, "retained_capture_sha256": digest(retained_path),
                        "stages": stages, "draft": result.draft}
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0, "nemo_calls": 0,
                      "owner_accepted": False, "cases": results}, indent=2))


if __name__ == "__main__":
    main()
