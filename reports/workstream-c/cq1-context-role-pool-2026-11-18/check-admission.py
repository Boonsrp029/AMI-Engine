"""Verify retained parity and bounded mapper requests with sockets blocked."""
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "scoped-fact-span-development-2026-11-15"))
from check_and_freeze import blocked, digest, encoding, inspect_case, read


def main():
    socket.socket.connect = socket.create_connection = blocked
    previous = ROOT.parent / "cq1-signed-table-pool-2026-11-18"
    development = ROOT.parent / "scoped-context-role-development-2026-11-18"
    contract = read(development / "development-contract.json")
    audit = read(ROOT / "freeze-audit.json")
    pool, scopes = ROOT / "pool", ROOT / "question-scopes"
    manifest = read(pool / "manifest.json")
    plans = read(pool / "plans-v3-explicit-coverage.json")
    bundle = read(scopes / "manifest.json")
    assert digest(pool / "manifest.json") == audit["pool_sha256"]
    assert digest(pool / "plans-v3-explicit-coverage.json") == audit["plans_sha256"]
    assert digest(scopes / "manifest.json") == audit["scope_manifest_sha256"]
    assert all(digest(pool / name) == value for name, value in manifest["sha256"].items())
    old_cases = {row["case_id"]: row for row in read(previous / "pool/cases.json")}
    old_plans = read(previous / "pool/plans-v3-explicit-coverage.json")
    old_scopes = read(previous / "question-scopes/manifest.json")["cases"]
    rows = {row["case_id"]: row for row in read(pool / "cases.json")}
    for cid in audit["retained_case_ids"]:
        assert rows[cid] == old_cases[cid] and plans[cid] == old_plans[cid]
        assert bundle["cases"][cid] == old_scopes[cid]
    assert bundle["case_ids"] == manifest["case_order"] == list(rows) == list(plans)
    tokenizer = Path(contract["tokenizer_path"])
    assert digest(tokenizer) == contract["tokenizer_sha256"]
    counter = encoding(read(tokenizer))
    reservations = {}
    for cid, entry in plans.items():
        item = bundle["cases"][cid]
        path = scopes / item["path"]
        assert digest(path) == item["sha256"]
        frozen = {**entry, "corpus_path": str(pool / Path(entry["corpus_path"]).name),
                  "requested_scopes": str(path), "requested_scopes_sha256": item["sha256"]}
        reservations[cid] = inspect_case({**contract, "input_sha256": {str(path): item["sha256"]}},
                                         frozen, counter)["mapping"]
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0,
        "retained_exact_questions_plans_scopes": 18, "checks": len(reservations),
        "largest_mapper_reservation": max(row["reserved"] for row in reservations.values()),
        "results": reservations}, indent=2))


if __name__ == "__main__":
    main()
