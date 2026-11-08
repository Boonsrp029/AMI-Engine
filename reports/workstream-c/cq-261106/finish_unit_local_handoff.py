"""Final offline evidence audit; does not create a grant or start inference."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))

from scripts.concurrent_composer_check import check_protocol


ROOT = Path(__file__).resolve().parent
DIGEST = "8da1a51cd9239cd54ec5617dff9d7859ddd39b419cd0d743823eb59d24811b37"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    folder = ROOT / "unit-local-composer-v2"
    protocol = check_protocol(folder/"protocol-v2.json",DIGEST)
    assert "1583 passed, 14 warnings in 463.42s" in (ROOT/"unit-local-full.txt").read_text(encoding="utf-8")
    assert "6 passed in 4.62s" in (ROOT/"concurrent-composer-controller-tests.txt").read_text(encoding="utf-8")
    validated = json.loads((folder/"offline-validation/validation-result.json").read_text(encoding="utf-8"))
    assert validated["status"].startswith("validated;") and validated["network_blocked"] is True
    assert validated["actual_model_calls"] == validated["nemo_invocations"] == 0
    assert not (folder/"actual").exists() and not (folder/"authorization.json").exists()
    for label in ("v5","v6"):
        findings = json.loads((ROOT/f"{label}-diagnostic-findings.json").read_text(encoding="utf-8"))
        actual = ROOT / ("actual-development-v4" if label=="v5" else "actual-development-v5")
        assert all(sha(actual/name)==value for name,value in findings["evidence_sha256"].items())
    for base in (ROOT,ROOT/"cq1",Path("data/external/release_qualification_2026_10_30_v4/frozen-v4")):
        manifest = json.loads((base/"manifest.json").read_text(encoding="utf-8"))
        assert all(sha(base/name)==value for name,value in manifest["sha256"].items())
    assert sha("reports/workflow_pilot/production-readiness-2026-10-27/resume-v108/runs/attempt-r07.json") == "5c09d7eaa6eb1f5c7a6434e531c8d4281af4efe46658f8bcd432aecfc82ebfd9"
    old = json.loads((ROOT/"development-contract-v6.json").read_text(encoding="utf-8"))
    for name in ("requirements.txt","requirements-serving.txt","constraints-pilot.txt","src/pilot/_evidence.py","src/pilot/engine.py"):
        assert sha(name)==old["input_sha256"][str(Path(name).resolve())]
    audit = {"status":"offline preparation ready; actual quality unverified; new grant absent",
        "application_capture_suite":"1583passed14warnings463.42seconds;terminalexit0",
        "later_controller_checks":"6passed4.62seconds;separate from1583",
        "targeted_instruction_runner_checks":62,"capture_checks":7,
        "protocol_sha256":DIGEST,"project_inputs_checked":len(protocol["project_files"]),
        "request_artifacts_checked":len(protocol["files"]),"actual_model_calls_this_pass":0,
        "standalone_socket_blocked_validation":"passed synthetic fixed response; not inference",
        "failed_v5_v6_artifacts_unchanged":True,"r07_and_reserved_sources_unchanged":True,
        "dependencies_and_sequential_prompt_unchanged":True,
        "human_adjudication":"pending new assessable output; no technical rescoring requested",
        "production_qualification":"not established","usage":"five-hour reading unavailable"}
    with (ROOT/"unit-local-final-audit.json").open("x",encoding="utf-8") as stream:
        json.dump(audit,stream,indent=2);stream.write("\n")
    handoff = json.loads((ROOT/"handoff.json").read_text(encoding="utf-8"))
    handoff.update(status="unit_local_composer_prepared_requires_new_single_request_grant",
        offline_unit_local=audit,active_full_suite_session=None,
        active_full_suite_log="reports/workstream-c/concurrent-qualification-2026-11-06/unit-local-full.txt",
        full_suite=audit["application_capture_suite"],prepared_composer_protocol=DIGEST,
        next=["No generation until an explicit grant matching authorization-packet-composer-v2.md exists; all prior allowances remain closed.",
              "Reverify corrected protocol-v2.json/current119inputs. Do not use the rejected initial protocol.json.",
              "If granted, record the actual user reference in a separate authorization.json; never infer authorization from prepared artifacts.",
              "Run scripts.concurrent_composer_check execute once: at most1localcomposerrequest,95seconds,zeroNeMo/no retries. No workflow/CQ1 is authorized.",
              "Inspect raw source support/completeness separately from fallback before any new workflow proposal. Owner source/wording review applies only to an assessable result."],
        authorization={"prior_batches":"closed","new_composer_grant":None})
    (ROOT/"handoff.json").write_text(json.dumps(handoff,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(audit))


if __name__ == "__main__":
    main()
