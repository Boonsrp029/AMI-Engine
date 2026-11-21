"""Compile the revised frozen CQ1 roster after two current actual development passes."""
import argparse
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parent
POOL = ROOT.parent / "cq1-context-role-pool-2026-11-18"
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
        expected_identity="7e076a0f6736975913e143b58f3d868aa94db9dd739cf84d5fd4941b692efe1d",
        pool=POOL / "pool", destination=ROOT / "qualification-contract.json",
        output_directory=ROOT / "actual-cq1", as_of=args.as_of,
        expected_pool_sha256="fb01cfe126d18cfa295f4f3856d34e760eb2cf1850a3ee8a07dec44a0ad9e240",
        expected_plans_sha256="93840600703bbd0e42974bd5dae02733bd617a06c8abcc42a246998cafb9c287",
        scope_manifest_path=POOL / "question-scopes/manifest.json",
        expected_scopes_sha256="ce9ada25059e799bba30a68999cb2b74d54a6bd86a6261cc1ddc43e14194805e",
        recorded_pool_root=ROOT.parent / "concurrent-qualification-2026-11-06/cq1",
        review_protocol=SHARED / "source-review-protocol.md",
        execution_artifacts=(ROOT / "run_qualification_case.py", Path(__file__), SHARED / "inspect_result.py",
                             POOL / "freeze-audit.json", POOL / "freeze-pool.py", POOL / "check-admission.py",
                             ROOT / "pool-admission.json", POOL / "README.md"))
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "execution_authorized": False,
                      "input_count": len(contract["input_sha256"])}))


if __name__ == "__main__":
    main()
