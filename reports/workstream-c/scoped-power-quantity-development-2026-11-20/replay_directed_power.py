"""Replay archived model outputs through the current directed-conversion gate."""
import hashlib
import json
from pathlib import Path
import socket
import time

from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification_runner import _safety_excerpt
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_bytes())


def blocked(*args, **kwargs):
    raise AssertionError("No sockets in replay")


def main():
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = blocked
    contract = read(ROOT / "development-contract.json")
    case = contract["cases"]["cq1-a29"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    source_records = {entry.source.source_id: entry.source.model_dump() for entry in report.sources}
    prior = read(ROOT / "offline-safety-boundary.json")
    negative = read(ROOT / "evidence-first/actual/power-wrong-scale.result.json")
    assert negative["raw_judge_responses"] == ["YES"]
    results = {}
    for mode in ("old_context", "wrong_scale", "wrong_base", "wrong_unit", "complete"):
        def fixed(stage, schema, instruction, inputs):
            raw = json.loads(read(ROOT / "actual-development-v1" / f"cq1-a29.{stage}.raw.json")["raw"])
            if stage == "mapping" and mode != "old_context":
                raw["facts"][0]["alternatives"][0][0]["context"] = []
            elif stage == "composition":
                cue = inputs["request_focus"]["r1"]["claim_text"]
                assert cue == "One gigawatt is equivalent to 1,000,000,000 watts."
                raw["claims"][0]["text"] = {
                    "wrong_scale": negative["guard_result"]["raw_output"],
                    "wrong_base": cue.replace("gigawatt", "megawatt"),
                    "wrong_unit": cue.replace("watts", "watt-hours"),
                    "complete": cue,
                }[mode]
            return {"parsed": schema.model_validate_json(json.dumps(raw)).model_dump()}
        try:
            draft = prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
        except ValueError as exc:
            assert mode != "complete"
            if mode == "old_context":
                assert "context" in str(exc)
            else:
                assert "source base, digit value and requested unit" in str(exc)
            results[mode] = "rejected before safety"
        else:
            assert mode == "complete" and not draft.diagnostics["fallback_unit_ids"]
            leading = _safety_excerpt(plan.query, draft.draft, source_records, include_power=True)
            source = prior["source"]
            assert leading["text"] == source["quote"] and leading["span_id"] == source["span_id"]
            assert [leading["start"], leading["end"]] == source["source_offsets"]
            assert leading["content_sha256"] == source["content_sha256"]
            full = "\n".join(s["content"] for s in source_records.values())
            assert hashlib.sha256(full.encode()).hexdigest() == prior["actual_safety_result"]["context_sha256"]
            results[mode] = {"draft": draft.draft, "leading_excerpt": leading, "full_evidence_sha256": hashlib.sha256(full.encode()).hexdigest()}
    with (ROOT / "directed-power-offline-replay.json").open("x", encoding="utf-8") as stream:
        json.dump({"model_calls": 0, "safety_calls": 0, "sockets_blocked": True, "results": results}, stream, indent=2)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
