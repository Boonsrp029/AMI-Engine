"""Freeze a one-request composer protocol; never creates an authorization file."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))

from scripts._concurrent_composer_capture import sha
from scripts.concurrent_composer_check import LIMITS, REQUIRED_PROJECT_FILES


ROOT = Path(__file__).resolve().parent


def main():
    project = Path.cwd()
    folder = ROOT / "unit-local-composer-v2"
    old = json.loads((ROOT / "development-contract-v6.json").read_text(encoding="utf-8"))
    expected = json.loads((folder / "capture.json").read_text(encoding="utf-8"))["input_identity"]
    names = set(old["input_sha256"])
    names.update(str(project/name) for name in REQUIRED_PROJECT_FILES)
    names.update(str(project/name) for name in ["src/pilot/subtasks/_composition_instruction.py",
        "scripts/_concurrent_composer_capture.py", "scripts/concurrent_composer_check.py",
        "tests/test_concurrent_composer_capture.py", "tests/test_concurrent_composer_check.py",
        "tests/test_subtask_composition_instruction.py"])
    project_files = {Path(name).resolve().relative_to(project).as_posix():sha(name) for name in sorted(names)}
    # Reassert preservation; only the declared concurrent source/test differences
    # from v6 may exist before taking the new identity.
    changed = {Path(name).resolve().relative_to(project).as_posix() for name,h in old["input_sha256"].items() if sha(name)!=h}
    assert changed == {"src/pilot/subtasks/generation.py", "tests/test_subtask_request_coverage.py"}, changed
    for name,h in json.loads((ROOT / "v6-diagnostic-findings.json").read_text(encoding="utf-8"))["evidence_sha256"].items():
        assert sha(ROOT / "actual-development-v5" / name) == h
    protocol = {"kind":"concurrent-composer-only-v1", "status":"prepared; new user grant required",
        "purpose":"Test unit-local free prose against the retained correct cq-p01 mapping, without mapper generation, safety or persistence",
        "model":old["model_snapshot"]["model"], "model_digest":old["model_snapshot"]["digest"],
        "model_settings":old["settings"], "composition_version":"cq-composer-v2-unit-local",
        "case_id":"cq-p01", "limits":LIMITS, "output_directory":"actual",
        "input":"input.json", "native_body":"native-body.json",
        "native_body_sha256":sha(folder/"native-body.json"),
        "authorization_reply":"Authorize one concurrent composer-v2 diagnostic",
        "frozen_contract":(ROOT/"development-contract-v6.json").relative_to(project).as_posix(),
        "frozen_mapping":(ROOT/"actual-development-v5/cq-p01.mapping.raw.json").relative_to(project).as_posix(),
        "replay_identity":expected,"project_files":project_files,
        "files":{name:sha(folder/name) for name in ("input.json","native-body.json","capture.json",
            "retained-failure-replay.json","context-audit.json","manifest.json")},
        "acceptance":["One raw claim per evidence unit, correctly reporting both available facts and periods.",
            "Retain Canada observed5.7percent2016 and Japan projected2.6percentannuallythrough2036 in their respective units.",
            "No unsupported relative difference, level/rate comparison, cross-unit number/date/geography/basis transfer or omitted requested fact.",
            "Record raw support/completeness separately from application fallback; no editorial rescue.",
            "Technical pass requires normal completion, pinned identity before/after, matching request and strict application validation.",
            "Assistant source review required; owner source/wording acceptance remains pending. No safety or stored approval is established."],
        "stop":"Once only. Close at any timeout, transport/identity/context/parse/validation/source/completeness failure; no retry or tuning inside the attempt.",
        "excluded":["mapper generation","NeMo","full workflow","cq-p02","CQ1","Ragas","hosted inference","approval/export","publication/deployment"],
        "freshness":"Consumed development evidence only; this is not unseen qualification success.",
        "usage":"Five-hour reading unavailable. Prior interrupted/backend internal token use and hardware/monetary cost remain unknown."}
    # The first preparation is retained: inspection correctly rejected its
    # missing service-helper pin. No service/inference was started.
    path = folder / "protocol-v2.json"
    with path.open("x",encoding="utf-8") as stream:
        json.dump(protocol,stream,ensure_ascii=False,indent=2);stream.write("\n")
    print(json.dumps({"protocol_sha256":sha(path), "project_files":len(project_files), "execution_authorized":False}))


if __name__ == "__main__":
    main()
