"""Persist explicit assistant findings and flags; performs no scoring inference."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.qualification_phase import QualificationLedger
from src.pilot.subtasks.quality_review import SourceReview


def read(path):
    return json.loads(path.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case")
    for name in ("raw-supported", "raw-complete"):
        parser.add_argument("--" + name, required=True, choices=("yes", "no", "unknown"))
    for name in ("supported", "complete"):
        parser.add_argument("--" + name, required=True, choices=("yes", "no"))
    parser.add_argument("--critical", required=True, type=int)
    parser.add_argument("--finding", action="append", required=True)
    parser.add_argument("--abstention", action="store_true")
    parser.add_argument("--conflict", action="store_true")
    parser.add_argument("--safe-injection", action="store_true")
    args = parser.parse_args()
    contract, grant = read(ROOT / "qualification-contract.json"), read(ROOT / "qualification-grant.json")
    output = Path(contract["output_directory"])
    path = output / f"{args.case}.result.json"
    result = read(path)
    assert result["technical_pass"] is True
    diagnostics = result["stored_run"]["metrics"].get("composition_diagnostics", {})
    values = {"yes": True, "no": False, "unknown": None}
    review = SourceReview.model_validate({"result_sha256": digest(path), "assessor": "assistant",
        "source_findings": args.finding, "critical_errors": args.critical,
        "raw_supported": values[args.raw_supported], "raw_complete": values[args.raw_complete],
        "final_supported": values[args.supported], "final_complete": values[args.complete],
        "proper_abstention": args.abstention, "explicit_conflict": args.conflict,
        "safe_injection": args.safe_injection, "fallback_used": bool(diagnostics.get("fallback_unit_ids")),
        "editorial_correction_used": bool(diagnostics.get("editorial_correction")),
        "owner_verdict": "pending", "owner_reference": ""})
    with (ROOT / f"{args.case}-qualification-assessment.json").open("x", encoding="utf-8") as handle:
        json.dump(review.model_dump(), handle, indent=2)
        handle.write("\n")
    QualificationLedger(output, contract, grant).assess(args.case, review.model_dump())
    summary = read(output / f"{args.case}.summary.json")
    print(json.dumps({"case": args.case, "category_pass_counts": summary["category_pass_counts"],
                      "attempted": len(summary["attempted_ids"]), "stop": summary["stop"]}))


if __name__ == "__main__":
    main()
