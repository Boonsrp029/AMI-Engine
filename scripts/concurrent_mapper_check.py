"""One separately granted mapper request; inspect/validate modes are offline."""
import argparse
import json
from pathlib import Path
import socket
import sys
import time
from unittest.mock import patch

from scripts._mapper_transport import read_json, request_body, sha, supervise, write_json, _loads, MODEL


LIMITS = {"overall_seconds": 95, "service_seconds": 60, "validation_seconds": 30,
          "main_calls": 1, "nemo_invocations": 0, "composer_calls": 0, "retries": 0, "warmups": 0}
REQUIRED_PROJECT_FILES = {"scripts/concurrent_mapper_check.py", "scripts/concurrent_mapper_envelope.py",
                          "scripts/_mapper_transport.py"}


def inside(root, name):
    root = Path(root).resolve()
    path = (root / name).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Protocol path leaves declared root")
    return path


def check_protocol(path, digest):
    path = Path(path).resolve()
    if sha(path) != digest:
        raise ValueError("Protocol identity changed")
    protocol = read_json(path)
    if (protocol["kind"] != "concurrent-mapper-only-v1" or protocol["limits"] != LIMITS
            or protocol["model"] != MODEL or protocol["case_id"] != "cq-p02"
            or protocol["output_directory"] != "actual-mapper"
            or not REQUIRED_PROJECT_FILES <= set(protocol["project_files"])):
        raise ValueError("Diagnostic scope or budget changed")
    for name, expected in protocol["project_files"].items():
        if sha(inside(Path.cwd(), name)) != expected:
            raise ValueError("Frozen project input changed")
    for name, expected in protocol["files"].items():
        if sha(inside(path.parent, name)) != expected:
            raise ValueError("Frozen request changed")
    proposal = read_json(inside(path.parent, protocol["proposal"]))
    if proposal["case_id"] != protocol["case_id"] or proposal["model_snapshot"]["digest"] != protocol["model_digest"]:
        raise ValueError("Mapper case or model pin changed")
    # Discover actual runtime paths, not merely the files the protocol lists.
    runtime = set(Path("src").rglob("*.py"))
    for pattern in ("*.yaml", "*.yml", "*.co"):
        runtime.update(Path("config").rglob(pattern))
    runtime.update(Path(n) for n in ("requirements.txt", "requirements-serving.txt", "constraints-pilot.txt"))
    current = {str(p.resolve()): sha(p) for p in runtime}
    if current != proposal["runtime_inputs"]:
        raise ValueError("Current runtime identity changed")
    for name, expected in proposal["input_sha256"].items():
        if sha(inside(path.parent, name)) != expected:
            raise ValueError("Frozen proposal request changed")
    if sha(inside(Path.cwd(), proposal["corpus_path"])) != proposal["corpus_sha256"]:
        raise ValueError("Frozen corpus changed")
    native = inside(path.parent, protocol["native_body"])
    if (request_body(read_json(inside(path.parent, protocol["input"]))) != read_json(native)
            or sha(native) != protocol["native_body_sha256"]):
        raise ValueError("Native request differs from frozen input")
    return protocol, proposal


def replay_mapping(proposal, response):
    """Use the real callback but stop before composition, with zero inference."""
    from src.pilot.subtasks.contracts import Plan
    from src.pilot.subtasks.generation import ConcurrentComposer
    from src.pilot.subtasks.retrieval import LocalBM25Adapter
    from src.pilot.subtasks.scheduler import run_plan
    from src.pilot.subtasks.runner import ModelAccess
    plan = Plan.model_validate_json(json.dumps(proposal["plan"]))
    report = run_plan(plan, "e" * 32, "f" * 32, LocalBM25Adapter(proposal["corpus_path"]))
    captured = {}
    composition_inputs = {}

    class StopBeforeComposition(Exception):
        pass

    def fixed(stage, schema, instruction, inputs):
        if stage == "composition":
            composition_inputs.update(inputs)
            raise StopBeforeComposition()
        if stage != "mapping" or captured:
            raise AssertionError("Unexpected callback stage or repeated mapping")
        captured.update(schema=schema.model_json_schema(), messages=[
            {"type": "system", "content": instruction},
            {"type": "human", "content": json.dumps(inputs, ensure_ascii=False, separators=(",", ":"))}])
        return {"parsed": response, "raw": json.dumps(response), "usage": None}

    access = ModelAccess(time.monotonic() + 30)
    try:
        result = ConcurrentComposer(plan, proposal["bindings"], proposal["as_of"], fixed,
            complete_required_branches=proposal["complete_required_branches"])(report, access)
    except StopBeforeComposition:
        result = None
    if access.guards or access.calls not in (1, 2):
        raise AssertionError("Offline mapping replay exceeded logical stage limits")
    return {"captured": captured, "composition_inputs_for_review": composition_inputs,
            "empty_result": result.draft if result else None, "fixed_mapper_replays": 1,
            "composition_callbacks_intercepted": int(bool(composition_inputs)),
            "actual_model_calls": 0, "actual_composer_calls": 0, "nemo_invocations": 0}


