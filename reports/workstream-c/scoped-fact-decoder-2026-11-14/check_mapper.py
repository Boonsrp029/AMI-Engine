"""Prepare, verify, or execute one explicitly granted mapper-only diagnostic."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import sys
import time


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
sys.path.insert(0, str(PROJECT))

from scripts._mapper_transport import request_body, sha, supervise


CASE = "cq1-a20"
REPLY = "Authorize one scoped fact-decoder mapper diagnostic"
LIMITS = {"overall_seconds": 120, "service_seconds": 60, "validation_seconds": 25,
          "main_calls": 1, "composer_calls": 0, "nemo_invocations": 0, "retries": 0}
PRIOR = ROOT.parent / "scoped-fact-selection-development-2026-11-14"


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def no_network(*args, **kwargs):
    raise AssertionError("Offline request validation cannot open sockets")


def capture(response=None):
    from src.pilot.subtasks._scoped_activation import prepare_composer
    from src.pilot.subtasks.contracts import Plan
    from src.pilot.subtasks.retrieval import LocalBM25Adapter
    from src.pilot.subtasks.runner import ModelAccess
    from src.pilot.subtasks.scheduler import run_plan

    socket.socket.connect = socket.create_connection = no_network
    contract = read(PRIOR / "development-contract.json")
    case = contract["cases"][CASE]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    if sha(Path(case["corpus_path"])) != plan.corpus_sha256:
        raise ValueError("Corpus identity changed")
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    frozen = {}
    projected = {}

    class Captured(Exception):
        pass

    def fixed(stage, schema, instruction, inputs):
        if stage == "composition" and response is not None:
            projected.update(inputs)
            raise Captured
        if stage != "mapping" or frozen:
            raise AssertionError("Unexpected callback stage")
        frozen.update(schema=schema.model_json_schema(), messages=[
            {"type": "system", "content": instruction},
            {"type": "human", "content": json.dumps(inputs, ensure_ascii=False, separators=(",", ":"))}])
        if response is None:
            raise Captured
        return {"parsed": schema.model_validate_json(response).model_dump(), "raw": response}

    try:
        prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 20))
    except Captured:
        pass
    return frozen, projected


def prepare():
    from pydantic import ValidationError
    from scripts._llama_token_count import encoding
    from src.pilot.subtasks._development_lineage import runtime_inputs

    frozen, _ = capture()
    previous = read(PRIOR / f"actual-development-v1/{CASE}.mapping.raw.json")["raw"]
    try:
        capture(previous)
    except ValidationError:
        pass
    else:
        raise AssertionError("Saved invalid response passed revised schema")
    prior_contract = read(PRIOR / "development-contract.json")
    tokenizer_path = Path(prior_contract["tokenizer_path"])
    if sha(tokenizer_path) != prior_contract["tokenizer_sha256"]:
        raise ValueError("Tokenizer identity changed")
    counter = encoding(read(tokenizer_path))
    reserved = sum(len(counter.encode(m["content"])) for m in frozen["messages"]) + 1156
    if reserved > 4096:
        raise ValueError("Mapper context budget exceeded")
    native = ROOT / "native-request.json"
    write(native, request_body(frozen))
    case = prior_contract["cases"][CASE]
    paths = [Path(__file__), PROJECT / "scripts/_mapper_transport.py", native, tokenizer_path,
             PRIOR / "development-contract.json", PRIOR / "batch-summary.json",
             PRIOR / f"actual-development-v1/{CASE}.mapping.raw.json", Path(case["corpus_path"]),
             Path(case["requested_scopes"])]
    protocol = {"case_id": CASE, "as_of": "2026-11-14", "authorization_reply": REPLY, "limits": LIMITS,
                "native_body_sha256": sha(native), "model_digest": prior_contract["model_snapshot"]["digest"],
                "reserved_tokens": reserved, "saved_invalid_response_rejected_by_schema": True,
                "pins": {**runtime_inputs(), **{str(p.resolve()): sha(p) for p in paths}}}
    write(ROOT / "protocol.json", protocol)
    return protocol


def verify(expected):
    protocol_path = ROOT / "protocol.json"
    if sha(protocol_path) != expected:
        raise ValueError("Protocol identity changed")
    protocol = read(protocol_path)
    if (protocol["case_id"] != CASE or protocol["limits"] != LIMITS or protocol["authorization_reply"] != REPLY
            or any(sha(Path(name)) != value for name, value in protocol["pins"].items())):
        raise ValueError("Frozen mapper inputs changed")
    return protocol


def validate(expected, service, output):
    protocol = verify(expected)
    received = read(service)
    if (not received["status"].startswith("completed_transport") or received["model_calls_started"] != 1
            or not received["identity_before"] or not received["identity_after"]
            or received["finish"].get("done_reason") != "stop"):
        raise ValueError("Transport did not complete the single pinned request")
    frozen, projected = capture(received["content"])
    if request_body(frozen) != read(ROOT / "native-request.json") or not projected:
        raise ValueError("Response did not reach the unchanged composition boundary")
    verify(expected)
    write(output, {"submitted_model_calls": 0, "composition_calls": 0, "composition_inputs": projected,
                   "protocol_case": protocol["case_id"], "source_review": "pending"})


def execute(expected, grant_path):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    started = time.monotonic()
    protocol = verify(expected)
    grant = read(grant_path)
    if (grant.get("contract_sha256") != expected or grant.get("human_reply") != REPLY
            or not str(grant.get("authorization_reference", "")).strip()
            or protocol["as_of"] != datetime.now(ZoneInfo("Asia/Bangkok")).date().isoformat()):
        raise ValueError("Applicable dated direct user grant is required")
    output = ROOT / "actual-mapper"
    output.mkdir()
    protocol_path = ROOT / "protocol.json"
    interpreter = sys.executable
    service_deadline = time.monotonic() + LIMITS["service_seconds"]
    command = [interpreter, str(PROJECT / "scripts/_mapper_transport.py"), "service",
               "--input", str(ROOT / "native-request.json"), "--output", str(output / "service"),
               "--contract", str(protocol_path), "--contract-sha256", expected,
               "--authorization", str(grant_path.resolve()), "--deadline", str(service_deadline)]
    service = supervise(command, output / "service", max(.001, service_deadline - time.monotonic()))
    if service["returncode"] != 0 or service["timed_out"]:
        return 1
    remaining = min(LIMITS["validation_seconds"], LIMITS["overall_seconds"] - (time.monotonic() - started))
    if remaining <= 0:
        return 1
    check = supervise([interpreter, str(Path(__file__)), "validate", "--hash", expected,
                       "--service", str(output / "service/service-result.json"),
                       "--output", str(output / "validated.json")], output / "validation", remaining)
    return int(check["returncode"] != 0 or check["timed_out"] or time.monotonic() - started > LIMITS["overall_seconds"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["prepare", "verify", "validate", "execute"])
    parser.add_argument("--hash")
    parser.add_argument("--grant", type=Path)
    parser.add_argument("--service", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        protocol = prepare()
    elif args.mode == "execute":
        return execute(args.hash, args.grant)
    elif args.mode == "validate":
        validate(args.hash, args.service, args.output)
        return 0
    else:
        protocol = verify(args.hash)
    print(json.dumps({"protocol_sha256": sha(ROOT / "protocol.json"),
                      "pins": len(protocol["pins"]), "reserved_tokens": protocol["reserved_tokens"],
                      "model_calls": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
