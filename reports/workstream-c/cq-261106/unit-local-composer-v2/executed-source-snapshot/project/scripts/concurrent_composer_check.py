"""One granted concurrent composer request; default mode only inspects pinned files."""
import argparse
import json
from pathlib import Path
import socket
import sys
import time
from unittest.mock import patch

from scripts._mapper_transport import read_json, request_body, sha, supervise, write_json, _loads, MODEL


LIMITS = {"overall_seconds":95, "service_seconds":60, "validation_seconds":30,
          "main_calls":1, "nemo_invocations":0, "retries":0}
REQUIRED_PROJECT_FILES = {"scripts/concurrent_composer_check.py", "scripts/_concurrent_composer_capture.py",
    "scripts/_mapper_transport.py", "src/pilot/subtasks/generation.py",
    "src/pilot/subtasks/_composition_instruction.py"}


def inside(root, name):
    path = (Path(root) / name).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("Protocol path leaves declared root")
    return path


def check_protocol(path, digest):
    path = Path(path).resolve()
    if sha(path) != digest:
        raise ValueError("Protocol identity changed")
    protocol = read_json(path)
    if (protocol["kind"] != "concurrent-composer-only-v1" or protocol["limits"] != LIMITS
            or protocol["model"] != MODEL or protocol["case_id"] != "cq-p01"
            or protocol["output_directory"] != "actual"
            or not REQUIRED_PROJECT_FILES <= set(protocol["project_files"])):
        raise ValueError("Diagnostic scope or budget changed")
    for name, expected in protocol["project_files"].items():
        if sha(inside(Path.cwd(), name)) != expected:
            raise ValueError("Frozen project input changed")
    for name, expected in protocol["files"].items():
        if sha(inside(path.parent, name)) != expected:
            raise ValueError("Frozen request changed")
    frozen = read_json(inside(path.parent, protocol["input"]))
    native_path = inside(path.parent, protocol["native_body"])
    if (request_body(frozen) != read_json(native_path)
            or sha(native_path) != protocol["native_body_sha256"]):
        raise ValueError("Native request differs from frozen input")
    contract_path = inside(Path.cwd(), protocol["frozen_contract"])
    mapping_path = inside(Path.cwd(), protocol["frozen_mapping"])
    contract = read_json(contract_path)
    expected = protocol["replay_identity"]
    corpus = inside(Path.cwd(), contract["cases"][protocol["case_id"]]["corpus_path"])
    if (sha(contract_path) != expected["contract"] or sha(mapping_path) != expected["mapping"]
            or sha(corpus) != expected["corpus"]):
        raise ValueError("Retained replay inputs changed")
    return protocol


