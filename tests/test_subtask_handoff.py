"""Preparatory attribution checks; not a spawned-runner integration claim."""
from dataclasses import replace
import pytest
from test_subtask_synthesis import fixture
from src.pilot.subtasks.synthesis import project_report
from src.pilot.subtasks._handoff import prepare,fingerprint,seal,verify_seal


def projected():
    p,r,m,c,b=fixture()
    return r,project_report(p,r,m,c,b,as_of='2026-11-05',is_current=lambda:True)


def test_typed_lineage_is_detached_and_bound_to_accepted_sources():
    report,result=projected();draft,lineage=prepare(result,report)
    assert lineage['claim_provenance'][1]['origins'][0]['subtask_id']=='s02'
    before=fingerprint(draft,{},lineage)
    result.draft['claims'][0]['text']='Changed callback state'
    assert fingerprint(draft,{},lineage)==before
    draft['claims'][0]['text']='Changed guarded content'
    assert fingerprint(draft,{},lineage)!=before


@pytest.mark.parametrize('damage',['guarded','identity','source','child','coverage'])
def test_invalid_lineage_rejects(damage):
    report,result=projected()
    if damage=='guarded':result=replace(result,safety_passed=True)
    elif damage=='identity':result.diagnostics['identity']['attempt_id']='f'*32
    elif damage=='coverage':result=replace(result,provenance=result.provenance[:1])
    else:result.provenance[0]['origins'][0]['source_id' if damage=='source' else 'child_attempt_id']='unknown'
    with pytest.raises(ValueError):prepare(result,report)


def test_old_dictionary_is_detached_without_invented_lineage():
    report,result=projected();draft,lineage=prepare(result.draft,report)
    assert draft==result.draft and draft is not result.draft and lineage is None


@pytest.mark.parametrize('damage',['diagnostics','claims','provenance','origin','origin_identity','guard_flag'])
def test_malformed_typed_result_fails_explicitly(damage):
    report,result=projected()
    if damage=='diagnostics':result=replace(result,diagnostics=None)
    elif damage=='claims':result.draft['claims']=None
    elif damage=='provenance':result=replace(result,provenance=None)
    elif damage=='guard_flag':result=replace(result,safety_passed=None)
    elif damage=='origin_identity':result.provenance[0]['origins'][0]['source_id']=[]
    else:result.provenance[0]['origins'][0]=None
    with pytest.raises(ValueError):prepare(result,report)


@pytest.mark.parametrize('damage',[None,'draft','sources','provenance','identity','status'])
def test_candidate_seal_binds_exact_content_and_identity(damage):
    report,result=projected();draft,lineage=prepare(result,report)
    sources={s.source_id:s.model_dump() for r in report.results for s in r.sources}
    identity=report.identity.model_dump();artifact=seal(draft,sources,lineage,identity)
    if damage is None:
        assert verify_seal(draft,sources,artifact,identity)==lineage
        return
    if damage=='draft':draft['claims'][0]['text']='Different text'
    elif damage=='sources':sources['d0']['content']='Different source'
    elif damage=='provenance':artifact['claim_provenance'][0]['origins'][0]['unit_id']='other-unit'
    elif damage=='identity':artifact['identity']['attempt_id']='f'*32
    else:artifact['status']='approved'
    with pytest.raises(ValueError):verify_seal(draft,sources,artifact,identity)


@pytest.mark.parametrize('damage',['extra_lineage','diagnostics','identity','nan'])
def test_candidate_rejects_malformed_serialized_attribution(damage):
    report,result=projected();draft,lineage=prepare(result,report)
    identity=report.identity.model_dump()
    if damage=='extra_lineage':lineage['unrecognized']='value'
    elif damage=='diagnostics':lineage['diagnostics']=None
    elif damage=='identity':identity['attempt_id']='not-an-attempt'
    else:lineage['diagnostics']['invalid_number']=float('nan')
    with pytest.raises(ValueError):seal(draft,{},lineage,identity)
