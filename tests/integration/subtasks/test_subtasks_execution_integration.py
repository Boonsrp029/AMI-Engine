"""D-owned integration: real scheduler + attempt sink + SQLite, fixed workers."""
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import pytest
from src.pilot.subtasks.contracts import Plan,Subtask,Result,Source,Progress,digest
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.persistence import AttemptSink,progress_view
from src.pilot.store import Store,Conflict
from src.pilot.schemas import ResearchRequest,ReviewRequest

SHA='a'*64


def setup(tmp_path, *, count=2, optional=(), dependency=False, cap=2):
    tasks=tuple(Subtask(subtask_id=f's{i:02}',operation='retrieve',query=f'fictional measure {i}',
        required=i not in optional,dependencies=('s01',) if dependency and i==2 else ()) for i in range(1,count+1))
    plan=Plan(query='Compare fictional regional measures',corpus_sha256=SHA,subtasks=tasks,retrieval_concurrency=cap)
    store=Store(tmp_path/'history.sqlite3',queue_limit=2)
    rid,_=store.create(ResearchRequest(query=plan.query,request_key='d-integration'),SHA)
    aid=uuid.uuid4().hex;assert store.claim(rid,aid)
    sink=AttemptSink(store,plan,rid,aid);sink.start()
    return store,plan,rid,aid,sink


def result(ctx):
    text=f'Fictional measure for {ctx.task.subtask_id} was 12 units.'
    source=Source(source_id=ctx.task.subtask_id,content=text,content_sha256=digest(text),corpus_sha256=SHA,role='support')
    return Result(identity=ctx.identity,subtask_id=ctx.task.subtask_id,child_attempt_id=ctx.child_attempt_id,
        dependencies=ctx.dependency_refs,outcome='evidence',sources=(source,),elapsed_seconds=0.0)


def start(pool,args,worker,**kwargs):
    store,plan,rid,aid,sink=args
    return pool.submit(run_plan,plan,rid,aid,worker,event=sink,is_current=sink.current,**kwargs)


@pytest.mark.parametrize('cap',[1,2])
def test_real_persistence_overlap_caps_and_plan_order(tmp_path,cap):
    args=setup(tmp_path,count=3,cap=cap);entered=[threading.Event() for _ in range(3)];release=[threading.Event() for _ in range(3)]
    lock=threading.Lock();active=0;peak=0
    def worker(ctx):
        nonlocal active,peak
        i=int(ctx.task.subtask_id[-1])-1
        with lock:active+=1;peak=max(peak,active)
        entered[i].set()
        try:assert release[i].wait(10);return result(ctx)
        finally:
            with lock:active-=1
    with ThreadPoolExecutor(1) as pool:
        f=start(pool,args,worker)
        try:
            assert entered[0].wait(10)
            if cap==2:assert entered[1].wait(10)
            assert not entered[cap].is_set()
            if cap==2:
                release[1].set();assert entered[2].wait(10);release[2].set();release[0].set()
            else:
                release[0].set();assert entered[1].wait(10);release[1].set();assert entered[2].wait(10);release[2].set()
            report=f.result(timeout=10)
        finally:
            for gate in release:gate.set()
    assert peak==cap and report.can_compose
    assert [r.subtask_id for r in report.results]==['s01','s02','s03']
    row=args[0].get(args[2]);view=progress_view(row)
    assert [b['status'] for b in view['branches']]==['completed']*3
    assert len([e for e in row['events'] if e['kind']=='subtask_result'])==3


def test_dependency_result_is_durable_before_dependent_entry(tmp_path):
    args=setup(tmp_path,dependency=True)
    def worker(ctx):
        if ctx.task.subtask_id=='s02':
            events=args[0].get(args[2])['events']
            assert any(e['kind']=='subtask_result' and e['payload']['subtask_id']=='s01' for e in events)
            assert ctx.dependency_refs[0].subtask_id=='s01'
        return result(ctx)
    report=run_plan(args[1],args[2],args[3],worker,event=args[4],is_current=args[4].current)
    assert report.can_compose