def validate_response(protocol_path, digest, service_path, output):
    """Validate one fixed response offline with sockets disabled and no safety."""
    output = Path(output)
    protocol = check_protocol(protocol_path, digest)
    result = {"actual_model_calls":0, "nemo_invocations":0, "network_blocked":True}
    try:
        received = read_json(service_path)
        if (not received["status"].startswith("completed_transport") or not received["response_complete"]
                or received["model_calls_started"] != 1 or not received["identity_before"]
                or not received["identity_after"] or received["finish"].get("done_reason") != "stop"):
            raise ValueError("Service response did not satisfy transport gates")
        response = _loads(received["content"])
        def forbidden(*args, **kwargs):
            raise AssertionError("Offline validation cannot open a socket")
        # Preserve the socket class during heavy imports (ssl subclasses it).
        with (patch.object(socket.socket, "connect", forbidden),
              patch.object(socket.socket, "connect_ex", forbidden),
              patch.object(socket.socket, "sendto", forbidden),
              patch.object(socket, "getaddrinfo", forbidden),
              patch.object(socket, "create_connection", forbidden)):
            from scripts._concurrent_composer_capture import capture_composer
            checked = capture_composer(inside(Path.cwd(), protocol["frozen_contract"]),
                protocol["case_id"], inside(Path.cwd(), protocol["frozen_mapping"]),
                expected=protocol["replay_identity"], response=response)
        frozen = read_json(inside(Path(protocol_path).resolve().parent, protocol["input"]))
        if checked["captured"] != frozen:
            raise ValueError("Actual composer schema or messages changed")
        if not checked["status"].startswith("composition validated"):
            raise ValueError(checked.get("error", "Composition validation failed"))
        result.update(status="validated; safety not executed; source assessment pending", replay=checked)
        check_protocol(protocol_path, digest)
    except Exception as exc:
        result.update(status="failed", error_type=type(exc).__name__, error=str(exc))
    with (output / "validation-result.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return result


def execute(protocol_path, digest, authorization):
    started = time.monotonic()
    protocol_path = Path(protocol_path).resolve()
    protocol = check_protocol(protocol_path, digest)
    grant = read_json(authorization)
    if (grant.get("contract_sha256") != digest
            or grant.get("human_reply") != protocol["authorization_reply"]
            or not isinstance(grant.get("authorization_reference"), str)
            or not grant["authorization_reference"].strip()):
        raise ValueError("A new direct protocol-specific user grant is required")
    output = inside(protocol_path.parent, protocol["output_directory"])
    output.mkdir(exist_ok=False)  # A failed or interrupted attempt cannot restart.
    deadline = started + LIMITS["overall_seconds"]
    summary = {"status":"started", "model_calls_started":None, "maximum_main_calls":1,
        "nemo_invocations":0, "source_assessment":"pending", "owner_adjudication":"pending",
        "conditional_workflow_authorized":False, "backend_cancellation_verified":False,
        "retry_performed":False, "phase_results":{}}
    try:
        seconds = min(60, deadline-time.monotonic()-32)
        if seconds <= 0:
            raise TimeoutError("Preparation exhausted service budget")
        service_out = output / "service"
        phase = supervise([sys.executable,"-m","scripts._mapper_transport","service",
            "--input",str(inside(protocol_path.parent,protocol["native_body"])),
            "--output",str(service_out),"--contract",str(protocol_path),"--contract-sha256",digest,
            "--authorization",str(authorization),"--deadline",str(time.monotonic()+seconds)], service_out, seconds)
        summary["phase_results"]["service"] = phase
        progress = service_out / "service-progress.json"
        if progress.exists():
            observed = read_json(progress)
            summary.update(model_calls_started=observed.get("model_calls_started"),
                inflight_usage_unknown=not observed.get("response_complete",False))
        if phase["timed_out"] or phase["returncode"] != 0:
            raise RuntimeError("Service failed; no retry")
        service_path = service_out / "service-result.json"
        received = read_json(service_path)
        summary.update(model_calls_started=received["model_calls_started"], usage=received["usage"],
                       inflight_usage_unknown=received["inflight_usage_unknown"])
        seconds = min(30, deadline-time.monotonic()-2)
        if seconds <= 0:
            raise TimeoutError("No offline validation budget remains")
        validation_out = output / "validation"
        phase = supervise([sys.executable,"-m","scripts.concurrent_composer_check","--mode","validate",
            "--protocol",str(protocol_path),"--sha256",digest,"--service",str(service_path),
            "--output",str(validation_out)], validation_out, seconds)
        summary["phase_results"]["validation"] = phase
        if phase["timed_out"] or phase["returncode"] != 0:
            raise RuntimeError("Offline validation failed; no retry")
        checked = read_json(validation_out / "validation-result.json")
        if not checked["status"].startswith("validated;"):
            raise RuntimeError("Composition validation gate failed")
        check_protocol(protocol_path, digest)
        summary["status"] = "validated; source assessment required; no workflow authorized"
    except Exception as exc:
        summary.update(status="failed; allowance closed", error_type=type(exc).__name__)
    summary.update(elapsed_seconds=time.monotonic()-started, overall_seconds=95,
                   elapsed_budget_exceeded=time.monotonic()>deadline, approvals_created=0,exports_created=0)
    write_json(output / "summary.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["inspect","execute","validate"], default="inspect")
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--service", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "inspect":
        check_protocol(args.protocol,args.sha256)
        print(json.dumps({"protocol_valid":True,"actual_model_calls":0,"execution_authorized":False}))
        return 0
    if args.mode == "validate":
        if not args.service or not args.output:
            parser.error("Validation requires a retained response and an owned output")
        result = validate_response(args.protocol,args.sha256,args.service,args.output)
        return 0 if result["status"].startswith("validated;") else 1
    if not args.authorization:
        parser.error("Execution requires a new protocol-specific user grant")
    result = execute(args.protocol,args.sha256,args.authorization)
    print(json.dumps(result))
    return 0 if result["status"].startswith("validated;") else 1


if __name__ == "__main__":
    raise SystemExit(main())
