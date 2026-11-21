"""Run one case from the frozen power-conversion safety diagnostic."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from scripts.diagnose_source_policy import sha, worker
from src.pilot._model_identity import verify_model

ROOT = Path(__file__).resolve().parent
CASES = ("power-supported", "power-wrong-scale")
REPLY = "Authorize power conversion evidence-first fact-check diagnostics"


def passed(result, expected):
    safety = result.get("guard_result", {})
    if result.get("status") != "assessed" or result.get("contract_passed") is not True:
        return False
    if expected == "YES":
        return safety.get("passed_guardrails") is True and safety.get("validated_report") == safety.get("raw_output")
    return safety.get("passed_guardrails") is False and safety.get("blocking_rail") == "self check facts"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--case", choices=CASES)
    parser.add_argument("--grant", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    path = ROOT / "contract.json"
    if sha(path) != args.contract_sha256:
        parser.error("Contract hash mismatch")
    contract = json.loads(path.read_bytes())
    if (list(contract["cases"]) != list(CASES)
            or contract["limits"] != {"seconds_per_case": 60, "nemo_total": 2, "workflow_calls": 0, "retries": 0}
            or any(sha(path) != digest for path, digest in contract["inputs"].items())):
        parser.error("Frozen inputs or scope changed")
    if not args.execute:
        if args.child:
            parser.error("Child requires execution mode")
        print("Verified frozen inputs. Zero inference.")
        return 0

    if args.case is None or args.grant is None or json.loads(args.grant.read_bytes()) != {
            "contract_sha256": args.contract_sha256, "human_reply": REPLY}:
        parser.error("Explicit matching user grant and case required")
    out = ROOT / "actual"
    if (out / "stopped.json").exists():
        parser.error("Allowance closed")
    if args.case == CASES[1]:
        first_path = out / f"{CASES[0]}.result.json"
        if not first_path.exists() or not passed(json.loads(first_path.read_bytes()), "YES"):
            parser.error("The supported case must pass before the negative control")

    case = contract["cases"][args.case]
    result_path = out / f"{args.case}.result.json"
    marker = out / f"{args.case}.started.json"
    if args.child:
        if not (out / f"{args.case}.log").is_file():
            parser.error("Child requires a reserved parent invocation")
        with marker.open("x", encoding="utf-8") as stream:
            json.dump({"contract_sha256": args.contract_sha256, "case_id": args.case}, stream)
        verify_model(contract["model_snapshot"])
        code = worker(case, result_path)
        verify_model(contract["model_snapshot"])
        return code or int(not passed(json.loads(result_path.read_bytes()), case["expected_single_verdict"]))

    out.mkdir(exist_ok=True)
    with (out / f"{args.case}.log").open("xb") as log:
        command = [sys.executable, str(Path(__file__).resolve()), "--contract-sha256", args.contract_sha256,
                   "--execute", "--case", args.case, "--grant", str(args.grant.resolve()), "--child"]
        try:
            code = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=60).returncode
            status = "passed" if code == 0 else "failed"
        except subprocess.TimeoutExpired:
            status = "timeout"
    if status != "passed":
        with (out / "stopped.json").open("x", encoding="utf-8") as stream:
            json.dump({"case_id": args.case, "status": status, "retry": False}, stream)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
