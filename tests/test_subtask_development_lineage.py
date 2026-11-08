"""Integrated development-lineage gates; fabricated records and no model calls."""
import json
from pathlib import Path
import pytest
from _qualification_fixtures import linked_ledger as fixture, rehash, write
from src.pilot.subtasks._development_lineage import canonical_hash


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


def test_minimal_legacy_gate_records_fail_closed(tmp_path):
    values=fixture(tmp_path)
    for case in values.contract["development_gate"]["cases"]:
        for name in ("development_contract_path","development_contract_file_sha256","started_path","started_sha256"):
            case.pop(name)
    values.contract["contract_sha256"]=canonical_hash(values.contract)
    values.grant["contract_sha256"]=values.contract["contract_sha256"]
    with pytest.raises(ValueError,match="Missing retained"):
        values._verify()
    assert not values.output.exists()


@pytest.mark.parametrize("damage",["missing_dev_pin","wrong_dev_pin","missing_current_pin"])
def test_matching_labels_cannot_hide_stale_or_unpinned_runtime(tmp_path,damage):
    values=fixture(tmp_path)
    key=str(Path("src/pilot/subtasks/_title_scope.py").resolve())
    case=values.contract["development_gate"]["cases"][0]
    dp=Path(case["development_contract_path"])
    dev=json.loads(dp.read_text(encoding="utf-8"))
    if damage=="missing_current_pin":
        values.contract["input_sha256"].pop(key)
    else:
        if damage=="missing_dev_pin":dev["input_sha256"].pop(key)
        else:dev["input_sha256"][key]="f"*64
        dev["contract_sha256"]=canonical_hash(dev);write(dp,dev)
        for item in values.contract["development_gate"]["cases"]:
            sp=Path(item["started_path"])
            start=json.loads(sp.read_text(encoding="utf-8"));start["contract_sha256"]=dev["contract_sha256"];write(sp,start)
    rehash(values)
    with pytest.raises(ValueError,match="runtime input"):
        values._verify()
