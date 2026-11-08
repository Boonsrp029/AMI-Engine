"""Synthetic candidate checks only; no runtime edit, model, network or Store."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[4]/"tests"))
from test_subtask_quality_review import fixture as review_fixture
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.qualification import digest
from lineage_candidate import QualificationLedger, canonical_hash


def write(path,value):
    path.write_text(json.dumps(value),encoding="utf-8")


def fixture(tmp_path, deadline=172.0):
    roster,_,_ = review_fixture()
    limits = {"main_calls_per_case":4,"nemo_per_case":1,"seconds_per_case":180,"retries":0}
    model, settings = {"provider":"synthetic","digest":"a"*64},{"temperature":0,"num_ctx":4096}
    plans = {cid:Plan(query=f"What was public regional output in {2010+i}?",corpus_sha256=str(i+1)*64,
        subtasks=(Subtask(subtask_id="s01",operation="retrieve",query="public output"),)) for i,cid in enumerate(("d1","d2"))}
    dev = {"phase":"development","case_ids":["d1","d2"],"pipeline_identity":"synthetic-pipeline",
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
    c = {"case_ids":[r["case_id"] for r in roster],"roster":roster,"input_sha256":{},
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


@pytest.mark.parametrize("deadline",[180.0,172.0])
def test_correct_lineage_including_reserved_deadline_passes_without_output(tmp_path,deadline):
    l = fixture(tmp_path,deadline);l._verify()
    assert not l.output.exists()


def test_reproduced_outer_relabeling_rejects_unchanged_pair(tmp_path):
    l = fixture(tmp_path)
    l.contract["pipeline_identity"] = l.contract["development_gate"]["pipeline_identity"] = "other-pipeline"
    rehash(l)
    with pytest.raises(ValueError,match="pipeline/model/settings"):
        l._verify()


@pytest.mark.parametrize("key",["started_path","development_contract_path"])
def test_missing_lineage_fails_closed(tmp_path,key):
    l = fixture(tmp_path);l.contract["development_gate"]["cases"][0].pop(key)
    l.contract["contract_sha256"] = canonical_hash(l.contract);l.grant["contract_sha256"] = l.contract["contract_sha256"]
    with pytest.raises(ValueError,match="Missing retained"):
        l._verify()


@pytest.mark.parametrize("damage",["query","corpus","plan","plan_identity","duplicate_run","duplicate_attempt","bounds","findings","status"])
def test_rehashed_wrong_records_still_reject(tmp_path,damage):
    l = fixture(tmp_path)
    cases = l.contract["development_gate"]["cases"]
    case = cases[1] if damage.startswith("duplicate") else cases[0]
    rp,ap = Path(case["result_path"]),Path(case["assessment_path"])
    r,a = json.loads(rp.read_text()),json.loads(ap.read_text())
    s = r["stored_run"]
    if damage=="query":s["query"]="Different query"
    elif damage=="corpus":s["corpus_sha"]="f"*64
    elif damage=="plan":s["events"][1]["payload"]["plan"]["query"]="Different query"
    elif damage=="plan_identity":s["events"][1]["payload"]["identity"]["plan_id"]="f"*64
    elif damage=="duplicate_run":s["id"]="1"*32
    elif damage=="duplicate_attempt":s["metrics"]["attempt_id"]="3"*32
    elif damage=="bounds":r["main_calls"]=5
    elif damage=="findings":a["source_findings"]=[" "]
    else:s["status"]="failed"
    write(rp,r);write(ap,a);rehash(l)
    with pytest.raises(ValueError):l._verify()


@pytest.mark.parametrize("damage",["case","contract","self_hash","model","settings"])
def test_wrong_start_or_retained_contract_rejects_even_with_new_file_hashes(tmp_path,damage):
    l = fixture(tmp_path);case=l.contract["development_gate"]["cases"][0]
    sp,dp = Path(case["started_path"]),Path(case["development_contract_path"])
    start,dev = json.loads(sp.read_text()),json.loads(dp.read_text())
    if damage=="case":start["case_id"]="d2"
    elif damage=="contract":start["contract_sha256"]="f"*64
    elif damage=="self_hash":dev["pipeline_identity"]="edited without canonical update"
    else:
        dev["model_snapshot" if damage=="model" else "settings"]={"changed":True}
        dev["contract_sha256"]=canonical_hash(dev)
        for c in l.contract["development_gate"]["cases"]:
            path=Path(c["started_path"]);st=json.loads(path.read_text());st["contract_sha256"]=dev["contract_sha256"];write(path,st)
        start=json.loads(sp.read_text())
    write(sp,start);write(dp,dev);rehash(l)
    with pytest.raises(ValueError):l._verify()


def test_mixed_development_contracts_reject_even_when_each_case_is_linked(tmp_path):
    l = fixture(tmp_path);case=l.contract["development_gate"]["cases"][1]
    original=Path(case["development_contract_path"])
    dev=json.loads(original.read_text());dev["output_directory"]="different-synthetic-batch"
    dev["contract_sha256"]=canonical_hash(dev)
    different=tmp_path/"second-contract.json";write(different,dev)
    case["development_contract_path"]=str(different)
    write(Path(case["started_path"]),{"case_id":"d2","contract_sha256":dev["contract_sha256"]})
    rehash(l)
    with pytest.raises(ValueError,match="mixes different"):
        l._verify()


def test_boolean_setting_cannot_alias_numeric_zero(tmp_path):
    l=fixture(tmp_path)
    l.contract["settings"]={"temperature":False,"num_ctx":4096}
    l.contract["contract_sha256"]=canonical_hash(l.contract);l.grant["contract_sha256"]=l.contract["contract_sha256"]
    with pytest.raises(ValueError,match="pipeline/model/settings"):
        l._verify()


@pytest.mark.parametrize("deadline",[0.0,181.0])
def test_invalid_or_extended_deadline_never_passes_lineage(tmp_path,deadline):
    l=fixture(tmp_path,deadline)
    with pytest.raises(ValueError):l._verify()


def test_old_minimal_fixture_still_passes_current_gate_but_candidate_rejects(tmp_path):
    from test_subtask_qualification_phase import ledger as current_fixture
    current=current_fixture(tmp_path)
    current._verify()
    candidate=QualificationLedger(current.output,current.contract,current.grant)
    with pytest.raises(ValueError):candidate._verify()
    assert not current.output.exists()
