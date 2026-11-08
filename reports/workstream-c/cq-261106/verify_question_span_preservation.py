"""Read-only preservation checks; save a new report without modifying evidence."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
repo = Path.cwd()
snapshot = root / "title-lineage-2026-11-07/executed-source-snapshot-v7"
manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert all(sha(snapshot / name) == digest for name, digest in manifest["input_sha256"].items())
actual = root / "title-lineage-2026-11-07/actual-development-v7"
assert all(sha(actual / name) == digest for name, digest in manifest["actual_output_sha256"].items())
constraints = {name: sha(repo / name) for name in ("requirements.txt", "requirements-serving.txt", "constraints-pilot.txt")}
assert all(value == manifest["input_sha256"][name] for name, value in constraints.items())
original = repo / "reports/workflow_pilot/production-readiness-2026-10-27/resume-v108/runs/attempt-r07.json"
assert sha(original) == "5c09d7eaa6eb1f5c7a6434e531c8d4281af4efe46658f8bcd432aecfc82ebfd9"
pool = root / "cq1/manifest.json"
assert sha(pool) == "d587da3c69e9edde1e7f2a5ddcc7dcefe402b6532c7d9f0a21a70b256ea6e26b"
plans = root / "cq1/plans-v3-explicit-coverage.json"
assert sha(plans) == "1c67c1fa832acd8f8dab10caafbfaa85b8f24cc7549fc5b6a9355d2310df9f81"
proposal_path = root / "question-span-2026-11-07/mapper-preflight-proposal.json"
proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
assert all(sha(Path(path)) == digest for path, digest in proposal["runtime_inputs"].items())
assert all(sha(Path(path)) == digest for path, digest in proposal["input_sha256"].items())
result = {"snapshot_files_verified": len(manifest["input_sha256"]),
    "original_actual_output_files_verified": len(manifest["actual_output_sha256"]),
    "dependency_constraint_hashes": constraints, "r07_unchanged": True,
    "CQ1_manifest_unchanged": True, "CQ1_plans_unchanged": True,
    "prepared_current_runtime_files_verified": len(proposal["runtime_inputs"]),
    "prepared_request_files_verified": len(proposal["input_sha256"]),
    "actual_generation_calls": 0}
output = root / "question-span-2026-11-07/preservation-check.json"
with output.open("x", encoding="utf-8") as handle:
    handle.write(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