@pytest.mark.parametrize('optional',[False,True])
def test_branch_failure_policy_survives_sqlite_projection(tmp_path,optional):
    args=setup(tmp_path,optional=(2,) if optional else ())
    def worker(ctx):
        if ctx.task.subtask_id=='s02':raise RuntimeError('synthetic branch failure')
        return result(ctx)
    report=run_plan(args[1],args[2],args[3],worker,event=args[4],is_current=args[4].current)
    assert report.can_compose is optional
    assert dict(report.states)['s02']=='failed'
    assert 's02' in report.missing_branches
    assert args[0].get(args[2])['draft'] is None


@pytest.mark.parametrize('stop',['cancel','recover'])
def test_parent_stop_fences_buffered_results_and_retry_history(tmp_path,stop):
    args=setup(tmp_path,count=1);store,plan,rid,aid,sink=args
    ready=threading.Event();release=threading.Event()
    def worker(ctx):
        answer=result(ctx);ready.set();assert release.wait(10);return answer
    with ThreadPoolExecutor(1) as pool:
        f=start(pool,args,worker)
        try:
            assert ready.wait(10)
            if stop=='cancel':store.cancel(rid)
            else:Store(store.path).recover()
            store.retry(rid);new=uuid.uuid4().hex;assert store.claim(rid,new)
            release.set()
            try:f.result(timeout=10)
            except Conflict:pass  # Sink explicitly rejects writes from the old attempt.
        finally:release.set()
    row=store.get(rid)
    assert not [e for e in row['events'] if e['kind']=='subtask_result']
    assert row['draft'] is None and row['revision']==0
    assert not store.attempt_event(rid,aid,'late',{})
    assert not store.finish_attempt(rid,aid,'deadline')


def test_concurrent_same_request_key_creates_exactly_one_run(tmp_path):
    store=Store(tmp_path/'duplicates.sqlite3');gate=threading.Barrier(3)
    def create():
        gate.wait(timeout=10)
        return store.create(ResearchRequest(query='Fictional independent measures',request_key='same-request-key'),SHA)
    with ThreadPoolExecutor(2) as pool:
        fs=[pool.submit(create) for _ in range(2)];gate.wait(timeout=10);values=[f.result(timeout=10) for f in fs]
    assert values[0][0]==values[1][0] and sorted(v[1] for v in values)==[False,True]
    with pytest.raises(Conflict):store.create(ResearchRequest(query='Changed request content',request_key='same-request-key'),SHA)


def test_event_redelivery_does_not_duplicate_durable_history(tmp_path):
    store,plan,rid,aid,sink=setup(tmp_path,count=1)
    child=uuid.uuid4().hex
    event=Progress(identity=sink.identity,subtask_id='s01',child_attempt_id=child,ordinal=1,status='queued',created_at=datetime.now(timezone.utc)).model_dump(mode='json')
    sink('subtask_progress',event);sink('subtask_progress',event)
    assert len([e for e in store.get(rid)['events'] if e['kind']=='subtask_progress'])==1


def test_persisted_terminal_state_cannot_be_reopened(tmp_path):
    store,plan,rid,aid,sink=setup(tmp_path,count=1);child=uuid.uuid4().hex
    for ordinal,state in enumerate(['queued','running','completed'],1):
        e=Progress(identity=sink.identity,subtask_id='s01',child_attempt_id=child,ordinal=ordinal,status=state,created_at=datetime.now(timezone.utc)).model_dump(mode='json');sink('subtask_progress',e)
    late=Progress(identity=sink.identity,subtask_id='s01',child_attempt_id=child,ordinal=4,status='running',created_at=datetime.now(timezone.utc)).model_dump(mode='json')
    with pytest.raises((Conflict,ValueError)):sink('subtask_progress',late)
    assert progress_view(store.get(rid))['branches'][0]['status']=='completed'


class Clock:
    def __init__(self):self.value=0.0;self.lock=threading.Lock()
    def __call__(self):
        with self.lock:return self.value
    def set(self,value):
        with self.lock:self.value=value


def test_deadline_rejects_ready_result_at_boundary_without_draft(tmp_path):
    args=setup(tmp_path,count=1);ready=threading.Event();release=threading.Event();clock=Clock()
    def worker(ctx):
        answer=result(ctx);ready.set();assert release.wait(10);return answer
    with ThreadPoolExecutor(1) as pool:
        f=start(pool,args,worker,clock=clock)
        try:
            assert ready.wait(10);clock.set(30.0);release.set();report=f.result(timeout=10)
        finally:release.set()
    assert not report.can_compose and not report.results
    assert not [e for e in args[0].get(args[2])['events'] if e['kind']=='subtask_result']


