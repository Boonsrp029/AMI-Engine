"""Verify retained-case parity and mapper admission for the frozen revised pool."""
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parent
OLDER = ROOT.parent / "scoped-fact-span-development-2026-11-15"
PRIOR = ROOT.parent / "cq1-conversion-pool-2026-11-15"
sys.path.insert(0, str(OLDER))

from check_and_freeze import blocked, digest, encoding, inspect_case, read


def main():
    socket.socket.connect = socket.create_connection = blocked
    audit = read(ROOT / "freeze-audit.json")
    contract = read(OLDER / "development-contract.json")
    tokenizer = Path(contract["tokenizer_path"])
    assert digest(tokenizer) == contract["tokenizer_sha256"]
    counter = encoding(read(tokenizer))
    pool = ROOT / "pool"
    scope = ROOT / "question-scopes"
    manifest = read(pool / "manifest.json")
    plans = read(pool / "plans-v3-explicit-coverage.json")
    scopes = read(scope / "manifest.json")
    assert digest(pool / "manifest.json") == audit["pool_sha256"]
    assert digest(pool / "plans-v3-explicit-coverage.json") == audit["plans_sha256"]
    assert digest(scope / "manifest.json") == audit["scope_manifest_sha256"]
    assert all(digest(pool / name) == sha for name, sha in manifest["sha256"].items())
    prior_rows = {r["case_id"]: r for r in read(PRIOR / "pool/cases.json")}
    new_rows = {r["case_id"]: r for r in read(pool / "cases.json")}
    prior_plans = read(PRIOR / "pool/plans-v3-explicit-coverage.json")
    prior_scopes = read(PRIOR / "question-scopes/manifest.json")["cases"]
    for cid in audit["retained_case_ids"]:
        assert new_rows[cid] == prior_rows[cid] and plans[cid] == prior_plans[cid]
        assert scopes["cases"][cid] == prior_scopes[cid]
    assert scopes["case_ids"] == manifest["case_order"] == list(new_rows) == list(plans)
    results = {}
    for cid, case in plans.items():
        item = scopes["cases"][cid]
        path = scope / item["path"]
        assert digest(path) == item["sha256"]
        inputs = {**case, "corpus_path": str(pool / Path(case["corpus_path"]).name),
                  "requested_scopes": str(path), "requested_scopes_sha256": item["sha256"]}
        results[cid] = inspect_case({**contract, "input_sha256": {str(path): item["sha256"]}},
                                    inputs, counter)["mapping"]
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0, "checks": len(results),
                      "retained_exact_questions_plans_scopes": len(audit["retained_case_ids"]),
                      "largest_mapper_reservation": max(item["reserved"] for item in results.values()),
                      "results": results}, indent=2))


if __name__ == "__main__":
    main()

