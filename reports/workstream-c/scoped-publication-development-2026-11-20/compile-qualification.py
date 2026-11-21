"""Compile the revised frozen CQ1 roster after two current actual development passes."""
import argparse
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parent
POOL = ROOT.parent / "cq1-publication-pool-2026-11-20"
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
        expected_identity="caa4ac9a435bc5efd3f0d83b0f73ccb61484446ff35acbfb0bd3d39899f808b0",
        pool=POOL / "pool", destination=ROOT / "qualification-contract.json",
        output_directory=ROOT / "actual-cq1", as_of=args.as_of,
        expected_pool_sha256="df37e3ab92d3f447dfe249cef0666cb9b9a8da27003208bc7ee2312ad9d96974",
        expected_plans_sha256="d335bca4e41ddffc83482b1c2b7481fbd8c42bfb3b5cab996608539f52a6dcf5",
        scope_manifest_path=POOL / "question-scopes/manifest.json",
        expected_scopes_sha256="fb9e1c1071d118758a985246ee47fb6456e05d921948dc6a4dcf7fe9ff115a12",
        recorded_pool_root=ROOT.parent / "concurrent-qualification-2026-11-06/cq1",
        review_protocol=SHARED / "source-review-protocol.md",
        execution_artifacts=(ROOT / "run_qualification_case.py", Path(__file__), SHARED / "inspect_result.py",
                             POOL / "freeze-audit.json", POOL / "freeze-pool.py", POOL / "check-admission.py",
                             POOL / "offline-mapper-admission.json", POOL / "README.md"))
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "execution_authorized": False,
                      "input_count": len(contract["input_sha256"])}))


if __name__ == "__main__":
    main()
