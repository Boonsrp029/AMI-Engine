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
        development_path=WORKSTREAM / "scoped-aggregate-subject-development-2026-11-13" / "development-contract.json",
        expected_identity="92160912e8529b6989a5c5824afe6f92b7ffc0ff91b49108134935cf9c66e1a7",
        pool=ROOT / "pool",
        destination=ROOT / "qualification-contract.json",
        output_directory=ROOT / "actual-cq1",
        as_of=args.as_of,
        expected_pool_sha256="57f938480032eccc02af088766e6b76247b1cd6f7d1b4c8acbae5f42e28296ad",
        expected_plans_sha256="8a0cd19b7ec4cb77bc20a3ef69e1c3b2d8a4d96b48e772f25d42650773512fd3",
        scope_manifest_path=ROOT / "question-scopes" / "manifest.json",
        expected_scopes_sha256="05da72c707bd24f814727e1dd6cc6e2776985be9aa332db0aa8ce7b04cec80d5",
        recorded_pool_root=WORKSTREAM / "concurrent-qualification-2026-11-06" / "cq1",
        review_protocol=ROOT / "source-review-protocol.md",
        execution_artifacts=(
            ROOT / "run_case.py", ROOT / "inspect_result.py",
            ROOT / "check_mapping_context.py", ROOT / "aggregate-subject-mapping-context-check.json",
            ROOT / "freeze-audit.json", Path(__file__),
        ),
    )
    print(json.dumps({"contract_sha256": contract["contract_sha256"],
                      "pinned_files": len(contract["input_sha256"]), "execution_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

