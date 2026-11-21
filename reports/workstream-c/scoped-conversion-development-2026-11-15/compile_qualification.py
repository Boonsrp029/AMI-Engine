"""Compile the existing CQ1 roster only after this table-focus development batch passes."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
POOL = ROOT.parent / "cq1-conversion-pool-2026-11-15"
EXPECTED_DEVELOPMENT = "799f2d0c43d43242087eb62f0e082568786fd9c12fc1a6a384c8d980bd980e74"

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
        expected_pool_sha256="960ca14353f611dea06066a8cec4b5846f5881935aa80aa16967b67974b92068",
        expected_plans_sha256="af0414a4e5d360df3a6ee64513d5df8ccc639eeac98e38ab2163d4bbca4ad406",
        scope_manifest_path=POOL / "question-scopes/manifest.json",
        expected_scopes_sha256="9504b9314962026d3d53edfd6b5b5c2eaae8d4a018cac57e93e856f1bc7bd412",
        recorded_pool_root=ROOT.parent / "concurrent-qualification-2026-11-06/cq1",
        review_protocol=POOL.parent / "cq1-fact-span-pool-2026-11-15/source-review-protocol.md",
        execution_artifacts=(ROOT / "run_qualification_case.py", Path(__file__),
                             POOL.parent / "cq1-fact-span-pool-2026-11-15/inspect_result.py", POOL / "freeze-audit.json"),
    )
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "execution_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



