"""Actual spawned C-to-A handoff, using fixed facts and no inference."""
from dataclasses import dataclass,replace
import hashlib
import pytest
from test_subtask_synthesis import fixture,A,B,Q
from src.pilot.schemas import ResearchRequest,ReviewRequest
from src.pilot.store import Store,Conflict
from src.pilot.subtasks.contracts import Plan,Subtask,Source,Result,digest
from src.pilot.subtasks.synthesis import project_report
from src.pilot.subtasks.runner import run_stored_plan


def operation(ctx):
    i=int(ctx.task.subtask_id[-1])-1;text=(A,B)[i]
    return Result(identity=ctx.identity,subtask_id=ctx.task.subtask_id,child_attempt_id=ctx.child_attempt_id,
        dependencies=ctx.dependency_refs,outcome='evidence',elapsed_seconds=0.,
        sources=(Source(source_id=f'd{i}',content=text,content_sha256=digest(text),corpus_sha256=ctx.identity.corpus_sha256,role='support'),))


@dataclass
class Composer:
    plan:object
    mode:str='valid'
    def __call__(self,report,access):
        _,_,mapping,composed,bindings=fixture()
        mapping=access.main(lambda:mapping)
        if self.mode=='fallback':composed['claims']=composed['claims'][:1]
        composed=access.main(lambda:composed)
        result=project_report(self.plan,report,mapping,composed,bindings,as_of='2026-11-05',is_current=lambda:True)
        if self.mode=='guarded':result=replace(result,safety_passed=True)
        if self.mode=='identity':result.diagnostics['identity']['attempt_id']='f'*32
        if self.mode=='origin':result.provenance[0]['origins'][0]['child_attempt_id']='f'*32
        return result


def allow(draft,sources):return True
def reject(draft,sources):return False
def mutate(draft,sources):draft['claims'][0]['text']='Changed during safety';return True
def mutate_source(draft,sources):sources['d0']['content']='Changed during safety';return True


def setup(tmp_path):
    corpus=tmp_path/'corpus.json';corpus.write_text('[]');sha=hashlib.sha256(corpus.read_bytes()).hexdigest()
    p=Plan(query=Q,corpus_sha256=sha,subtasks=(Subtask(subtask_id='s01',operation='retrieve',query='observed'),Subtask(subtask_id='s02',operation='retrieve',query='projected')))
    store=Store(tmp_path/'history.sqlite3');rid,_=store.create(ResearchRequest(query=Q,request_key='typed-runner-case'),sha)
    return store,rid,p,corpus


@pytest.mark.parametrize('mode',['valid','fallback'])
def test_spawned_typed_lineage_and_revision_history(tmp_path,mode):
    store,rid,p,corpus=setup(tmp_path)
    run_stored_plan(store,rid,p,corpus,operation,Composer(p,mode),allow)
    row=store.get(rid);metrics=row['metrics']
    assert row['status']=='needs_review' and metrics['model_calls']==2 and metrics['guardrail_invocations']==1
    assert len(metrics['composition_provenance'])==2
    artifact=next(e['payload'] for e in row['events'] if e['kind']=='composition_candidate')
    assert artifact['status'].startswith('candidate;')
    assert artifact['content_sha256']==metrics['composition_content_sha256']
    results={e['payload']['subtask_id']:e['payload'] for e in row['events'] if e['kind']=='subtask_result'}
    for claim in metrics['composition_provenance']:
        for origin in claim['origins']:
            actual=results[origin['subtask_id']]
            assert origin['child_attempt_id']==actual['child_attempt_id']
            assert origin['content_sha256']==actual['sources'][0]['content_sha256']
    assert bool(metrics['composition_diagnostics']['fallback_unit_ids'])==(mode=='fallback')
    with pytest.raises(Conflict):store.export(rid)
    store.review(rid,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-A',support_confirmed=True))
    original=store.export(rid);assert store.export(rid)==original
    store.save_draft(rid,row['draft'],row['sources'],{},expected_revision=1)
    with pytest.raises(Conflict):store.export(rid)
    assert next(e['payload'] for e in store.get(rid)['events'] if e['kind']=='composition_candidate')==artifact


@pytest.mark.parametrize('mode,safety',[('guarded',allow),('identity',allow),('origin',allow),('valid',reject),('valid',mutate),('valid',mutate_source)])
def test_typed_failure_cannot_publish_candidate_or_draft(tmp_path,mode,safety):
    store,rid,p,corpus=setup(tmp_path)
    with pytest.raises(ValueError):run_stored_plan(store,rid,p,corpus,operation,Composer(p,mode),safety)
    row=store.get(rid)
    assert row['status']=='failed' and row['revision']==0
    assert not any(e['kind']=='composition_candidate' for e in row['events'])
    assert row['metrics'].get('guardrail_invocations',0)==(0 if mode!='valid' else 1)


@pytest.mark.parametrize('stop',['reject_candidate','cancel_after_candidate'])
def test_parent_fence_between_candidate_and_publication(tmp_path,monkeypatch,stop):
    store,rid,p,corpus=setup(tmp_path);write=store.attempt_event
    def fenced(run_id,attempt_id,kind,payload):
        if kind!='composition_candidate':return write(run_id,attempt_id,kind,payload)
        if stop=='reject_candidate':return False
        accepted=write(run_id,attempt_id,kind,payload)
        store.cancel(run_id)
        return accepted
    monkeypatch.setattr(store,'attempt_event',fenced)
    with pytest.raises(Conflict):run_stored_plan(store,rid,p,corpus,operation,Composer(p),allow)
    row=store.get(rid);assert row['revision']==0 and row['draft'] is None
    assert any(e['kind']=='composition_candidate' for e in row['events'])==(stop=='cancel_after_candidate')
    with pytest.raises(Conflict):store.export(rid)


def empty_composer(report,access):
    from src.pilot.subtasks.synthesis import SynthesisResult
    return SynthesisResult({'title':'No supported answer','claims':[],
        'warnings':['Supplied evidence does not answer the question.']},(),{'identity':report.identity.model_dump()})


def test_typed_empty_claims_skip_safety_and_cannot_be_approved(tmp_path):
    store,rid,p,corpus=setup(tmp_path)
    run_stored_plan(store,rid,p,corpus,operation,empty_composer,reject)
    row=store.get(rid);assert row['metrics']['guardrail_invocations']==0
    with pytest.raises(Conflict):store.review(rid,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-A',support_confirmed=True))
    with pytest.raises(Conflict):store.export(rid)