def validate_response(protocol_path, digest, service_path, output):
    protocol, proposal = check_protocol(protocol_path, digest)
    result = {"actual_model_calls": 0, "nemo_invocations": 0, "network_blocked": True,
              "source_assessment": "pending", "owner_adjudication": "pending"}
    try:
        received = read_json(service_path)
        if (not received["status"].startswith("completed_transport") or received["response_complete"] is not True
                or type(received["model_calls_started"]) is not int or received["model_calls_started"] != 1
                or received["identity_before"] is not True or received["identity_after"] is not True
                or received["finish"].get("done_reason") != "stop"):
            raise ValueError("Service response did not satisfy transport gates")
        response = _loads(received["content"])
        def forbidden(*args, **kwargs):
            raise AssertionError("Offline validation cannot open a socket")
        with (patch.object(socket.socket, "connect", forbidden), patch.object(socket.socket, "connect_ex", forbidden),
              patch.object(socket.socket, "sendto", forbidden), patch.object(socket, "getaddrinfo", forbidden),
              patch.object(socket, "create_connection", forbidden)):
            checked = replay_mapping(proposal, response)
        frozen = read_json(inside(Path(protocol_path).resolve().parent, protocol["input"]))
        if checked["captured"] != frozen:
            raise ValueError("Actual mapper schema or messages changed")
        check_protocol(protocol_path, digest)
        result.update(status="validated; semantic source assessment pending", raw_selection=response, replay=checked)
    except Exception as exc:
        result.update(status="failed", error_type=type(exc).__name__, error=str(exc))
    with (Path(output) / "validation-result.json").open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def execute(protocol_path, digest, authorization):
    started = time.monotonic()
    protocol_path = Path(protocol_path).resolve()
    protocol, _ = check_protocol(protocol_path, digest)
    grant = read_json(authorization)
    if (grant.get("contract_sha256") != digest or grant.get("human_reply") != protocol["authorization_reply"]
            or not isinstance(grant.get("authorization_reference"), str) or not grant["authorization_reference"].strip()):
        raise ValueError("A new direct protocol-specific user grant is required")
    output = inside(protocol_path.parent, protocol["output_directory"])
    output.mkdir(exist_ok=False)
    deadline = started + 95
    summary = {"status": "started", "model_calls_started": None, "maximum_main_calls": 1,
        "nemo_invocations": 0, "composer_calls": 0, "source_assessment": "pending", "owner_adjudication": "pending",
        "conditional_workflow_authorized": False, "backend_cancellation_verified": False,
        "retry_performed": False, "phase_results": {}}
    try:
        seconds = min(60, deadline - time.monotonic() - 32)
        if seconds <= 0:
            raise TimeoutError("Preparation exhausted service budget")
        service_out = output / "service"
        phase = supervise([sys.executable, "-m", "scripts._mapper_transport", "service",
            "--input", str(inside(protocol_path.parent, protocol["native_body"])), "--output", str(service_out),
            "--contract", str(protocol_path), "--contract-sha256", digest, "--authorization", str(authorization),
            "--deadline", str(time.monotonic() + seconds)], service_out, seconds)
        summary["phase_results"]["service"] = phase
        progress = service_out / "service-progress.json"
        if progress.exists():
            observed = read_json(progress)
            summary.update(model_calls_started=observed.get("model_calls_started"),
                inflight_usage_unknown=not observed.get("response_complete", False))
        if phase["timed_out"] or phase["returncode"] != 0:
            raise RuntimeError("Service failed; no retry")
        service_path = service_out / "service-result.json"
        received = read_json(service_path)
        summary.update(model_calls_started=received["model_calls_started"], usage=received["usage"],
            inflight_usage_unknown=received["inflight_usage_unknown"])
        seconds = min(30, deadline - time.monotonic() - 2)
        if seconds <= 0:
            raise TimeoutError("No offline validation budget remains")
        validation_out = output / "validation"
        phase = supervise([sys.executable, "-m", "scripts.concurrent_mapper_check", "--mode", "validate",
            "--protocol", str(protocol_path), "--sha256", digest, "--service", str(service_path),
            "--output", str(validation_out)], validation_out, seconds)
        summary["phase_results"]["validation"] = phase
        if phase["timed_out"] or phase["returncode"] != 0:
            raise RuntimeError("Offline validation failed; no retry")
        checked = read_json(validation_out / "validation-result.json")
        if not checked["status"].startswith("validated;"):
            raise RuntimeError("Mapping validation gate failed")
        check_protocol(protocol_path, digest)
        if time.monotonic() > deadline:
            raise TimeoutError("Overall diagnostic deadline exceeded")
        summary["status"] = "validated; source review pending; allowance closed"
    except Exception as exc:
        summary.update(status="failed; allowance closed", error_type=type(exc).__name__, error=str(exc))
    summary.update(elapsed_seconds=time.monotonic() - started, overall_seconds=95,
        elapsed_budget_exceeded=time.monotonic() > deadline, approvals_created=0, exports_created=0)
    write_json(output / "summary.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["inspect", "execute", "validate"], default="inspect")
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--service", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "inspect":
        check_protocol(args.protocol, args.sha256)
        print(json.dumps({"protocol_valid": True, "actual_model_calls": 0, "execution_authorized": False}))
        return 0
    if args.mode == "validate":
        if not args.service or not args.output:
            parser.error("Validation requires a retained response and owned output")
        result = validate_response(args.protocol, args.sha256, args.service, args.output)
    else:
        if not args.authorization:
            parser.error("Execution requires a new protocol-specific user grant")
        result = execute(args.protocol, args.sha256, args.authorization)
    print(json.dumps(result))
    return 0 if result["status"].startswith("validated;") else 1


if __name__ == "__main__":
    raise SystemExit(main())
