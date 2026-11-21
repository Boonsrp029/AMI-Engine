"""Display compact retained evidence for one current qualification source review."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_bytes())


def main():
    cid = sys.argv[1]
    contract = read(ROOT / "qualification-contract.json")
    assert cid in contract["case_ids"]
    output = Path(contract["output_directory"])
    path = output / f"{cid}.result.json"
    result = read(path)
    stored = result.get("stored_run") or {}
    d = stored.get("metrics", {}).get("composition_diagnostics", {})
    fields = ("technical_pass", "failure_type", "main_calls", "nemo_invocations", "elapsed_seconds")
    sources = stored.get("sources", {})
    assert all(hashlib.sha256(s["content"].encode()).hexdigest() == s["content_sha256"] for s in sources.values())
    print(json.dumps({"execution": {key: result.get(key) for key in fields},
        "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "status": stored.get("status"), "revision": stored.get("revision"), "draft": stored.get("draft"),
        "reference": next(row for row in read(Path(contract["source_reference_path"])) if row["case_id"] == cid),
        "projection": {key: d.get(key) for key in ("fallback_unit_ids", "editorial_correction",
            "requested_branch_coverage", "application_rendered_table_rows", "application_rendered_source_fields")},
        "resolved_evidence": d.get("resolved_evidence_mapping"),
        "failure_events": [event["payload"] for event in stored.get("events", [])
            if "fail" in event["kind"] or "error" in event["kind"]]}, indent=2))
    for stage in ("mapping", "composition"):
        p = output / f"{cid}.{stage}.raw.json"
        if p.exists():
            value = read(p)
            print(stage, json.dumps({key: value.get(key) for key in ("raw", "usage")}))
    safety = output / f"{cid}.safety.json"
    if safety.exists():
        print("safety", json.dumps(read(safety)))


if __name__ == "__main__":
    main()
