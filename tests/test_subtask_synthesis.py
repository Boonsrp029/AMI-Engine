from dataclasses import replace
from types import SimpleNamespace
import pytest
from src.pilot.subtasks.contracts import Plan,Subtask,Identity,Source,Result,digest
from src.pilot.subtasks.scheduler import Report,aggregate,run_plan
from src.pilot.subtasks.synthesis import compose_report

Q='Compare observed electricity demand in 2018 and projected electricity demand through 2032.'
A='Observed electricity demand grew 4.5% in 2018.'
B='Electricity demand is projected to grow 2.25% annually through 2032.'
SHA='a'*64


def fixture(optional=False):
 p=Plan(query=Q,corpus_sha256=SHA,subtasks=(Subtask(subtask_id='s01',operation='retrieve',query='observed'),Subtask(subtask_id='s02',operation='retrieve',query='projected',required=not optional)))
 identity=Identity(run_id='b'*32,attempt_id='c'*32,plan_id=p.plan_id,corpus_sha256=SHA)
 results=tuple(Result(identity=identity,subtask_id=f's0{i+1}',child_attempt_id=str(i+1)*32,outcome='evidence',elapsed_seconds=0.,sources=(Source(source_id=f'd{i}',content=q,content_sha256=digest(q),corpus_sha256=SHA,role='support'),)) for i,q in enumerate([A,B]))
 report=Report(identity,'completed',(('s01','completed'),('s02','completed')),results,aggregate(results),(),True)
 mapping={'components':[{'component_id':'r1','question_anchor':Q,'status':'supported','short_answer':A+' '+B,'evidence':[{'source_id':f'd{i}','quote':q} for i,q in enumerate([A,B])]}]}
 composed={'title':'Analyst research brief','claims':[{'component_id':'r1','unit_id':f'u{i+1}','text':q} for i,q in enumerate([A,B])]}
 return p,report,mapping,composed,{'r1':('s01','s02')}


def execute(values,passed=True,fence=lambda:True):
 calls=[]
 def guard(**kwargs):calls.append(kwargs);return {'passed_guardrails':passed}
 result=compose_report(*values,as_of='2026-11-04',guard=SimpleNamespace(validate_output=guard),is_current=fence)
 return result,calls


def test_complete_claim_provenance_and_final_safety():
 result,calls=execute(fixture())
 assert len(result.draft['claims'])==2 and len(calls)==1
 assert result.provenance[0]['origins'][0]['subtask_id']=='s01'
 assert result.provenance[1]['origins'][0]['subtask_id']=='s02'
 assert B in calls[0]['raw_report']
 assert not result.diagnostics['fallback_unit_ids']


@pytest.mark.parametrize('text',[A,'Electricity demand is projected to grow 2.25% through 2018.','Electricity generation is projected to grow 2.25% through 2032.','Electricity demand grew 2.25% through 2032.'])
def test_cross_unit_number_date_measure_and_basis_reject(text):
 values=fixture();values[3]['claims'][1]['text']=text
 with pytest.raises(ValueError):execute(values)


def test_optional_technical_failure_preserves_supported_answer_and_explicit_gap():
 p,r,m,c,b=fixture(True);r=replace(r,status='partial',states=(('s01','completed'),('s02','failed')),results=r.results[:1],sources=aggregate(r.results[:1]),missing_branches=('s02',))
 m['components'][0]['evidence']=m['components'][0]['evidence'][:1]
 m['components'].append({'component_id':'r2','question_anchor':Q,'status':'missing','short_answer':'','evidence':[],'gap_anchor':'projected electricity demand'})
 b={'r1':('s01',),'r2':('s02',)};c['claims']=c['claims'][:1]
 result,_=execute((p,r,m,c,b))
 assert result.draft['claims'][0]['text']==A
 assert any('s02' in w and 'failed' in w for w in result.draft['warnings'])
 assert any('projected electricity demand' in w for w in result.draft['warnings'])


