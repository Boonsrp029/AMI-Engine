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
        development_path=WORKSTREAM / "scoped-direct-evidence-development-2026-11-13" / "development-contract.json",
        expected_identity="264d7b2f3f49ec88424dd726d0804dc7787c618b6e0c02a6f18d159e7d5f1472",
        pool=ROOT / "pool",
        destination=ROOT / "qualification-contract.json",
        output_directory=ROOT / "actual-cq1",
        as_of=args.as_of,
        expected_pool_sha256="ba15b6a0ff830abba031957751626567e766a4a93a92870bdcbcbff15799bfa9",
        expected_plans_sha256="9f0bc227015c44e7045b50cbd1e09ea6210cbfda303d136358e5dbf441a2d8ec",
        scope_manifest_path=ROOT / "question-scopes" / "manifest.json",
        expected_scopes_sha256="810fe2b8b7713134b0c9a5c06bf376d59bd8a0a4cf65627a605604c5d01bcbce",
        recorded_pool_root=WORKSTREAM / "concurrent-qualification-2026-11-06" / "cq1",
        review_protocol=ROOT / "source-review-protocol.md",
        execution_artifacts=(
            ROOT / "run_case.py", ROOT / "inspect_result.py",
            ROOT / "check_mapping_context.py", ROOT / "direct-evidence-mapping-context-check.json",
            ROOT / "freeze-audit.json", Path(__file__),
        ),
    )
    print(json.dumps({"contract_sha256": contract["contract_sha256"],
                      "pinned_files": len(contract["input_sha256"]), "execution_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


