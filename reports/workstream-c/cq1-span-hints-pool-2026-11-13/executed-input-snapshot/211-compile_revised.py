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
        development_path=WORKSTREAM / "scoped-span-hints-development-2026-11-13" / "development-contract.json",
        expected_identity="4839470efadb458f37d04e55f3df8d8bc21e2bb482265f257bf0c3cec5d5c269",
        pool=ROOT / "pool",
        destination=ROOT / "qualification-contract.json",
        output_directory=ROOT / "actual-cq1",
        as_of=args.as_of,
        expected_pool_sha256="9bc3ac6ab7ef2dbeb76e94cc5ca8f89b4b36c8125cc027f91042da6946c78e6f",
        expected_plans_sha256="7734b2c1a65ab9622ca2d3d4984140c0acab255a7c76f8029a641828c9b1e461",
        scope_manifest_path=ROOT / "question-scopes" / "manifest.json",
        expected_scopes_sha256="e7167eca3a6341cc086ebf977ee76c72ab53cd2158a65784b8df072e89b55734",
        recorded_pool_root=WORKSTREAM / "concurrent-qualification-2026-11-06" / "cq1",
        review_protocol=ROOT / "source-review-protocol.md",
        execution_artifacts=(
            ROOT / "run_case.py", ROOT / "inspect_result.py",
            ROOT / "check_mapping_context.py", ROOT / "span-hints-mapping-context-check.json",
            ROOT / "freeze-audit.json", Path(__file__),
        ),
    )
    print(json.dumps({"contract_sha256": contract["contract_sha256"],
                      "pinned_files": len(contract["input_sha256"]), "execution_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
