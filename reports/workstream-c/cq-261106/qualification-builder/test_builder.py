"""Offline compiler checks with synthetic rows; never inference or real grants."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[4]/"tests"))
from _qualification_fixtures import linked_ledger, write
from test_subtask_quality_review import fixture as review_fixture
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks._development_lineage import canonical_hash
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.qualification_phase import QualificationLedger
from src.pilot.subtasks.quality_review import COUNTS, THRESHOLDS
from build_qualification import build


def setup(tmp_path):
    dev_dir=tmp_path/"dev";dev_dir.mkdir()
    linked_ledger(dev_dir)
    dp=dev_dir/"development.json";dev=json.loads(dp.read_text(encoding="utf-8"))
    dev.update(output_directory=str(dev_dir),as_of="2026-11-07")
    dev["contract_sha256"]=canonical_hash(dev);write(dp,dev)
    for cid in dev["case_ids"]:
        write(dev_dir/(cid+".started.json"),{"case_id":cid,"contract_sha256":dev["contract_sha256"]})
    pool=tmp_path/"pool";pool.mkdir()
    corpus=pool/"corpus.json";write(corpus,[{"feed_id":"synthetic","clean_content":"Synthetic output was seven units in 2012."}])
    roster,_,_=review_fixture()
    write(pool/"cases.json",[{**r,"required_findings":["DO NOT SEND THIS REFERENCE TO THE MODEL"]} for r in roster])
    plans={}
    for row in roster:
        plan=Plan(query="Describe the synthetic output.",corpus_sha256=digest(corpus),
            subtasks=(Subtask(subtask_id="s01",operation="retrieve",query="synthetic"),))
        plans[row["case_id"]]={"plan":plan.model_dump(mode="json"),"bindings":{"r1":["s01"]},
            "corpus_path":str(corpus),"category":row["category"],"complete_required_branches":{"r1":["s01"]}}
    write(pool/"plans.json",plans)
    write(pool/"manifest.json",{"pool_id":"CQ1","note":"SYNTHETIC TEST ONLY","categories":COUNTS,
        "thresholds":{**THRESHOLDS,"critical_errors":0},
        "sha256":{name:digest(pool/name) for name in ("cases.json","corpus.json")}})
    write(pool/"plans-v3-coverage-manifest.json",{"plans_file":"plans.json","sha256":digest(pool/"plans.json"),
        "original_content_manifest_sha256":digest(pool/"manifest.json")})
    return dict(development_path=dp,expected_identity=dev["contract_sha256"],pool=pool,
        destination=tmp_path/"future/contract.json",output_directory=tmp_path/"future/actual",as_of="2026-11-07",
        expected_pool_sha256=digest(pool/"manifest.json"),expected_plans_sha256=digest(pool/"plans.json"))


def test_compiler_binds_lineage_and_thresholds_without_grant_or_attempt(tmp_path):
    args=setup(tmp_path);c=build(**args)
    assert c["execution_authorized"] is False and len(c["case_ids"])==20
    assert c["category_thresholds"]=={**THRESHOLDS,"critical_errors":0}
    assert c["qualification_protocol"]["main_calls_total_max"]==80
    assert c["qualification_protocol"]["nemo_invocations_total_max"]==20
    assert not args["output_directory"].exists()
    assert all(set(r)=={"case_id","category"} for r in c["roster"])
    assert all("required_findings" not in row for row in c["cases"].values())
    assert all("started_path" in row and "development_contract_path" in row for row in c["development_gate"]["cases"])
    synthetic={"contract_sha256":c["contract_sha256"],"case_ids":c["case_ids"],"limits":c["limits"],
        "authorization_reference":"SYNTHETIC IN-MEMORY TEST ONLY; no real permission"}
    QualificationLedger(args["output_directory"],c,synthetic)._verify()
    assert not list(tmp_path.rglob("*grant*"))


def test_missing_current_result_refuses_before_any_future_output(tmp_path):
    args=setup(tmp_path);(tmp_path/"dev/d2.result.json").unlink()
    with pytest.raises(ValueError,match="missing"):build(**args)
    assert not args["destination"].parent.exists()


def test_failed_source_assessment_never_compiles(tmp_path):
    args=setup(tmp_path);path=tmp_path/"dev/d1.assessment.json"
    a=json.loads(path.read_text());a["verdict"]="fail";write(path,a)
    with pytest.raises(ValueError):build(**args)
    assert not args["destination"].exists()


def test_closed_development_batch_never_compiles(tmp_path):
    args=setup(tmp_path);write(tmp_path/"dev/stopped.json",{"reason":"synthetic failure"})
    with pytest.raises(ValueError,match="Failed development"):build(**args)
    assert not args["destination"].exists()


def test_matching_labels_do_not_hide_unpinned_runtime(tmp_path):
    args=setup(tmp_path);dp=args["development_path"];dev=json.loads(dp.read_text())
    dev["input_sha256"].pop(str(Path("src/pilot/subtasks/_title_scope.py").resolve()))
    dev["contract_sha256"]=canonical_hash(dev);write(dp,dev);args["expected_identity"]=dev["contract_sha256"]
    for cid in dev["case_ids"]:
        write(tmp_path/("dev/"+cid+".started.json"),{"case_id":cid,"contract_sha256":dev["contract_sha256"]})
    with pytest.raises(ValueError,match="runtime input"):build(**args)
    assert not args["destination"].exists()


@pytest.mark.parametrize("damage",["pool_identity","plan_identity","corpus"])
def test_predeclared_pool_and_plan_identity_cannot_drift(tmp_path,damage):
    args=setup(tmp_path)
    if damage=="pool_identity":args["expected_pool_sha256"]="f"*64
    elif damage=="plan_identity":args["expected_plans_sha256"]="f"*64
    else:(args["pool"]/"corpus.json").write_bytes((args["pool"]/"corpus.json").read_bytes()+b" ")
    with pytest.raises(ValueError):build(**args)
    assert not args["destination"].exists()


def test_existing_contract_is_never_overwritten(tmp_path):
    args=setup(tmp_path);args["destination"].parent.mkdir();args["destination"].write_text("Preserved local owner text")
    with pytest.raises(ValueError,match="fresh contract"):build(**args)
    assert args["destination"].read_text()=="Preserved local owner text"
