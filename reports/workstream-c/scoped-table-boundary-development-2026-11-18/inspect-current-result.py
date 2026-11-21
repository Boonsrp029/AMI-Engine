"""Display one current qualification result and its pinned review sources."""
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
    result = read(output / f"{cid}.result.json")
    stored = result.get("stored_run") or {}
    diagnostics = stored.get("metrics", {}).get("composition_diagnostics", {})
    selected = {sid for claim in (stored.get("draft") or {}).get("claims", []) for sid in claim["source_ids"]}
    print(json.dumps({"execution": {key: result.get(key) for key in
        ("technical_pass", "failure_type", "main_calls", "nemo_invocations", "elapsed_seconds")},
        "wall": read(ROOT / f"wall-clock-{cid}.json"), "status": stored.get("status"),
        "revision": stored.get("revision"), "draft": stored.get("draft"),
        "projection": {key: diagnostics.get(key) for key in ("fallback_unit_ids", "editorial_correction",
            "requested_branch_coverage", "application_rendered_table_rows", "application_rendered_source_fields")},
        "failure_events": [event["payload"] for event in stored.get("events", [])
            if "fail" in event["kind"] or "error" in event["kind"]],
        "reference": next(row for row in read(Path(contract["source_reference_path"])) if row["case_id"] == cid),
        "cited_sources": {sid: value for sid, value in stored.get("sources", {}).items() if sid in selected}}, indent=2))
    for stage in ("mapping", "composition", "safety"):
        path = output / f"{cid}.{stage}.raw.json" if stage != "safety" else output / f"{cid}.safety.json"
        if path.is_file():
            print(stage, json.dumps(read(path)))


if __name__ == "__main__":
    main()
