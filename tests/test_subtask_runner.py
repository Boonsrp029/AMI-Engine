"""Spawned synthetic operations; no model client and no actual human decisions."""
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import hashlib,multiprocessing,threading,time
from pathlib import Path
import pytest
from src.pilot.schemas import ResearchRequest,ReviewRequest
from src.pilot.store import Store,Conflict
from src.pilot.subtasks.contracts import Plan,Subtask,Result,Source,digest
from src.pilot.subtasks.runner import run_stored_plan

BARRIER=threading.Barrier(2)

@dataclass
class Operation:
    mode:str='overlap'
    marker:str=''
    def __call__(self,ctx):
        if self.mode=='overlap':BARRIER.wait(5)
        if self.mode=='hang':
            Path(self.marker).write_text('entered');threading.Event().wait(60)
        if self.mode=='fail':raise RuntimeError('synthetic failure')
        if self.mode=='change':Path(self.marker).write_text('changed')
        return Result(identity=ctx.identity,subtask_id=ctx.task.subtask_id,child_attempt_id=ctx.child_attempt_id,
            dependencies=ctx.dependency_refs,outcome='evidence',sources=(Source(source_id=ctx.task.subtask_id,
                content='Synthetic fact '+ctx.task.subtask_id,content_sha256=digest('Synthetic fact '+ctx.task.subtask_id),
                corpus_sha256=ctx.identity.corpus_sha256,role='support'),),elapsed_seconds=0.0)


def compose(report,access):
    return access.main(lambda:{'title':'Synthetic brief','claims':[{'text':s.source.content,'source_ids':[s.source.source_id]} for s in report.sources],'warnings':[]})


def reject(draft,sources):return False

def allow(draft,sources):return True

def exceed(report,access):
    for i in range(5):access.main(lambda:None)


def setup(tmp_path,n=2,deadline=180.0):
    file=tmp_path/'corpus.json';file.write_text('[]');sha=hashlib.sha256(file.read_bytes()).hexdigest()
    plan=Plan(query='Synthetic question',corpus_sha256=sha,deadline_seconds=deadline,
        subtasks=tuple(Subtask(subtask_id=f's{i:02}',operation='retrieve',query='synthetic') for i in range(1,n+1)))
    store=Store(tmp_path/'history.sqlite3');rid,_=store.create(ResearchRequest(query=plan.query,request_key='synthetic-run'),sha)
    return store,rid,plan,file


def test_spawned_overlap_pipeline_and_review_export(tmp_path):
    store,rid,plan,file=setup(tmp_path)
    run_stored_plan(store,rid,plan,file,Operation(),compose,allow)
    row=store.get(rid);assert row['status']=='needs_review' and row['metrics']['model_calls']==1 and row['metrics']['guardrail_invocations']==1
    assert len(row['draft']['claims'])==2
    with pytest.raises(Conflict):store.export(rid)
    store.review(rid,ReviewRequest(revision=1,decision='approve',reviewer='synthetic',support_confirmed=True))
    assert store.export(rid)==store.export(rid)


@pytest.mark.parametrize('mode',['safety','budget','branch','corpus'])
def test_pipeline_failure_never_saves_draft(tmp_path,mode):
    store,rid,plan,file=setup(tmp_path,n=1)
    op=Operation('change',str(file)) if mode=='corpus' else Operation('fail' if mode=='branch' else 'normal')
    with pytest.raises(Exception):run_stored_plan(store,rid,plan,file,op,exceed if mode=='budget' else compose,reject if mode=='safety' else allow)
    row=store.get(rid);assert row['status']=='failed' and row['revision']==0
    if mode=='budget':assert row['metrics']['model_calls']==4
    with pytest.raises(Conflict):store.export(rid)


def test_cancel_reaps_noncooperative_owned_worker(tmp_path):
    store,rid,plan,file=setup(tmp_path,n=1);marker=tmp_path/'entered';cancel=threading.Event()
    with ThreadPoolExecutor(1) as caller:
        f=caller.submit(run_stored_plan,store,rid,plan,file,Operation('hang',str(marker)),compose,allow,cancellation=cancel)
        try:
            until=time.monotonic()+15
            while not marker.exists() and time.monotonic()<until:cancel.wait(.02)
            assert marker.exists();cancel.set()
            with pytest.raises(Exception):f.result(10)
        finally:cancel.set()
    row=store.get(rid);assert row['status']=='interrupted' and row['revision']==0
    pid=next(e['payload']['pid'] for e in row['events'] if e['kind']=='subtask_worker_started')
    assert pid not in {p.pid for p in multiprocessing.active_children()}


def test_parent_deadline_prevents_late_finalization(tmp_path):
    store,rid,plan,file=setup(tmp_path,n=1,deadline=3.0)
    with pytest.raises(Exception):run_stored_plan(store,rid,plan,file,Operation('hang',str(tmp_path/'entered')),compose,allow)
    row=store.get(rid);assert row['status']=='failed' and row['revision']==0 and row['metrics']['failure_reason']=='deadline'

def test_model_access_serializes_concurrent_adapter_calls():
    from src.pilot.subtasks.runner import ModelAccess
    gateway=ModelAccess(time.monotonic()+30)
    entered=threading.Event();release=threading.Event();attempting=threading.Event();second_started=threading.Event()
    def first():entered.set();assert release.wait(5);return 1
    def second():attempting.set();return gateway.main(lambda:second_started.set() or 2)
    with ThreadPoolExecutor(2) as workers:
        a=workers.submit(gateway.main,first)
        try:
            assert entered.wait(5);b=workers.submit(second);assert attempting.wait(5)
            assert not second_started.is_set();release.set();assert a.result(5)==1 and b.result(5)==2
        finally:release.set()
    assert gateway.calls==2
