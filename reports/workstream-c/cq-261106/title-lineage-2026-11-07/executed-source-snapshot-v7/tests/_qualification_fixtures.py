"""Synthetic retained-contract/start/result fixtures; never real execution grants."""
import json
from pathlib import Path
from test_subtask_quality_review import fixture as review_fixture
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.qualification_phase import QualificationLedger
from src.pilot.subtasks._development_lineage import canonical_hash, runtime_inputs


def write(path,value):
    path.write_text(json.dumps(value),encoding="utf-8")


def linked_ledger(tmp_path, deadline=172.0):
    roster,_,_ = review_fixture()
    limits = {"main_calls_per_case":4,"nemo_per_case":1,"seconds_per_case":180,"retries":0}
    model, settings = {"provider":"synthetic","digest":"a"*64},{"temperature":0,"num_ctx":4096}
    plans = {cid:Plan(query=f"What was public regional output in {2010+i}?",corpus_sha256=str(i+1)*64,
        subtasks=(Subtask(subtask_id="s01",operation="retrieve",query="public output"),)) for i,cid in enumerate(("d1","d2"))}
    pins=runtime_inputs()
    dev = {"phase":"development","case_ids":["d1","d2"],"pipeline_identity":"synthetic-pipeline","input_sha256":pins.copy(),
        "model_snapshot":model,"settings":settings,"limits":limits,
        "cases":{cid:{"plan":plan.model_dump(mode="json")} for cid,plan in plans.items()}}
    dev["contract_sha256"] = canonical_hash(dev)
    dp = tmp_path/"development.json";write(dp,dev)
    cases = []
    for i,(cid,plan) in enumerate(plans.items()):
        rp,ap,sp = (tmp_path/f"{cid}.{kind}.json" for kind in ("result","assessment","started"))
        run,attempt = str(i+1)*32,str(i+3)*32
        actual = plan.model_copy(update={"deadline_seconds":deadline})
        identity = {"run_id":run,"attempt_id":attempt,"plan_id":actual.plan_id,"corpus_sha256":plan.corpus_sha256}
        result = {"technical_pass":True,"failure_type":None,"main_calls":2,"nemo_invocations":1,"elapsed_seconds":20,
            "stored_run":{"id":run,"status":"needs_review","draft":{"claims":[]},"query":plan.query,"corpus_sha":plan.corpus_sha256,
                "metrics":{"attempt_id":attempt,"model_calls":2,"guardrail_invocations":1},
                "events":[{"kind":"attempt_started","payload":{"attempt_id":attempt}},
                    {"kind":"subtask_plan","payload":{"identity":identity,"plan":actual.model_dump(mode="json")}}]}}
        write(rp,result)
        write(ap,{"verdict":"pass","source_findings":["Synthetic source support only"],"result_sha256":digest(rp)})
        write(sp,{"case_id":cid,"contract_sha256":dev["contract_sha256"]})
        cases.append({"case_id":cid,"result_path":str(rp),"result_sha256":digest(rp),
            "assessment_path":str(ap),"assessment_sha256":digest(ap),"started_path":str(sp),"started_sha256":digest(sp),
            "development_contract_path":str(dp),"development_contract_file_sha256":digest(dp)})
    c = {"case_ids":[r["case_id"] for r in roster],"roster":roster,"input_sha256":pins.copy(),
        "pipeline_identity":"synthetic-pipeline","model_snapshot":model,"settings":settings,
        "development_case_ids":["d1","d2"],"development_gate":{"pipeline_identity":"synthetic-pipeline","cases":cases},"limits":limits}
    c["contract_sha256"] = canonical_hash(c)
    g = {"contract_sha256":c["contract_sha256"],"case_ids":c["case_ids"],"limits":limits,
         "authorization_reference":"SYNTHETIC TEST ONLY; no real authorization"}
    return QualificationLedger(tmp_path/"out",c,g)


def rehash(l):
    for case in l.contract["development_gate"]["cases"]:
        rp,ap = Path(case["result_path"]),Path(case["assessment_path"])
        assessment = json.loads(ap.read_text());assessment["result_sha256"] = digest(rp);write(ap,assessment)
        for path_key,hash_key in (("result_path","result_sha256"),("assessment_path","assessment_sha256"),
            ("started_path","started_sha256"),("development_contract_path","development_contract_file_sha256")):
            case[hash_key] = digest(case[path_key])
    l.contract["contract_sha256"] = canonical_hash(l.contract)
    l.grant["contract_sha256"] = l.contract["contract_sha256"]
