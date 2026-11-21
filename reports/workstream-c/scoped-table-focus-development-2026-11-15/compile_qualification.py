"""Compile the existing CQ1 roster only after this table-focus development batch passes."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
POOL = ROOT.parent / "cq1-fact-span-pool-2026-11-15"
EXPECTED_DEVELOPMENT = "b8acd9b2a16b7bea250efa6d8fd15175dcfca91a1a9fedc5f0dc2a2d7d71b382"

sys.path.insert(0, str(POOL))
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
        expected_pool_sha256="ba15b6a0ff830abba031957751626567e766a4a93a92870bdcbcbff15799bfa9",
        expected_plans_sha256="9f0bc227015c44e7045b50cbd1e09ea6210cbfda303d136358e5dbf441a2d8ec",
        scope_manifest_path=POOL / "question-scopes/manifest.json",
        expected_scopes_sha256="810fe2b8b7713134b0c9a5c06bf376d59bd8a0a4cf65627a605604c5d01bcbce",
        recorded_pool_root=ROOT.parent / "concurrent-qualification-2026-11-06/cq1",
        review_protocol=POOL / "source-review-protocol.md",
        execution_artifacts=(ROOT / "run_qualification_case.py", Path(__file__),
                             POOL / "inspect_result.py", POOL / "freeze-audit.json"),
    )
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "execution_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

