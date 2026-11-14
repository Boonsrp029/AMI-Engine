"""Compile the frozen revised CQ1 package once current development passes."""
import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
WORKSTREAM = ROOT.parent
sys.path.insert(0, str(WORKSTREAM / "cq-261106" / "qualification-builder"))

from build_qualification import build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True, help="Explicit Bangkok date for the prospective run")
    args = parser.parse_args()
    contract = build(
        development_path=WORKSTREAM / "scoped-opposition-development-2026-11-12" / "development-contract.json",
        expected_identity="d98bca1799af0758aaae8484f1f1658fe713bc1bb1d530adfe7932209fc0521a",
        pool=ROOT / "pool",
        destination=ROOT / "qualification-contract.json",
        output_directory=ROOT / "actual-cq1",
        as_of=args.as_of,
        expected_pool_sha256="239bb977e85fbf2240b98c3d65255aeba6c9636bb824446a90f24dc1e60854d2",
        expected_plans_sha256="6e136e6062388814a2541d328eef1e6b39a52676fe69cef6df3a6dfe621a5231",
        scope_manifest_path=ROOT / "question-scopes" / "manifest.json",
        expected_scopes_sha256="ffe04190ba301e256e69fb012b5d1ab14f817dd0fc884ea94d6079a9d9dbba52",
        recorded_pool_root=WORKSTREAM / "concurrent-qualification-2026-11-06" / "cq1",
        review_protocol=ROOT / "source-review-protocol.md",
        execution_artifacts=(
            ROOT / "run_case.py", ROOT / "inspect_result.py",
            ROOT / "offline-mapping-context.json", ROOT / "freeze-audit.json", Path(__file__),
        ),
    )
    print(json.dumps({"contract_sha256": contract["contract_sha256"],
                      "pinned_files": len(contract["input_sha256"]), "execution_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
