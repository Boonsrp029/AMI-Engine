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
        development_path=WORKSTREAM / "scoped-table-selection-development-2026-11-13" / "development-contract.json",
        expected_identity="bd4c66afabf91cacbcc77139162f95eef227b704bc68c52dacd516a653f0ec95",
        pool=ROOT / "pool",
        destination=ROOT / "qualification-contract.json",
        output_directory=ROOT / "actual-cq1",
        as_of=args.as_of,
        expected_pool_sha256="ce574566207e9dfe505890552e580534c822c46b2ee1bcb8f221fc78cc03e5e4",
        expected_plans_sha256="543c1ad27fb0818feaee1074f827729022277e6a35bc415ec18f7d464ad6741f",
        scope_manifest_path=ROOT / "question-scopes" / "manifest.json",
        expected_scopes_sha256="e9698c6ea37aaf72e50191ec58f3c5b7b61f23af612d38e68e25b9e3d3bc9f5c",
        recorded_pool_root=WORKSTREAM / "concurrent-qualification-2026-11-06" / "cq1",
        review_protocol=ROOT / "source-review-protocol.md",
        execution_artifacts=(
            ROOT / "run_case.py", ROOT / "inspect_result.py",
            ROOT / "check_mapping_context.py", ROOT / "table-selection-mapping-context-check.json",
            ROOT / "freeze-audit.json", Path(__file__),
        ),
    )
    print(json.dumps({"contract_sha256": contract["contract_sha256"],
                      "pinned_files": len(contract["input_sha256"]), "execution_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
