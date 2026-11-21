"""Run one explicitly granted source-policy check. Default mode verifies offline."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from scripts.diagnose_source_policy import sha, worker
from src.pilot._model_identity import verify_model

ROOT = Path(__file__).resolve().parent
REPLY = "Authorize one capacity fact-check diagnostic"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--grant", type=Path)
    args = parser.parse_args()
    path = ROOT / "fact-check-contract.json"
    if sha(path) != args.contract_sha256:
        parser.error("Contract hash mismatch")
    contract = json.loads(path.read_bytes())
    if any(sha(p) != digest for p, digest in contract["inputs"].items()):
        parser.error("Frozen input changed")
    if not args.execute:
        print("Verified inputs only. Zero inference.")
        return 0
    if args.grant is None or json.loads(args.grant.read_bytes()) != {
        "contract_sha256": args.contract_sha256, "human_reply": REPLY
    }:
        parser.error("Explicit matching user grant required")
    output = ROOT / "actual-fact-check"
    output.mkdir(exist_ok=False)
    # A fresh process owns the entire 60-second inference and verification window.
    child = [
        sys.executable, "-c",
        "from runpy import run_path; import sys; "
        "script = run_path(sys.argv[1]); sys.exit(script['check']())", str(Path(__file__).resolve().with_name("run_fact_check.py")),
    ]
    try:
        with (output / "execution.log").open("xb") as log:
            result = subprocess.run(child, stdout=log, stderr=subprocess.STDOUT, timeout=60)
    except subprocess.TimeoutExpired:
        (output / "stopped.json").write_text('{"status":"timeout","retry":false}\n', encoding="utf-8")
        return 1
    return result.returncode


def check():
    c = json.loads((ROOT / "fact-check-contract.json").read_bytes())
    verify_model(c["model_snapshot"])
    code = worker(c["case"], ROOT / "actual-fact-check/result.json")
    verify_model(c["model_snapshot"])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
