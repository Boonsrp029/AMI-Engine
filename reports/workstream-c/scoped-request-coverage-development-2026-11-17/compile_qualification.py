"""Compile the existing CQ1 roster only after this request coverage development batch passes."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
POOL = ROOT.parent / "cq1-coverage-pool-2026-11-17"
EXPECTED_DEVELOPMENT = "38d7ee82c6dbb35588ed29f1b1b36941b8b78f608a5ecee5d6acf78940fdaad3"

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
        expected_pool_sha256="a5dc54e22ee4ce01c16bc9b4992f16dba9c4497ae448764d5bf28feb0b7576f7",
        expected_plans_sha256="aed1d36d752a47b0e89f4e194db4e337ec2a908f9771e26d525f3fe7cf461063",
        scope_manifest_path=POOL / "question-scopes/manifest.json",
        expected_scopes_sha256="a3392ace284fce41644b1b4655d887d4d0622f42c102b5307bff6c6d7ba59543",
        recorded_pool_root=ROOT.parent / "concurrent-qualification-2026-11-06/cq1",
        review_protocol=POOL.parent / "cq1-fact-span-pool-2026-11-15/source-review-protocol.md",
        execution_artifacts=(ROOT / "run_qualification_case.py", Path(__file__),
                             POOL.parent / "cq1-fact-span-pool-2026-11-15/inspect_result.py", POOL / "freeze-audit.json"),
    )
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "execution_authorized": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())








