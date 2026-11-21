"""Account for all actual attempts after the frozen stop condition."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from src.pilot.subtasks.quality_review import summarize


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    contract = read(ROOT / "qualification-contract.json")
    output = Path(contract["output_directory"])
    attempts, reviews, usage, walls = {}, {}, {}, {}
    for cid in contract["case_ids"]:
        path = output / f"{cid}.result.json"
        if not path.exists():
            assert not (output / f"{cid}.started.json").exists()
            continue
        attempts[cid] = {**read(path), "result_sha256": digest(path)}
        assessment = output / f"{cid}.assessment.json"
        if assessment.exists():
            reviews[cid] = read(assessment)
        usage[cid] = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        for stage in ("mapping", "composition"):
            capture = output / f"{cid}.{stage}.raw.json"
            if capture.exists():
                for key, value in read(capture)["usage"].items():
                    usage[cid][key] += value
        walls[cid] = read(ROOT / f"wall-clock-{cid}.json")["elapsed_seconds"]
    summary = summarize(contract["roster"], attempts, reviews)
    assert summary["stop"] == {"case_id": "cq1-a40", "reason": "technical failure"}
    assert len(summary["attempted_ids"]) == 2 and len(summary["unattempted_ids"]) == 18
    assert (output / "stopped.json").exists()
    summary.update(contract_sha256=contract["contract_sha256"], allowance_status="closed at failure",
        attempted_count=2, technical_pass_count=1, technical_failure_count=1,
        main_calls=sum(row["main_calls"] for row in attempts.values()),
        nemo_invocations=sum(row["nemo_invocations"] for row in attempts.values()),
        capture_reported_main_tokens=sum(row["total_tokens"] for row in usage.values()),
        usage_by_case=usage, owned_wall_seconds=walls, internal_nemo_usage="unmeasured", monetary_cost="unmeasured",
        result_sha256={cid: row["result_sha256"] for cid, row in attempts.items()},
        development_editorial_acceptance="Owner accepted both U.S.-explicit development copies in owner-acceptance-development.json; separate from qualification.")
    with (ROOT / "qualification-batch-summary.json").open("x", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: summary[key] for key in ("attempted_count", "technical_pass_count",
        "technical_failure_count", "main_calls", "nemo_invocations", "capture_reported_main_tokens", "stop")}))


if __name__ == "__main__":
    main()
