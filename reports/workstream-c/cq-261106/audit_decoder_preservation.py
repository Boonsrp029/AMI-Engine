"""Offline preservation and saved-response rejection; never creates a model client."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.pilot._evidence import build_span_catalog
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.generation import selection_schema
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.scheduler import run_plan


ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    changes = {"src/pilot/subtasks/generation.py", "tests/test_subtask_request_coverage.py",
               "scripts/audit_concurrent_context.py"}
    baseline = json.loads((ROOT / "coverage-policy-source-manifest.json").read_text())
    drift = [name for name, sha in baseline.items() if digest(name) != sha]
    assert {name.replace("\\", "/") for name in drift} == changes, drift
    verified = {}
    for folder, manifest in [(ROOT, ROOT / "manifest.json"),
                             (ROOT / "cq1", ROOT / "cq1/manifest.json"),
                             (Path("data/external/release_qualification_2026_10_30_v4/frozen-v4"),
                              Path("data/external/release_qualification_2026_10_30_v4/frozen-v4/manifest.json"))]:
        entries = json.loads(manifest.read_text(encoding="utf-8"))["sha256"]
        for name, sha in entries.items():
            assert digest(folder / name) == sha, name
        verified[str(manifest)] = len(entries)
    r07 = Path("reports/workflow_pilot/production-readiness-2026-10-27/resume-v108/runs/attempt-r07.json")
    assert digest(r07) == "5c09d7eaa6eb1f5c7a6434e531c8d4281af4efe46658f8bcd432aecfc82ebfd9"
    contract = json.loads((ROOT / "development-contract-v5.json").read_text())
    for name in ("requirements.txt", "requirements-serving.txt", "constraints-pilot.txt"):
        assert digest(name) == contract["input_sha256"][str(Path(name).resolve())]
    case = contract["cases"]["cq-p01"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    report = run_plan(plan, "a"*32, "b"*32, LocalBM25Adapter(case["corpus_path"]))
    sources = {r.source.source_id: r.source.model_dump() for r in report.sources}
    schema = selection_schema(build_span_catalog(sources), plan.query, report=report,
                              requirements=case["complete_required_branches"])
    raw_path = ROOT / "actual-development-v4/cq-p01.mapping.raw.json"
    raw_sha = digest(raw_path)
    retained = json.loads(raw_path.read_text())
    try:
        schema.model_validate_json(retained["raw"])
    except ValueError as exc:
        replay = {"rejected": True, "error_type": type(exc).__name__}
    else:
        raise AssertionError("Retained incomplete supported response must reject")
    assert digest(raw_path) == raw_sha
    result = {"generation_calls": 0, "baseline_paths_checked": len(baseline),
        "declared_existing_path_changes": drift, "manifests_verified": verified,
        "r07_unchanged": True, "dependencies_unchanged": True,
        "v5_raw_sha256": raw_sha, "saved_response_replay": replay,
        "qualification": "not established"}
    target = ROOT / "decoder-preservation-audit.json"
    with target.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
