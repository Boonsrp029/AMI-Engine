"""Offline replay and evidence seal after the v7 first-failure closure."""
import hashlib
import json
from pathlib import Path
import sys
import traceback

sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from scripts._concurrent_composer_capture import capture_composer


ROOT=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path,value):
    with path.open("x",encoding="utf-8") as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write("\n")


def main():
    contract_path=ROOT/"development-contract-v7.json";contract=read(contract_path)
    assert all(sha(name)==value for name,value in contract["input_sha256"].items())
    actual=ROOT/"actual-development-v7"
    assert (actual/"stopped.json").exists()
    p1,p2=(read(actual/(cid+".result.json")) for cid in contract["case_ids"])
    assert p1["technical_pass"] is True and p2["technical_pass"] is False
    assert read(actual/"cq-p01.assessment.json")["verdict"]=="pass"
    assert not (actual/"cq-p02.composition.raw.json").exists() and not (actual/"cq-p02.safety.json").exists()
    mapping=actual/"cq-p02.mapping.raw.json"
    before=sha(mapping)
    expected={"contract":sha(contract_path),"mapping":before,"corpus":sha(contract["cases"]["cq-p02"]["corpus_path"])}
    try:
        capture_composer(contract_path,"cq-p02",mapping,expected=expected)
    except ValueError as exc:
        failure={"message":str(exc),"error_type":type(exc).__name__,"traceback":traceback.format_exc()}
    else:raise AssertionError("The retained malformed partial anchor must still fail")
    assert failure["message"]=="Evidence mapping gap anchor is not in the question"
    assert sha(mapping)==before
    write(ROOT/"cq-p02-offline-replay.json",{"actual_model_calls":0,"original_mapper_sha256":before,
        "regraded":False,"failure":failure})
    archive=ROOT/"executed-source-snapshot-v7";archive.mkdir()
    pins={}
    for name,value in contract["input_sha256"].items():
        relative=Path(name).resolve().relative_to(Path.cwd().resolve())
        assert ".git" not in relative.parts and ".env" not in relative.name
        target=archive/relative;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(Path(name).read_bytes());assert sha(target)==value
        pins[relative.as_posix()]=value
    for name in ("development-contract-v7.json","development-grant-v7.json","run_v7_bounded.py"):
        (archive/name).write_bytes((ROOT/name).read_bytes())
    outputs={path.relative_to(actual).as_posix():sha(path) for path in actual.rglob("*") if path.is_file()}
    write(archive/"manifest.json",{"input_sha256":pins,"actual_output_sha256":outputs,
        "operator_wrapper_sha256":sha(ROOT/"run_v7_bounded.py"),
        "wall_clock_records":{cid:sha(ROOT/("wall-clock-"+cid+".json")) for cid in contract["case_ids"]}})
    usage={"input_tokens":0,"output_tokens":0,"total_tokens":0}
    responses=[]
    for cid in contract["case_ids"]:
        for stage in ("mapping","composition"):
            path=actual/(cid+"."+stage+".raw.json")
            if path.exists():
                response=read(path);assert response["response_metadata"]["done_reason"]=="stop"
                for key in usage:usage[key]+=response["usage"][key]
                responses.append({"case_id":cid,"stage":stage,"usage":response["usage"],"finish_reason":"stop"})
    findings={"status":"v7 stopped at cq-p02; allowance closed; two-case gate not passed",
        "contract_sha256":contract["contract_sha256"],"development_planned":2,"development_attempted":2,
        "assistant_passed":["cq-p01"],"failed":["cq-p02"],"unattempted":[],
        "cq_p01":{"technical_pass":True,"source_complete":True,"raw_complete":True,"fallback":False,
            "title":"neutral; mapper global geography unresolved, suppression branch not exercised by this actual case",
            "safety":"one actual NeMo PASSED","persistence":"revision1 needs_review reopened read-only; zero reviews/exports",
            "owner_verdict":"pending","application_seconds":p1["elapsed_seconds"],"wall_seconds":read(ROOT/"wall-clock-cq-p01.json")["elapsed_seconds"]},
        "cq_p02":{"technical_pass":False,"phase":"mapping","raw_status":"partial",
            "evidence":"correct supported wind span selected; retail-price branch correctly returned missing",
            "defect":"gap_anchor copies the supported source sentence instead of the unresolved question fragment",
            "confirmed_error":failure["message"],"composition_requests":0,"nemo_invocations":0,"saved_revision":0,
            "application_seconds":p2["elapsed_seconds"],"wall_seconds":read(ROOT/"wall-clock-cq-p02.json")["elapsed_seconds"]},
        "main_requests":3,"nemo_invocations":1,"known_main_usage":usage,"responses":responses,
        "incomplete_usage":"NeMo internal request/token counts; historical interrupted request; monetary/hardware costs",
        "CQ1attempted":0,"CQ1unattempted":20,"approvals_created":0,"exports_created":0,
        "new_calls_for_diagnosis":0,"inputs_unchanged_through_batch":True,"output_hashes":outputs,
        "next":"Offline bounded question-fragment decoder design for partial/conflicting anchors; do not relax validation, fill omitted fields or repair the saved response. No further inference without a new grant."}
    write(ROOT/"v7-diagnostic-findings.json",findings)
    handoff=read(ROOT.parent/"handoff.json")
    handoff.update(status="v7_closed_p01_actual_pass_p02_question_anchor_failure",latest_development_actual=findings,
        authorization={"all_allowances":"closed; v7 used3main1NeMo and stopped at cq-p02"},active_diagnostic_session=None,
        next=["No generation/retries/CQ1 under the closed v7 grant.",
              "Preserve executed-source-snapshot-v7 and original outputs before any later offline edits.",
              "Design bounded concurrent-only question-fragment choices for partial/conflicting gap_anchor; keep component IDs/bindings, exact validators, model/settings and call ceiling.",
              "Use different synthetic facts and test that available facts remain partial while missing fragments belong to the original question; do not change global sequential request parsing.",
              "Owner semantic review applies to p01's valid claims, not p02's technical rejection. No stored approval/export."],
        cumulative_actual={"main_request_starts":11,"nemo_invocations":2,
            "known_completed_main_input_tokens":6377,"known_completed_main_output_tokens":1225,
            "known_completed_main_total_tokens":7602,"historical_interrupted_backend_usage":"unknown","internal_nemo_usage":"unknown"})
    (ROOT.parent/"handoff.json").write_text(json.dumps(handoff,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"sealed":True,"passed":["cq-p01"],"failed":["cq-p02"],"failure":failure["message"],
        "main_requests":3,"nemo_invocations":1,"known_main_usage":usage,"grant_closed":True}))


if __name__=="__main__":main()
