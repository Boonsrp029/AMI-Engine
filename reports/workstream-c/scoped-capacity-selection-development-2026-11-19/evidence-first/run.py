"""Verify the frozen pair offline, or run it under a direct grant."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from scripts.diagnose_source_policy import sha, worker
from src.pilot._model_identity import verify_model

ROOT = Path(__file__).resolve().parent
REPLY = "Authorize capacity evidence-first fact-check diagnostics"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--grant", type=Path)
    parser.add_argument("--child", type=int, choices=(0, 1), help=argparse.SUPPRESS)
    args = parser.parse_args()
    frozen = ROOT / "contract.json"
    if sha(frozen) != args.contract_sha256:
        parser.error("Contract hash mismatch")
    contract = json.loads(frozen.read_bytes())
    if any(sha(path) != digest for path, digest in contract["inputs"].items()):
        parser.error("Frozen input changed")
    if not args.execute:
        if args.child is not None:
            parser.error("Child requires execution mode")
        print("Verified inputs only. Zero inference.")
        return 0
    if args.grant is None or json.loads(args.grant.read_bytes()) != {
        "contract_sha256": args.contract_sha256, "human_reply": REPLY
    }:
        parser.error("Explicit matching user grant required")
    output = ROOT / "actual"
    if args.child is not None:
        n = args.child
        if n and json.loads((output / "result-0.json").read_bytes())["contract_passed"] is not True:
            parser.error("The first case must pass")
        with (output / f"started-{n}.json").open("x", encoding="utf-8") as stream:
            json.dump({"index": n, "contract_sha256": args.contract_sha256}, stream)
        verify_model(contract["model_snapshot"])
        path = output / f"result-{n}.json"
        code = worker(contract["cases"][n], path)
        verify_model(contract["model_snapshot"])
        return code or int(json.loads(path.read_bytes())["contract_passed"] is not True)
    output.mkdir(exist_ok=False)
    for n in range(len(contract["cases"])):
        cmd = [sys.executable, str(Path(__file__).resolve()), "--contract-sha256", args.contract_sha256,
               "--execute", "--grant", str(args.grant.resolve()), "--child", str(n)]
        with (output / f"execution-{n}.log").open("xb") as log:
            try:
                code = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=60).returncode
                status = "pass" if code == 0 else "failed"
            except subprocess.TimeoutExpired:
                status = "timeout"
        if status != "pass":
            (output / "stopped.json").write_text(json.dumps({"index": n, "status": status}), encoding="utf-8")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
