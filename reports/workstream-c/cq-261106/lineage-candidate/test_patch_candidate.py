"""Load exact proposed patch modules in memory; preserve actual runtime module."""
import importlib.util
import sys
from pathlib import Path

import pytest
from test_lineage_candidate import fixture, rehash


ROOT=Path(__file__).resolve().parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def proposed(monkeypatch):
    name="src.pilot.subtasks._development_lineage"
    helper=load(name,ROOT/"proposed_development_lineage.py")
    monkeypatch.setitem(sys.modules,name,helper)
    return load("src.pilot.subtasks._candidate_qualification_phase",ROOT/"proposed_qualification_phase.py").QualificationLedger


def test_exact_proposed_patch_accepts_reduced_deadline_without_replacing_runtime(tmp_path,proposed):
    from src.pilot.subtasks.qualification_phase import QualificationLedger as Current
    original=Current._verify
    values=fixture(tmp_path,172.0)
    proposed(values.output,values.contract,values.grant)._verify()
    assert Current._verify is original
    assert not values.output.exists()


def test_exact_proposed_patch_rejects_outer_relabeling(tmp_path,proposed):
    values=fixture(tmp_path)
    values.contract["pipeline_identity"]=values.contract["development_gate"]["pipeline_identity"]="changed"
    rehash(values)
    with pytest.raises(ValueError,match="pipeline/model/settings"):
        proposed(values.output,values.contract,values.grant)._verify()


def test_category_stop_rule_survives_exact_patch_with_synthetic_rows(tmp_path,proposed,monkeypatch):
    import test_subtask_qualification_phase as maintained
    def linked(path):
        values=fixture(path)
        return proposed(values.output,values.contract,values.grant)
    monkeypatch.setattr(maintained,"ledger",linked)
    maintained.test_nine_of_ten_allowance_controls_actual_admission(tmp_path)
