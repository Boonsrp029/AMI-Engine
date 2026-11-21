"""Compile the revised frozen CQ1 roster after two current actual development passes."""
import argparse
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parent
POOL = ROOT.parent / "cq1-us-table-pool-2026-11-19"
SHARED = ROOT.parent / "cq1-fact-span-pool-2026-11-15"
sys.path.insert(0, str(SHARED))
from build_qualification import build


def blocked(*args, **kwargs):
    raise AssertionError("Contract preparation cannot open sockets")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args()
    socket.socket.connect = socket.create_connection = blocked
    contract = build(
        development_path=ROOT.parent / "scoped-us-table-development-2026-11-19/development-contract.json",
        expected_identity="4ae9c89e7429eacb870fc45de78717063e789dc2a0cf64f4db2447459fb8dff0",
        pool=POOL / "pool", destination=ROOT / "qualification-contract.json",
        output_directory=ROOT / "actual-cq1", as_of=args.as_of,
        expected_pool_sha256="72d3f155ad77e17cd62bf5e1d5e6163ef0e8aa894ed9252f11891c167e8d0acd",
        expected_plans_sha256="fe0f862fd6b776247be6f0b19688bba2e6dcc696f49b0e0c8769ab865054e2df",
        scope_manifest_path=POOL / "question-scopes/manifest.json",
        expected_scopes_sha256="8fdcbfff52459285b5a790b083d5d7dccca55e728eb41905b911a4a80a9aa338",
        recorded_pool_root=ROOT.parent / "concurrent-qualification-2026-11-06/cq1",
        review_protocol=SHARED / "source-review-protocol.md",
        execution_artifacts=(ROOT / "run_qualification_case.py", Path(__file__), SHARED / "inspect_result.py",
                             POOL / "freeze-audit.json", POOL / "freeze-pool.py", POOL / "check-admission.py",
                             POOL / "offline-mapper-admission.json", POOL / "README.md", ROOT.parent / "scoped-us-table-development-2026-11-19/qualification-contract.json"))
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "execution_authorized": False,
                      "input_count": len(contract["input_sha256"])}))


if __name__ == "__main__":
    main()
