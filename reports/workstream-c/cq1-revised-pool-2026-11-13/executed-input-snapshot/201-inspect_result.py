"""Display one retained CQ1 result and its frozen source reference for adjudication."""
import argparse
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_id")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    case_id = args.case_id
    contract = read(root / "qualification-contract.json")
    if case_id not in contract["case_ids"]:
        raise ValueError("Unknown case")
    output = Path(contract["output_directory"])
    result = read(output / (case_id + ".result.json"))
    wall = read(root / f"wall-clock-{case_id}.json")
    keys = ("technical_pass", "failure_type", "main_calls", "nemo_invocations", "elapsed_seconds")
    print(json.dumps({k: result[k] for k in keys}, ensure_ascii=False))
    print("wall", json.dumps(wall))
    stored = result.get("stored_run") or {}
    print("status and revision", stored.get("status"), stored.get("revision"))
    if not result["technical_pass"]:
        print("failure events", [event["payload"] for event in stored.get("events", [])
                                 if "fail" in event["kind"] or "error" in event["kind"]])
    print("draft", json.dumps(stored.get("draft"), ensure_ascii=False))
    d = (stored.get("metrics") or {}).get("composition_diagnostics", {})
    print("projection", {k: d.get(k) for k in ("fallback_unit_ids", "editorial_correction",
                                             "public_claim_coverage", "requested_branch_coverage")})
    for stage in ("mapping", "composition"):
        path = output / f"{case_id}.{stage}.raw.json"
        if path.is_file():
            record = read(path)
            print(stage, record.get("raw"), record.get("usage"),
                  (record.get("response_metadata") or {}).get("done_reason"))
    safety = output / f"{case_id}.safety.json"
    if safety.is_file():
        print("NeMo passed", read(safety).get("passed_guardrails"))
    references = Path(contract["source_reference_path"])
    reference = next(row for row in read(references) if row["case_id"] == case_id)
    print("reference", json.dumps(reference, ensure_ascii=False))
    citations = {sid for claim in (stored.get("draft") or {}).get("claims", [])
                 for sid in claim["source_ids"]}
    print("cited source text", {sid: v["content"] for sid, v in (stored.get("sources") or {}).items()
                                if sid in citations})


if __name__ == "__main__":
    main()
