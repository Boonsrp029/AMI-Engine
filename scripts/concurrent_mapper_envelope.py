"""Hard process envelope for one granted mapper diagnostic; never retry."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from scripts.concurrent_mapper_check import check_protocol
from scripts._mapper_transport import read_json, write_json


def run(protocol, digest, authorization, *, popen=subprocess.Popen, clock=time.monotonic,
        terminate_tree=None):
    started = clock()
    protocol = Path(protocol).resolve()
    checked, _ = check_protocol(protocol, digest)
    grant = read_json(authorization)
    if (grant.get("contract_sha256") != digest or grant.get("human_reply") != checked["authorization_reply"]
            or not isinstance(grant.get("authorization_reference"), str) or not grant["authorization_reference"].strip()):
        raise ValueError("A new direct protocol-specific user grant is required")
    output = protocol.parent / "operator-envelope"
    output.mkdir(exist_ok=False)
    write_json(output / "started.json", {"maximum_seconds": 95, "started_monotonic": started,
        "retries": 0, "protocol_sha256": digest})
    process = None
    timed_out = False
    code = None
    try:
        with (output / "stdout.txt").open("wb") as stdout, (output / "stderr.txt").open("wb") as stderr:
            remaining = 95 - (clock() - started)
            if remaining <= 0:
                raise TimeoutError("Preparation exhausted overall budget")
            process = popen([sys.executable, "-m", "scripts.concurrent_mapper_check", "--mode", "execute",
                "--protocol", str(protocol), "--sha256", digest, "--authorization", str(authorization)],
                stdout=stdout, stderr=stderr)
            remaining = 95 - (clock() - started)
            if remaining <= 0:
                raise subprocess.TimeoutExpired("owned mapper controller", 95)
            code = process.wait(timeout=remaining)
    except (subprocess.TimeoutExpired, TimeoutError):
        timed_out = True
        if process is not None and process.poll() is None:
            if terminate_tree:
                terminate_tree(process)
            elif sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    capture_output=True, timeout=5, check=False)
                if process.poll() is None:
                    process.kill()
            else:
                # This frozen operator is Windows-only; refuse other hosts below.
                process.kill()
            code = process.wait(timeout=5)
    result = {"returncode": code, "timed_out": timed_out, "elapsed_seconds": clock() - started,
        "maximum_seconds": 95, "retry_performed": False, "backend_cancellation_verified": False,
        "status": "stopped at process boundary" if timed_out else "controller returned; inspect its retained result",
        "source_assessment": "pending", "owner_adjudication": "pending"}
    write_json(output / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("Frozen diagnostic operator requires Windows process-tree termination")
    result = run(args.protocol, args.sha256, args.authorization)
    print(json.dumps(result))
    return 0 if result["returncode"] == 0 and not result["timed_out"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
