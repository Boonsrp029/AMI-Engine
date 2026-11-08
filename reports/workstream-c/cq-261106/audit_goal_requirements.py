"""Readiness audit and synthetic admission-lineage probe; zero inference."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
sys.path.insert(0,str(Path.cwd()/"tests"))

from scripts.concurrent_composer_check import check_protocol
from test_subtask_qualification_phase import ledger


ROOT = Path(__file__).resolve().parent
PROTOCOL_SHA = "8da1a51cd9239cd54ec5617dff9d7859ddd39b419cd0d743823eb59d24811b37"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    packet = ROOT/"unit-local-composer-v2"
    p = check_protocol(packet/"protocol-v2.json",PROTOCOL_SHA)
    assert not (packet/"authorization.json").exists() and not (packet/"actual").exists()
    content = json.loads((ROOT/"cq1/manifest.json").read_text(encoding="utf-8"))
    assert all(sha(ROOT/"cq1"/name)==value for name,value in content["sha256"].items())
    plans_manifest = json.loads((ROOT/"cq1/plans-v3-coverage-manifest.json").read_text(encoding="utf-8"))
    assert sha(ROOT/"cq1"/plans_manifest["plans_file"]) == plans_manifest["sha256"]
    assert sha(ROOT/"cq1/manifest.json") == plans_manifest["original_content_manifest_sha256"]
    cases = json.loads((ROOT/"cq1/cases.json").read_text(encoding="utf-8"))
    plans = json.loads((ROOT/"cq1"/plans_manifest["plans_file"]).read_text(encoding="utf-8"))
    assert set(plans)=={case["case_id"] for case in cases}
    assert dict(Counter(c["category"] for c in cases))==content["categories"]
    # Existing maintained fixture supplies synthetic rows/grants only. No start,
    # inference, review acceptance, Store or qualification output is created.
    probe = ROOT/"offline-gate-audit"
    probe.mkdir()
    l = ledger(probe)
    l._verify()
    rows = {Path(c[key]):sha(c[key]) for c in l.contract["development_gate"]["cases"]
            for key in ("result_path","assessment_path")}
    l.contract["pipeline_identity"] = "different-synthetic-pipeline"
    l.contract["development_gate"]["pipeline_identity"] = "different-synthetic-pipeline"
    original = {k:v for k,v in l.contract.items() if k!="contract_sha256"}
    l.contract["contract_sha256"] = hashlib.sha256(json.dumps(original,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    l.grant["contract_sha256"] = l.contract["contract_sha256"]
    l._verify()
    assert all(sha(path)==value for path,value in rows.items())
    assert not l.output.exists()
    check_protocol(packet/"protocol-v2.json",PROTOCOL_SHA)
    audit = {"actual_model_calls":0,"scope":"current Goal requirements, not production qualification",
        "prepared":{"purpose_inputs_model_settings":True,"limits_and_output":True,
            "development_protocol":True,"CQ1_content_and_thresholds":True,"source_review_schema":True},
        "current_composer_protocol_verified":True,"composer_grant_present":False,
        "composer_attempt_present":False,"CQ1_plans_content_verified":True,
        "CQ1_categories":content["categories"],"CQ1_thresholds":content["thresholds"],
        "actual_gates":{"current_composer_quality":"unverified; grant pending",
            "two_case_development_gate":"not passed; prior cq-p01 failed, cq-p02 unattempted",
            "CQ1_quality":"0of20attempted; no applicable grant",
            "owner_adjudication":"pending future assessable outputs and exact qualification bundle"},
        "new_lineage_finding":{"reproduced":True,"synthetic_only":True,
            "description":"QualificationLedger accepts unchanged synthetic passing pair after both declared pipeline identities are changed together; retained development start/contract lineage is not required.",
            "actual_application_runtime_edited":False,"new_qualification_attempts":0,
            "affects_current_composer_only_protocol":False,
            "required_action":"Harden exact development contract/start/result lineage before any CQ1 contract is admitted. Preserve the pending composer protocol."},
        "goal_complete":False,"generation_blocker":"new explicit composer-only grant absent",
        "safe_followup":"Prepare isolated offline qualification-lineage hardening without mutating the pending frozen protocol.",
        "usage":"five-hour reading unavailable"}
    with (ROOT/"goal-requirements-audit.json").open("x",encoding="utf-8") as stream:
        json.dump(audit,stream,indent=2);stream.write("\n")
    print(json.dumps(audit))


if __name__ == "__main__":
    main()