def test_wrong_result_corpus_never_reaches_persistence(tmp_path):
    args=setup(tmp_path,count=1)
    def worker(ctx):
        good=result(ctx)
        return good.model_copy(update={'identity':good.identity.model_copy(update={'corpus_sha256':'b'*64})})
    report=run_plan(args[1],args[2],args[3],worker,event=args[4],is_current=args[4].current)
    assert not report.can_compose
    assert not [e for e in args[0].get(args[2])['events'] if e['kind']=='subtask_result']


def reviewed_candidate(tmp_path):
    store,plan,rid,aid,sink=setup(tmp_path,count=1)
    report=run_plan(plan,rid,aid,result,event=sink,is_current=sink.current)
    assert report.can_compose
    source=report.sources[0].source
    draft={'title':'Synthetic D integration brief','claims':[{'text':source.content,'source_ids':[source.source_id]}],'warnings':[]}
    store.save_draft(rid,draft,{source.source_id:source.model_dump()}, {},attempt_id=aid)
    return store,rid,draft,source


def test_review_edit_race_cannot_approve_new_revision_with_old_decision(tmp_path):
    store,rid,draft,source=reviewed_candidate(tmp_path);gate=threading.Barrier(3)
    def review():
        gate.wait(timeout=10)
        try:store.review(rid,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-D',support_confirmed=True));return True
        except Conflict:return False
    def edit():
        gate.wait(timeout=10)
        return store.save_draft(rid,draft,{source.source_id:source.model_dump()},{},expected_revision=1)
    with ThreadPoolExecutor(2) as pool:
        rf=pool.submit(review);ef=pool.submit(edit);gate.wait(timeout=10)
        rf.result(timeout=10);assert ef.result(timeout=10)==2
    assert store.get(rid)['revision']==2 and store.get(rid)['status']=='needs_review'
    with pytest.raises(Conflict):store.export(rid)
    with pytest.raises(Conflict):store.review(rid,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-D',support_confirmed=True))


def test_cached_export_preserved_but_edit_requires_new_approval(tmp_path):
    store,rid,draft,source=reviewed_candidate(tmp_path)
    store.review(rid,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-D',support_confirmed=True))
    original=store.export(rid)
    assert original==store.export(rid)
    store.save_draft(rid,draft,{source.source_id:source.model_dump()},{},expected_revision=1)
    with pytest.raises(Conflict):store.export(rid)
    with store.connection() as db:
        row=db.execute('SELECT content FROM exports WHERE run_id=? AND revision=1',(rid,)).fetchone()
        assert row['content']==original[0]



def test_concurrent_redelivery_is_one_transactional_history_event(tmp_path):
    store,plan,rid,aid,sink=setup(tmp_path,count=1);gate=threading.Barrier(3)
    event=Progress(identity=sink.identity,subtask_id='s01',child_attempt_id=uuid.uuid4().hex,ordinal=1,status='queued',created_at=datetime.now(timezone.utc)).model_dump(mode='json')
    def deliver():
        duplicate=AttemptSink(store,plan,rid,aid);gate.wait(timeout=10);duplicate('subtask_progress',event)
    with ThreadPoolExecutor(2) as pool:
        futures=[pool.submit(deliver) for _ in range(2)];gate.wait(timeout=10)
        for future in futures:future.result(timeout=10)
    events=[e for e in store.get(rid)['events'] if e['kind']=='subtask_progress']
    assert len(events)==1 and events[0]['payload']['ordinal']==1


@pytest.mark.parametrize('damage',['ordinal','child'])
def test_conflicting_delivery_cannot_corrupt_persisted_child_history(tmp_path,damage):
    store,plan,rid,aid,sink=setup(tmp_path,count=1)
    event=Progress(identity=sink.identity,subtask_id='s01',child_attempt_id=uuid.uuid4().hex,ordinal=1,status='queued',created_at=datetime.now(timezone.utc)).model_dump(mode='json')
    sink('subtask_progress',event);before=store.get(rid)['events']
    bad={**event,'status':'running','ordinal':1 if damage=='ordinal' else 2}
    if damage=='child':bad['child_attempt_id']=uuid.uuid4().hex
    with pytest.raises((Conflict,ValueError)):sink('subtask_progress',bad)
    assert store.get(rid)['events']==before
