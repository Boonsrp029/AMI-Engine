import json
from datetime import datetime, timezone
from pathlib import Path
import pytest
from pydantic import ValidationError
from src.pilot.subtasks.contracts import Plan, Subtask, Source, Result, Identity, Progress, digest, transition, TERMINAL

SHA='a'*64

def plan(tasks=None,**extra):
    return Plan(query='Synthetic research request',corpus_sha256=SHA,subtasks=tuple(tasks or [Subtask(subtask_id='s01',operation='retrieve',query='fictional capacity')]),**extra)


def test_frozen_fixture_and_json_roundtrip():
    fixture=Path('tests/fixtures/subtasks/plan.json').read_text()
    p=Plan.model_validate_json(fixture)
    assert p==Plan.model_validate_json(p.model_dump_json())
    assert len(p.plan_id)==64


def test_identity_changes_with_resource_policy_query_and_order():
    p=plan()
    assert p.plan_id==plan().plan_id
    assert p.plan_id!=plan(retrieval_concurrency=1).plan_id
    assert p.plan_id!=Plan(**{**p.model_dump(),'query':'A different question'}).plan_id
    with pytest.raises(ValidationError):p.query='changed'


@pytest.mark.parametrize('damage',['cycle','unknown','self','duplicate_id','duplicate_dependency'])
def test_invalid_graphs_rejected(damage):
    tasks=[dict(subtask_id='s01',operation='retrieve',query='x'),dict(subtask_id='s02',operation='retrieve',query='y')]
    if damage=='cycle':tasks[0]['dependencies']=('s02',);tasks[1]['dependencies']=('s01',)
    if damage=='unknown':tasks[0]['dependencies']=('s05',)
    if damage=='self':tasks[0]['dependencies']=('s01',)
    if damage=='duplicate_id':tasks[1]['subtask_id']='s01'
    if damage=='duplicate_dependency':tasks[1]['dependencies']=('s01','s01')
    with pytest.raises(ValidationError):plan([Subtask(**s) for s in tasks])


def test_forward_dependency_valid_but_not_a_cycle():
    p=plan([Subtask(subtask_id='s01',operation='retrieve',query='a',dependencies=('s02',)),Subtask(subtask_id='s02',operation='retrieve',query='b')])
    assert p.subtasks[0].dependencies==('s02',)


@pytest.mark.parametrize('fields',[{'retrieval_concurrency':3},{'retrieval_concurrency':True},{'deadline_seconds':181.0},{'deadline_seconds':float('nan')},{'maximum_main_calls':5},{'model_concurrency':2}])
def test_resource_escalation_invalid(fields):
    with pytest.raises(ValidationError):plan(**fields)


@pytest.mark.parametrize('kwargs',[{'operation':'retrieve'},{'operation':'retrieve','query':' '},{'operation':'retrieve','query':'x','source_ids':('s',)}, {'operation':'inspect_sources'},{'operation':'inspect_sources','source_ids':('a',),'query':'x'}])
def test_operation_inputs_invalid(kwargs):
    with pytest.raises(ValidationError):Subtask(subtask_id='s01',**kwargs)


def test_exact_source_and_result_corpus():
    identity=Identity(run_id='a'*32,attempt_id='b'*32,plan_id='c'*64,corpus_sha256=SHA)
    record=dict(source_id='known',content='Exact synthetic evidence',content_sha256=digest('Exact synthetic evidence'),corpus_sha256=SHA,role='support')
    source=Source(**record)
    result=Result(identity=identity,subtask_id='s01',child_attempt_id='d'*32,outcome='evidence',sources=(source,),elapsed_seconds=0.0)
    assert result.sources[0]==source
    with pytest.raises(ValidationError):Source(**{**record,'content':'changed'})
    with pytest.raises(ValidationError):Result(**{**result.model_dump(),'sources':(Source(**{**record,'corpus_sha256':'e'*64}),)})
    with pytest.raises(ValidationError):Result(**{**result.model_dump(),'sources':(source,source)})
    with pytest.raises(ValidationError):Result(**{**result.model_dump(),'outcome':'missing'})


def test_terminal_states_cannot_publish_new_transitions():
    for previous in TERMINAL:
        for following in ['queued','running','completed','failed','cancelled','blocked']:
            with pytest.raises(ValueError):transition(previous,following)
    transition('queued','waiting_on_dependency');transition('waiting_on_dependency','running');transition('running','completed')


def test_progress_requires_aware_time_and_sanitized_reason():
    args=dict(identity=Identity(run_id='a'*32,attempt_id='b'*32,plan_id='c'*64,corpus_sha256=SHA),subtask_id='s01',child_attempt_id='d'*32,ordinal=1,status='running')
    assert Progress(**args,created_at=datetime.now(timezone.utc))
    with pytest.raises(ValidationError):Progress(**args,created_at=datetime.now())
    with pytest.raises(ValidationError):Progress(**args,created_at=datetime.now(timezone.utc),reason='raw secret exception')



def test_blank_parent_query_and_empty_plan_rejected():
    with pytest.raises(ValidationError):Plan(query='   ',corpus_sha256=SHA,subtasks=plan().subtasks)
    with pytest.raises(ValidationError):Plan(query='Valid question',corpus_sha256=SHA,subtasks=())
