"""Freeze a mapper request offline; this script never executes inference."""
import hashlib
import json
from pathlib import Path
import socket
import time


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "question-span-2026-11-07"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, value):
    with (OUT / name).open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    def blocked(*args, **kwargs):
        raise AssertionError("Offline preparation cannot use network services")

    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = socket.getaddrinfo = blocked
    from src.pilot.subtasks.contracts import Plan
    from src.pilot.subtasks.generation import ConcurrentComposer, CONCURRENT_MAPPING_VERSION
    from src.pilot.subtasks.retrieval import LocalBM25Adapter
    from src.pilot.subtasks.scheduler import run_plan
    from src.pilot.subtasks.runner import ModelAccess
    from src.pilot.subtasks._development_lineage import runtime_inputs
    from scripts._mapper_transport import request_body, validate_body

    old_contract = ROOT / "title-lineage-2026-11-07/development-contract-v7.json"
    contract = json.loads(old_contract.read_text(encoding="utf-8"))
    case = contract["cases"]["cq-p02"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert sha(case["corpus_path"]) == plan.corpus_sha256
    report = run_plan(plan, "c" * 32, "d" * 32, LocalBM25Adapter(case["corpus_path"]))
    frozen = {}

    class Captured(Exception):
        pass

    def capture(stage, schema, instruction, inputs):
        assert stage == "mapping" and not frozen
        frozen.update(schema=schema.model_json_schema(), messages=[
            {"type": "system", "content": instruction},
            {"type": "human", "content": json.dumps(inputs, ensure_ascii=False, separators=(",", ":"))}])
        raise Captured()

    access = ModelAccess(time.monotonic() + 30)
    try:
        ConcurrentComposer(plan, case["bindings"], "2026-11-07", capture,
            complete_required_branches=case["complete_required_branches"])(report, access)
    except Captured:
        pass
    else:
        raise AssertionError("Expected mapper capture, never composition")
    assert frozen and access.calls == 1 and access.guards == 0
    body = request_body(frozen)
    validate_body(body)
    OUT.mkdir(exist_ok=True)
    write("mapper-input.json", frozen)
    write("mapper-request-body.json", body)
    write("mapper-preflight-proposal.json", {
        "status": "prepared only; no execution grant", "case_id": "cq-p02",
        "mapping_version": CONCURRENT_MAPPING_VERSION,
        "as_of": "2026-11-07", "plan": plan.model_dump(mode="json"),
        "bindings": case["bindings"], "complete_required_branches": case["complete_required_branches"],
        "model_snapshot": contract["model_snapshot"], "settings": contract["settings"],
        "input_sha256": {str((OUT / n).resolve()): sha(OUT / n) for n in ("mapper-input.json", "mapper-request-body.json")},
        "runtime_inputs": runtime_inputs(), "corpus_path": case["corpus_path"],
        "corpus_sha256": plan.corpus_sha256,
        "budget": {"main_calls": 1, "nemo_invocations": 0, "composer_calls": 0,
            "service_seconds": 60, "offline_validation_seconds": 30, "overhead_seconds": 5,
            "total_seconds": 95, "retries": 0, "warmups": 0},
        "acceptance": ["Strict current wire parses and resolves through existing source validators",
            "Retain supported wind share, generation measure, country and historical period",
            "Partial component identifies unanswered Denmark retail electricity prices yesterday using exact question offsets",
            "Do not call wind fact missing; do not invent price facts; no contradictory source assignments",
            "Valid offset membership alone does not pass semantic missingness or completeness"],
        "excluded": ["full workflow", "CQ1", "Ragas", "hosted inference", "approval/export", "deployment"],
        "preparation": {"actual_model_calls": 0, "network_blocked": True,
            "logical_capture_slots": access.calls, "request_body_validation": "passed"}})
    print("Frozen mapper-only proposal; zero actual model calls")


if __name__ == "__main__":
    main()
