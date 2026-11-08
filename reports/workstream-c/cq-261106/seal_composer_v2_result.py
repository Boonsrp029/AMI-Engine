"""Seal the one actual composer result and assistant source assessment."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from scripts.concurrent_composer_check import check_protocol


ROOT=Path(__file__).resolve().parent
PACKET=ROOT/"unit-local-composer-v2"
DIGEST="8da1a51cd9239cd54ec5617dff9d7859ddd39b419cd0d743823eb59d24811b37"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    with path.open("x",encoding="utf-8") as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write("\n")


def main():
    protocol=check_protocol(PACKET/"protocol-v2.json",DIGEST)
    actual=PACKET/"actual"
    summary=json.loads((actual/"summary.json").read_text(encoding="utf-8"))
    service=json.loads((actual/"service/service-result.json").read_text(encoding="utf-8"))
    validation=json.loads((actual/"validation/validation-result.json").read_text(encoding="utf-8"))
    assert summary["model_calls_started"]==1 and summary["nemo_invocations"]==0
    assert summary["retry_performed"] is False and summary["elapsed_budget_exceeded"] is False
    assert service["identity_before"] is True and service["identity_after"] is True
    assert service["finish"]["done_reason"]=="stop" and service["response_complete"] is True
    assert validation["status"].startswith("validated;") and validation["network_blocked"] is True
    replay=validation["replay"]
    assert replay["diagnostics"]["fallback_unit_ids"]==[] and replay["diagnostics"]["editorial_correction"] is False
    inputs=json.loads(replay["captured"]["messages"][1]["content"])
    units={u["unit_id"]:u for u in inputs["units"]}
    raw=json.loads(service["content"])
    assert len(raw["claims"])==len(units)==2
    findings=[]
    for claim in raw["claims"]:
        unit=units[claim["unit_id"]]
        assert claim["text"]==unit["evidence"][0]["quote"]
        findings.append({"unit_id":claim["unit_id"],"text":claim["text"],
            "source_id":unit["evidence"][0]["source_id"],"support":"exact supplied synthetic quotation",
            "requested_measure_period_geography_basis":"retained","unsupported_relative_comparison":False})
    assert replay["draft"]["title"]=="Analyst research brief (Canada)"
    assert any("Japan" in c["text"] for c in replay["draft"]["claims"])
    archive=PACKET/"executed-source-snapshot"
    archive.mkdir()
    identities={}
    for name,expected in protocol["project_files"].items():
        relative=Path(name)
        assert not relative.is_absolute() and ".." not in relative.parts and ".git" not in relative.parts
        assert ".env" not in relative.name
        source=Path(name)
        assert sha(source)==expected
        target=archive/"project"/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(source.read_bytes())
        assert sha(target)==expected
        identities[name]=expected
    request_hashes={}
    for name,expected in protocol["files"].items():
        target=archive/"request"/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((PACKET/name).read_bytes());assert sha(target)==expected
        request_hashes[name]=expected
    (archive/"protocol-v2.json").write_bytes((PACKET/"protocol-v2.json").read_bytes())
    outputs={p.relative_to(actual).as_posix():sha(p) for p in actual.rglob("*") if p.is_file()}
    write(archive/"manifest.json",{"project_files":identities,"request_files":request_hashes,
        "protocol_sha256":DIGEST,"actual_output_sha256":outputs})
    assessment={"status":"assistant-authored; owner adjudication pending","case_id":"cq-p01",
        "scope":"one actual composer request over retained synthetic mapper evidence; not a workflow or qualification",
        "protocol_sha256":DIGEST,"model_identity_verified_before_after":True,
        "technical_gate_pass":True,"raw_supported":True,"raw_complete":True,
        "raw_claim_findings":findings,"application_claims_supported":True,"application_claims_complete":True,
        "raw_title":"Analyst research brief","application_title":replay["draft"]["title"],
        "application_title_scope_pass":False,"overall_final_output_gate_pass":False,
        "application_issue":"Single-country Canada label does not describe the explicitly two-country Canada/Japan brief. Inherited mapper geography covers only the Canada source.",
        "fallback_used":False,"editorial_correction_used":False,
        "main_requests":1,"nemo_invocations":0,"usage":service["usage"],
        "elapsed_seconds":summary["elapsed_seconds"],"internal_service_complete":True,
        "guardrail_safety":"not executed by design","persisted_workflow":"none by design",
        "stored_approvals":0,"exports_created":0,"grant_state":"closed; one request consumed; no retries or workflows",
        "owner_acceptance":"pending for source/wording; no approval/export",
        "freshness":"consumed development evidence; no unseen or matched-improvement claim",
        "cost":"monetary/hardware unmeasured","outputs_sha256":outputs,
        "source_snapshot":"executed-source-snapshot/manifest.json",
        "next":"Offline application title-scope coverage repair; preserve raw/source evidence and strict validation. Integrate future lineage candidate only after re-freezing affected future packages."}
    write(PACKET/"result-assessment.json",assessment)
    h=json.loads((ROOT/"handoff.json").read_text(encoding="utf-8"))
    h.update(status="composer_v2_actual_complete_raw_pass_application_title_scope_failed_grant_closed",
        latest_composer_actual=assessment,active_diagnostic_session=None,
        authorization={"prior_batches":"closed","composer_v2":"closed;1requestused;no workflow authorized"},
        next=["No more generation under the consumed one-request composer grant.",
              "Preserve actual outputs and executed-source-snapshot before any source edits.",
              "Fix the application global geographic title only when selected-unit/source scope justifies a common label; use neutral title otherwise. Preserve per-claim countries and strict validators.",
              "The unapplied lineage candidate can be integrated in the now-closed package window, followed by targeted/integrated checks and new frozen future contracts.",
              "Owner source/wording review applies to the raw two-claim result before owner acceptance; title engineering repair does not require rescoring. No stored approval/export."],
        cumulative_actual={"main_request_starts":8,"nemo_invocations":1,
            "known_completed_main_input_tokens":4571,"known_completed_main_output_tokens":824,
            "known_completed_main_total_tokens":5395,"interrupted_backend_tokens":"unknown","internal_nemo_usage":"unknown"})
    (ROOT/"handoff.json").write_text(json.dumps(h,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"sealed":True,"raw_gate_pass":True,"application_title_scope_pass":False,
        "main_requests":1,"nemo":0,"usage":service["usage"],"output_files_hashed":len(outputs),"grant_closed":True}))


if __name__=="__main__":main()
