"""Compile the revised frozen CQ1 roster after two current actual development passes."""
import argparse
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parent
POOL = ROOT.parent / "cq1-power-quantity-pool-2026-11-20"
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
        expected_identity="1f13d50964bd6b8460ecf4b302ff796326b42e2eeda722ca7df3ef739e3e1a1b",
        pool=POOL / "pool", destination=ROOT / "qualification-contract.json",
        output_directory=ROOT / "actual-cq1", as_of=args.as_of,
        expected_pool_sha256="e848ab337f865155d0219af9263b7f35e1491cf38a7a4cc97425a41d117d65d0",
        expected_plans_sha256="37cf91d0d492599996e1f2b79570fca7634fca57ff364b47f2349a073b1a9ed6",
        scope_manifest_path=POOL / "question-scopes/manifest.json",
        expected_scopes_sha256="2e0ca63f25b1b7092897685dbb627ccc1f40dfaaacfe85534b5e4e0815b2bbe9",
        recorded_pool_root=ROOT.parent / "concurrent-qualification-2026-11-06/cq1",
        review_protocol=SHARED / "source-review-protocol.md",
        execution_artifacts=(ROOT / "run_qualification_case.py", Path(__file__), SHARED / "inspect_result.py",
                             POOL / "freeze-audit.json", POOL / "freeze-pool.py", POOL / "check-admission.py",
                             ROOT / "current-mapper-admission.json", POOL / "README.md"))
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "execution_authorized": False,
                      "input_count": len(contract["input_sha256"])}))


if __name__ == "__main__":
    main()

