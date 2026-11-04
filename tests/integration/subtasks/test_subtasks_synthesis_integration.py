"""D joins real scheduler, persistence and C's synthesis boundary using fixed drafts."""
from types import SimpleNamespace
import pytest
from src.pilot.subtasks.contracts import Source,Result,digest
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.synthesis import compose_report
from src.pilot._evidence import EvidenceMap
from test_subtasks_execution_integration import setup


def fixture(tmp_path):
    store,plan,rid,aid,sink=setup(tmp_path)
    texts={'s01':'A fictional rate was observed at 4% in 2020.','s02':'A fictional rate is projected at 3% in 2030.'}
    def worker(ctx):
        text=texts[ctx.task.subtask_id]
        source=Source(source_id=ctx.task.subtask_id,content=text,content_sha256=digest(text),corpus_sha256=plan.corpus_sha256,role='support')
        return Result(identity=ctx.identity,subtask_id=ctx.task.subtask_id,child_attempt_id=ctx.child_attempt_id,outcome='evidence',sources=(source,),elapsed_seconds=0.0)
    report=run_plan(plan,rid,aid,worker,event=sink,is_current=sink.current)
    mapping=EvidenceMap.model_validate({'components':[{'component_id':f'r{i}','question_anchor':'fictional',
        'status':'supported','short_answer':texts[sid],'evidence':[{'source_id':sid,'quote':texts[sid]}]} for i,sid in enumerate(texts,1)]})
    composed={'title':'Analyst research brief','claims':[{'component_id':f'r{i}','unit_id':f'u{i}','text':text} for i,text in enumerate(texts.values(),1)]}
    bindings={'r1':('s01',),'r2':('s02',)}
    return store,plan,rid,aid,sink,report,mapping,composed,bindings


@pytest.mark.parametrize('mode',['valid','wrong_numeric','reject_guard','cancel_in_guard','cross_branch'])
def test_real_aggregate_synthesis_guard_and_publication_fence(tmp_path,mode):
    store,plan,rid,aid,sink,report,mapping,composed,bindings=fixture(tmp_path);checked=[]
    if mode=='wrong_numeric':composed['claims'][1]['text']=composed['claims'][0]['text']
    if mode=='cross_branch':bindings={'r1':('s02',),'r2':('s01',)}
    def guard(**kwargs):
        checked.append(kwargs)
        if mode=='cancel_in_guard':store.cancel(rid)
        return {'passed_guardrails':mode!='reject_guard'}
    def invoke():return compose_report(plan,report,mapping,composed,bindings,as_of='2026-11-04',guard=SimpleNamespace(validate_output=guard),is_current=sink.current)
    if mode=='valid':
        answer=invoke();assert len(checked)==1 and len(answer.provenance)==2
        assert [p['origins'][0]['subtask_id'] for p in answer.provenance]==['s01','s02']
        assert store.get(rid)['draft'] is None  # Composition cannot approve/publish itself.
        sources={s.source.source_id:s.source.model_dump() for s in report.sources}
        store.save_draft(rid,answer.draft,sources,{},attempt_id=aid)
        assert store.get(rid)['status']=='needs_review'
    else:
        with pytest.raises(ValueError):invoke()
        assert store.get(rid)['draft'] is None
        if mode in {'wrong_numeric','cross_branch'}:assert not checked