def test_required_failure_blocks_before_guard():
 p,r,m,c,b=fixture();r=replace(r,can_compose=False,states=(('s01','completed'),('s02','failed')))
 with pytest.raises(ValueError,match='s02'):execute((p,r,m,c,b))


def test_branch_crossing_rejected_even_if_source_exists():
 p,r,m,c,b=fixture();b={'r1':('s01',),'r2':('s02',)}
 m['components'].append({'component_id':'r2','question_anchor':Q,'status':'missing','short_answer':'','evidence':[],'gap_anchor':'projected electricity demand'})
 with pytest.raises(ValueError,match='crosses branch'):execute((p,r,m,c,b))


def test_guardrail_failure_and_stale_attempt_never_return_draft():
 with pytest.raises(ValueError,match='safety'):execute(fixture(),passed=False)
 checks=iter([True,True,False])
 with pytest.raises(ValueError,match='Stale'):execute(fixture(),fence=lambda:next(checks))


def test_real_scheduler_report_consumed_by_adapter():
 p,_,m,c,b=fixture()
 def operation(ctx):
  q=A if ctx.task.subtask_id=='s01' else B;i=0 if ctx.task.subtask_id=='s01' else 1
  return Result(identity=ctx.identity,subtask_id=ctx.task.subtask_id,child_attempt_id=ctx.child_attempt_id,elapsed_seconds=0.,outcome='evidence',sources=(Source(source_id=f'd{i}',content=q,content_sha256=digest(q),corpus_sha256=SHA,role='support'),))
 r=run_plan(p,'b'*32,'c'*32,operation)
 result,_=execute((p,r,m,c,b))
 assert len(result.provenance)==2


def test_unbound_completed_branch_cannot_disappear():
 p,r,m,c,b=fixture();b={'r1':('s01',)}
 with pytest.raises(ValueError):execute((p,r,m,c,b))


def test_missing_result_remains_visible_with_supported_partial_answer():
 p,r,m,c,b=fixture();missing=r.results[1].model_copy(update={'outcome':'missing','sources':()})
 r=replace(r,results=(r.results[0],missing),sources=aggregate((r.results[0],missing)))
 m['components'][0]['evidence']=m['components'][0]['evidence'][:1];c['claims']=c['claims'][:1]
 result,_=execute((p,r,m,c,b))
 assert result.draft['claims'][0]['text']==A
 assert any('s02 returned missing' in w for w in result.draft['warnings'])


def test_omitted_unit_fallback_keeps_lineage_and_raw_output():
 values=fixture();values[3]['claims']=values[3]['claims'][:1]
 result,calls=execute(values)
 assert result.diagnostics['fallback_unit_ids']==['u2']
 assert len(result.diagnostics['raw_composer_output']['claims'])==1
 assert result.provenance[1]['origins'][0]['subtask_id']=='s02'
 assert B in calls[0]['raw_report']


def test_conflicting_component_abstains_without_picking_winner():
 p,r,m,c,b=fixture();results=tuple(x.model_copy(update={'outcome':'conflicting'}) for x in r.results)
 r=replace(r,results=results,sources=aggregate(results));m['components'][0].update(status='conflicting',short_answer='',gap_anchor=Q)
 result,calls=execute((p,r,m,{'title':'Analyst research brief','claims':[]},b))
 assert result.draft['claims']==[] and calls==[]
 assert any('conflicting' in w.lower() for w in result.draft['warnings'])


def test_projection_leaves_safety_to_runner_exactly_once():
 from src.pilot.subtasks.synthesis import project_report
 from src.pilot.subtasks.runner import ModelAccess
 import time
 p,r,m,c,b=fixture()
 result=project_report(p,r,m,c,b,as_of='2026-11-04',is_current=lambda:True)
 assert result.safety_passed is False
 access=ModelAccess(time.monotonic()+10)
 checks=[]
 assert access.guard(lambda:checks.append(result.draft) or True)
 assert access.guards==1 and len(checks)==1
 with pytest.raises(RuntimeError,match='budget'):access.guard(lambda:True)


