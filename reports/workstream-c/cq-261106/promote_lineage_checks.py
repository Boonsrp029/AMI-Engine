"""Promote the reviewed synthetic candidate fixtures/checks; no inference."""
from pathlib import Path


ROOT=Path(__file__).resolve().parent


def main():
    candidate=(ROOT/"lineage-candidate/test_lineage_candidate.py").read_text(encoding="utf-8")
    setup=candidate[candidate.index("def write(path,value):"):candidate.index('@pytest.mark.parametrize("deadline"')]
    setup=setup.replace("def fixture(tmp_path, deadline=172.0):","def linked_ledger(tmp_path, deadline=172.0):")
    header='''"""Synthetic retained-contract/start/result fixtures; never real execution grants."""
import json
from pathlib import Path
from test_subtask_quality_review import fixture as review_fixture
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.qualification_phase import QualificationLedger
from src.pilot.subtasks._development_lineage import canonical_hash


'''
    with Path("tests/_qualification_fixtures.py").open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(header+setup.rstrip()+"\n")
    tests=candidate[candidate.index('@pytest.mark.parametrize("deadline"'):candidate.index("def test_old_minimal_fixture")]
    header='''"""Integrated development-lineage gates; fabricated records and no model calls."""
import json
from pathlib import Path
import pytest
from _qualification_fixtures import linked_ledger as fixture, rehash, write
from src.pilot.subtasks._development_lineage import canonical_hash


'''
    footer='''def test_minimal_legacy_gate_records_fail_closed(tmp_path):
    values=fixture(tmp_path)
    for case in values.contract["development_gate"]["cases"]:
        for name in ("development_contract_path","development_contract_file_sha256","started_path","started_sha256"):
            case.pop(name)
    values.contract["contract_sha256"]=canonical_hash(values.contract)
    values.grant["contract_sha256"]=values.contract["contract_sha256"]
    with pytest.raises(ValueError,match="Missing retained"):
        values._verify()
    assert not values.output.exists()
'''
    with Path("tests/test_subtask_development_lineage.py").open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(header+tests+footer)
    print("Promoted synthetic lineage fixtures and regression checks; no runtime calls")


if __name__=="__main__":main()
