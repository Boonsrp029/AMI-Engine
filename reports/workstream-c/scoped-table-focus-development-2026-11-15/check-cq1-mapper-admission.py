"""Check all frozen CQ1 mapper requests without generation."""
import json
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parent
OLDER = ROOT.parent / "scoped-fact-span-development-2026-11-15"
POOL = ROOT.parent / "cq1-fact-span-pool-2026-11-15"
sys.path.insert(0, str(OLDER))

from check_and_freeze import blocked, digest, encoding, inspect_case, read


def main():
    socket.socket.connect = socket.create_connection = blocked
    contract = read(ROOT / "development-contract.json")
    assert all(digest(name) == expected for name, expected in contract["input_sha256"].items())
    tokenizer = Path(contract["tokenizer_path"])
    assert digest(tokenizer) == contract["tokenizer_sha256"]
    counter = encoding(read(tokenizer))
    plans_path = POOL / "pool/plans-v3-explicit-coverage.json"
    scope_path = POOL / "question-scopes/manifest.json"
    audit = read(POOL / "freeze-audit.json")
    assert digest(plans_path) == audit["plans_sha256"]
    assert digest(scope_path) == audit["scope_manifest_sha256"]
    scopes = read(scope_path)
    plans = read(plans_path)
    previous = read(OLDER / "offline-request-check.json")["roster_mapper_only"]
    assert set(scopes["case_ids"]) == set(plans) == set(previous)
    results = {}
    for cid in scopes["case_ids"]:
        case = plans[cid]
        path = scope_path.parent / scopes["cases"][cid]["path"]
        expected = scopes["cases"][cid]["sha256"]
        assert digest(path) == expected
        inputs = {**case, "corpus_path": str(plans_path.parent / Path(case["corpus_path"]).name),
                  "requested_scopes": str(path), "requested_scopes_sha256": expected}
        result = inspect_case({**contract, "input_sha256": {str(path): expected}}, inputs, counter)["mapping"]
        results[cid] = {**result, "prior_format_schema_tokens": previous[cid]["mapping"]["format_schema_tokens"]}
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "sockets_blocked": True, "model_calls": 0,
                      "checked": len(results), "request_reservation_limit": 4096,
                      "maximum_reservation": max(c["reserved"] for c in results.values()),
                      "changed_schema_token_counts": [cid for cid, c in results.items()
                                                      if c["format_schema_tokens"] != c["prior_format_schema_tokens"]],
                      "cases": results}, indent=2))


if __name__ == "__main__":
    main()
