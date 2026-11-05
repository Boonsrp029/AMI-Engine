"""Read-only progress snapshots; fixed workers and controlled SQLite barriers."""
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import json,threading,uuid
import pytest
from test_pilot_identity import configured,headers
from src.pilot.schemas import ResearchRequest
from src.pilot.store import Store
from src.pilot.subtasks.contracts import Plan,Subtask
from src.pilot.subtasks.persistence import AttemptSink,progress_view
from src.pilot.subtasks.scheduler import run_plan


def seed(store,sha):
    p=Plan(query='Synthetic analyst question',corpus_sha256=sha,
        subtasks=(Subtask(subtask_id='s01',operation='retrieve',query='fact'),
            Subtask(subtask_id='s02',operation='inspect_sources',source_ids=('synthetic',),dependencies=('s01',),required=False)))
    rid,_=store.create(ResearchRequest(query=p.query,request_key='progress-api-case'),sha)
    aid=uuid.uuid4().hex;store.claim(rid,aid);sink=AttemptSink(store,p,rid,aid);sink.start()
    return rid,aid,p,sink


def fixed_result(ctx):
    from src.pilot.subtasks.contracts import Result,Source,digest
    text='Synthetic fact'
    return Result(identity=ctx.identity,subtask_id=ctx.task.subtask_id,child_attempt_id=ctx.child_attempt_id,
        dependencies=ctx.dependency_refs,outcome='evidence',elapsed_seconds=0.,sources=(Source(source_id='synthetic',
        content=text,content_sha256=digest(text),corpus_sha256=ctx.identity.corpus_sha256,role='support'),))


@pytest.mark.parametrize('role',['reader','analyst','reviewer','operator'])
def test_endpoint_get_permissions_and_no_mutation(configured,role):
    app,client,calls,_=configured;store=app.state.store
    rid,aid,p,sink=seed(store,'a'*64)
    before=store.get(rid)
    response=client.get(f'/api/runs/{rid}/progress',headers=headers(role));assert response.status_code==200
    data=response.json();assert data['run']==before and data['sequence']==before['events'][-1]['seq']
    view=data['progress'];assert view['availability']=='available' and view['plan_id']==p.plan_id
    assert view['attempt_id']==aid and view['run_id']==rid and view['parent_status']=='running'
    assert view['branches'][1]['depends_on']==['s01'] and view['branches'][1]['required'] is False
    assert view['branches'][1]['operation']=='inspect_sources' and view['branches'][0]['outcome'] is None
    assert store.get(rid)==before and calls==[]
    assert client.get(f'/api/runs/{rid}/progress').status_code==403
    assert client.get(f'/api/runs/{"f"*32}/progress',headers=headers(role)).status_code==404


def test_outcomes_phases_restart_and_retry(configured):
    app,client,calls,_=configured;store=app.state.store;rid,aid,p,sink=seed(store,'a'*64)
    def view():return client.get(f'/api/runs/{rid}/progress',headers=headers('reader')).json()['progress']
    run_plan(p,rid,aid,fixed_result,event=sink,is_current=sink.current)
    assert view()['phase']=='awaiting_composition'
    assert [b['outcome'] for b in view()['branches']]==['evidence','evidence']
    sink('model_request_started',{'stage':'subtask_compose'});assert view()['phase']=='composition'
    sink('guard_invocation_started',{'stage':'subtask_safety'});assert view()['phase']=='safety'
    store.cancel(rid);assert view()['phase']=='interrupted'
    store.retry(rid);assert view()['phase']=='queued' and view()['attempt_current'] is False
    new=uuid.uuid4().hex;store.claim(rid,new)
    # Latest attempt without a plan must not inherit old branch completion.
    assert view()['attempt_id']==new and view()['branches']==[] and view()['availability']=='no_plan'
    assert calls==[]


@pytest.mark.parametrize('damage',['plan','progress','result'])
def test_malformed_projection_is_distinct_from_no_plan(configured,damage):
    app,client,_,_=configured;store=app.state.store;rid,aid,p,sink=seed(store,'a'*64)
    if damage=='plan':
        with store.connection() as db:
            db.execute("UPDATE events SET payload=? WHERE run_id=? AND kind='subtask_plan'",(json.dumps({'attempt_id':aid,'plan':{},'identity':{}}),rid))
    else:store.event(rid,'subtask_'+damage,{'attempt_id':aid,'private_error':'do-not-echo'})
    data=client.get(f'/api/runs/{rid}/progress',headers=headers('reader')).json()
    assert data['progress']['availability']=='unavailable' and data['progress']['branches']==[]
    assert 'do-not-echo' not in json.dumps(data['progress'])


def test_no_plan_and_derived_interruption(configured):
    app,client,_,_=configured;store=app.state.store
    rid,_=store.create(ResearchRequest(query='Sequential question',request_key='sequential-case'),'a'*64)
    data=client.get(f'/api/runs/{rid}/progress',headers=headers('reader')).json()
    assert data['sequence']==0 and data['progress']['availability']=='no_plan'
    rid,aid,p,sink=seed(store,'a'*64);store.recover()
    assert all(b['derived'] and b['status']=='cancelled' for b in progress_view(store.get(rid),detailed=True)['branches'])


@pytest.mark.parametrize('field',['run_id','attempt_id','plan_id','corpus_sha256','child_attempt_id','stage'])
def test_valid_shaped_wrong_identity_or_early_stage_is_unavailable(configured,field):
    app,client,_,_=configured;store=app.state.store;rid,aid,p,sink=seed(store,'a'*64)
    if field=='stage':sink('model_request_started',{'stage':'subtask_compose'})
    else:
        run_plan(p,rid,aid,fixed_result,event=sink,is_current=sink.current)
        with store.connection() as db:
            event=db.execute("SELECT seq,payload FROM events WHERE run_id=? AND kind='subtask_result' ORDER BY seq DESC LIMIT 1",(rid,)).fetchone()
            data=json.loads(event['payload'])
            if field=='child_attempt_id':data[field]='f'*32
            else:data['identity'][field]='f'*(32 if field in {'run_id','attempt_id'} else 64)
            db.execute('UPDATE events SET payload=? WHERE seq=?',(json.dumps(data),event['seq']))
    response=client.get(f'/api/runs/{rid}/progress',headers=headers('reader')).json()
    assert response['progress']['availability']=='unavailable'


def test_get_holds_one_sqlite_snapshot_during_concurrent_commit(tmp_path,monkeypatch):
    store=Store(tmp_path/'snapshot.sqlite3')
    with store.connection() as db:db.execute('PRAGMA journal_mode=WAL')
    rid,_=store.create(ResearchRequest(query='Snapshot question',request_key='snapshot-case'),'a'*64)
    entered=threading.Event();release=threading.Event();connection=store.connection
    class Proxy:
        def __init__(self,db):self.db=db
        def execute(self,sql,*args):
            cursor=self.db.execute(sql,*args)
            if sql.startswith('SELECT * FROM runs'):
                entered.set();assert release.wait(10)
            return cursor
    @contextmanager
    def controlled():
        with connection() as db:yield Proxy(db)
    monkeypatch.setattr(store,'connection',controlled)
    with ThreadPoolExecutor(1) as pool:
        pending=pool.submit(store.get,rid)
        try:
            assert entered.wait(10)
            with connection() as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute("UPDATE runs SET status='failed' WHERE id=?",(rid,))
                db.execute("INSERT INTO events(run_id,kind,payload,created) VALUES(?,?,?,?)",(rid,'synthetic','{}','synthetic'))
            release.set();row=pending.result(10)
        finally:release.set()
    assert row['status']=='queued' and row['events']==[]
