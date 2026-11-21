"""Compile the revised frozen CQ1 roster after two current actual development passes."""
import argparse
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parent
POOL = ROOT.parent / "cq1-signed-table-pool-2026-11-18"
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
        development_path=ROOT / "development-contract.json",
        expected_identity="9419020bb5eb9bef8a46af3baef5dae583cd1d7342fad08f1ac6e8b64ee9b459",
        pool=POOL / "pool", destination=ROOT / "qualification-contract.json",
        output_directory=ROOT / "actual-cq1", as_of=args.as_of,
        expected_pool_sha256="5ae1609af2d436826f838ea457666ec378cefaf7f089ec741cd11bd6cf184da1",
        expected_plans_sha256="75ceb1a0fbed6806eb0d331b04d16c1229a2ea20eddfddcba3cffe8e39c0ae31",
        scope_manifest_path=POOL / "question-scopes/manifest.json",
        expected_scopes_sha256="8bda3f9419f74f66a645e64a2f370d5e1b7e5ca29e10f2bd88bb528cd74a5d70",
        recorded_pool_root=ROOT.parent / "concurrent-qualification-2026-11-06/cq1",
        review_protocol=SHARED / "source-review-protocol.md",
        execution_artifacts=(ROOT / "run_qualification_case.py", Path(__file__), SHARED / "inspect_result.py",
                             POOL / "freeze-audit.json", POOL / "freeze-pool.py", POOL / "check-admission.py",
                             POOL / "offline-mapper-admission.json", ROOT / "owner-acceptance-development.json",
                             ROOT / "editorial-proposals.json"))
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "execution_authorized": False,
                      "input_count": len(contract["input_sha256"])}))


if __name__ == "__main__":
    main()
