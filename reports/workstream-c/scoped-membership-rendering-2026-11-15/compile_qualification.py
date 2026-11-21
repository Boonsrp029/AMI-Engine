"""Compile the existing CQ1 roster only after this membership rendering development batch passes."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
POOL = ROOT.parent / "cq1-membership-pool-2026-11-15"
EXPECTED_DEVELOPMENT = "2ada51ceb758383322525cd7d73770838827eee380b85cf85d58ba31a8a52769"

sys.path.insert(0, str(POOL.parent / "cq1-fact-span-pool-2026-11-15"))
from build_qualification import build


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True, help="Prospective qualification date in Bangkok")
    args = parser.parse_args()
    contract = build(
        development_path=ROOT / "development-contract.json",
        expected_identity=EXPECTED_DEVELOPMENT,
        pool=POOL / "pool",
        destination=ROOT / "qualification-contract.json",
        output_directory=ROOT / "actual-cq1",
        as_of=args.as_of,
        expected_pool_sha256="173736c2cd8855cf3a4d47e0ed8722a1622b0b46d599449c4edbc2b15dbfae52",
        expected_plans_sha256="f2edc3943429c1550e17632db6c612d213a9268e89dca00006d09d21714ac76e",
        scope_manifest_path=POOL / "question-scopes/manifest.json",
        expected_scopes_sha256="643fe875fb799ab9c2d06b87e35b7dc0ddc539b96307a402f337b98f723c98a3",
        recorded_pool_root=ROOT.parent / "concurrent-qualification-2026-11-06/cq1",
        review_protocol=POOL.parent / "cq1-fact-span-pool-2026-11-15/source-review-protocol.md",
        execution_artifacts=(ROOT / "run_qualification_case.py", Path(__file__),
                             POOL.parent / "cq1-fact-span-pool-2026-11-15/inspect_result.py", POOL / "freeze-audit.json"),
    )
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "execution_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())