def test_guarded_result_is_explicitly_safe_and_keeps_lineage():
 result,calls=execute(fixture())
 assert result.safety_passed is True and result.provenance and len(calls)==1


def test_scheduler_synthesis_storage_approval_export_and_lineage(tmp_path):
 from src.pilot.subtasks.synthesis import persist_synthesis,project_report
 from src.pilot.store import Store,Conflict
 from src.pilot.schemas import ResearchRequest,ReviewRequest
 from src.pilot.subtasks.contracts import Identity
 store=Store(tmp_path/'history.sqlite3');p,_,m,c,b=fixture()
 rid,_=store.create(ResearchRequest(query=Q,request_key="synthetic-composition-integration"),SHA);attempt='c'*32;assert store.claim(rid,attempt)
 def operation(ctx):
  i=0 if ctx.task.subtask_id=='s01' else 1;q=[A,B][i]
  return Result(identity=ctx.identity,subtask_id=ctx.task.subtask_id,child_attempt_id=ctx.child_attempt_id,outcome='evidence',elapsed_seconds=0.,sources=(Source(source_id=f'd{i}',content=q,content_sha256=digest(q),corpus_sha256=SHA,role='support'),))
 report=run_plan(p,rid,attempt,operation)
 pending=project_report(p,report,m,c,b,as_of='2026-11-04',is_current=lambda:True)
 with pytest.raises(ValueError,match='Guarded'):persist_synthesis(store,report,pending)
 result,_=execute((p,report,m,c,b));assert persist_synthesis(store,report,result)==1
 row=store.get(rid);assert row['status']=='needs_review'
 assert row['metrics']['composition_provenance'][1]['origins'][0]['subtask_id']=='s02'
 assert any(e['kind']=='composition_candidate' for e in row['events'])
 with pytest.raises(Conflict):store.export(rid)
 store.review(rid,ReviewRequest(revision=1,decision='approve',reviewer='synthetic',support_confirmed=True))
 exported=store.export(rid);assert exported==store.export(rid)
 store.save_draft(rid,result.draft,row['sources'],row['metrics'],expected_revision=1)
 with pytest.raises(Conflict):store.export(rid)
 with pytest.raises(ValueError,match='Stale'):persist_synthesis(store,report,result)


@pytest.mark.parametrize('damage',['parent','corpus','child','order','source'])
def test_adversarial_aggregate_identity_is_rejected(damage):
 p,r,m,c,b=fixture()
 if damage=='parent':
  result=r.results[0].model_copy(update={'identity':r.identity.model_copy(update={'attempt_id':'e'*32})})
  r=replace(r,results=(result,r.results[1]),sources=aggregate((result,r.results[1])))
 elif damage=='corpus':r=replace(r,identity=r.identity.model_copy(update={'corpus_sha256':'e'*64}))
 elif damage=='child':
  result=r.results[1].model_copy(update={'child_attempt_id':r.results[0].child_attempt_id})
  r=replace(r,results=(r.results[0],result),sources=aggregate((r.results[0],result)))
 elif damage=='order':r=replace(r,results=tuple(reversed(r.results)),sources=aggregate(tuple(reversed(r.results))))
 else:
  source=r.results[0].sources[0].model_copy(update={'content':'Altered source'})
  result=r.results[0].model_copy(update={'sources':(source,)})
  r=replace(r,results=(result,r.results[1]),sources=aggregate((result,r.results[1])))
 with pytest.raises(ValueError):execute((p,r,m,c,b))


def test_required_real_scheduler_failure_remains_explicit():
 p,_,m,c,b=fixture()
 def fail(ctx):raise RuntimeError('Synthetic unavailable retrieval')
 r=run_plan(p,'b'*32,'c'*32,fail)
 with pytest.raises(ValueError,match='Required branch unavailable.*s01'):execute((p,r,m,c,b))
