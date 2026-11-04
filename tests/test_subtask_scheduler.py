"""Deterministic workers/barriers; no inference and no latency benchmark."""
import threading
from concurrent.futures import ThreadPoolExecutor
import pytest
from src.pilot.subtasks.contracts import Plan,Subtask,Result,Source,digest
from src.pilot.subtasks.scheduler import run_plan

SHA='a'*64

def plan(*deps, optional=()):
    return Plan(query='Synthetic question',corpus_sha256=SHA,subtasks=tuple(
        Subtask(subtask_id=f's{i:02}',operation='retrieve',query=f'query{i}',dependencies=d,required=i not in optional)
        for i,d in enumerate(deps,1)))


def result(ctx, text='Synthetic fact', source_id=None):
    return Result(identity=ctx.identity,subtask_id=ctx.task.subtask_id,child_attempt_id=ctx.child_attempt_id,
        dependencies=ctx.dependency_refs,outcome='evidence',sources=(Source(source_id=source_id or ctx.task.subtask_id,
        content=text,content_sha256=digest(text),corpus_sha256=SHA,role='support'),),elapsed_seconds=0.0)


def test_overlap_caps_dependency_and_deterministic_aggregation():
    barrier=threading.Barrier(3);release=threading.Event();third=threading.Event();events=[]
    def worker(ctx):
        if ctx.task.subtask_id in {'s01','s02'}:
            barrier.wait(timeout=5);assert release.wait(5)
        else:
            assert [r.subtask_id for r in ctx.dependencies]==['s01']
            third.set()
        return result(ctx)
    with ThreadPoolExecutor(1) as owner:
        future=owner.submit(run_plan,plan((),(),('s01',)),'a'*32,'b'*32,worker,event=lambda k,p:events.append((k,p)))
        try:
            barrier.wait(timeout=5);assert not third.is_set()
            release.set();report=future.result(5)
        finally:release.set()
    assert report.can_compose and third.is_set()
    assert [r.subtask_id for r in report.results]==['s01','s02','s03']
    assert [s.source.source_id for s in report.sources]==['s01','s02','s03']
    running=set()
    for kind,payload in events:
        if kind!='subtask_progress':continue
        if payload['status']=='running':running.add(payload['subtask_id'])
        elif payload['status'] in {'completed','failed','cancelled','blocked'}:running.discard(payload['subtask_id'])
        assert len(running)<=2


def test_parent_cancel_fences_late_worker_and_signals_token():
    entered=threading.Event();release=threading.Event();finished=threading.Event();cancel=threading.Event();events=[];seen=[]
    def worker(ctx):
        seen.append(ctx);entered.set()
        try:assert release.wait(5);return result(ctx)
        finally:finished.set()
    with ThreadPoolExecutor(1) as owner:
        future=owner.submit(run_plan,plan(()),'a'*32,'b'*32,worker,cancellation=cancel,event=lambda k,p:events.append((k,p)))
        try:
            assert entered.wait(5);cancel.set();report=future.result(5)
            before=list(events);assert not report.can_compose and seen[0].cancelled()
        finally:release.set();assert finished.wait(5)
    assert events==before and report.results==() and report.status=='cancelled'


def test_required_failure_blocks_dependent_and_prevents_composition():
    calls=[]
    def worker(ctx):calls.append(ctx.task.subtask_id);raise RuntimeError('do not disclose private details')
    report=run_plan(plan((),('s01',)),'a'*32,'b'*32,worker)
    assert report.status=='failed' and not report.can_compose
    assert dict(report.states)=={'s01':'failed','s02':'blocked'} and calls==['s01']


def test_optional_failure_reports_partial_without_losing_required_evidence():
    def worker(ctx):
        if ctx.task.subtask_id=='s02':raise RuntimeError('synthetic')
        return result(ctx)
    report=run_plan(plan((),(),optional=(2,)),'a'*32,'b'*32,worker)
    assert report.can_compose and report.status=='partial' and report.missing_branches==('s02',)


@pytest.mark.parametrize('parent',[False,True])
def test_late_completion_after_clock_deadline_is_never_published(parent):
    now=[0.0];events=[]
    def worker(ctx):now[0]=181.0 if parent else 31.0;return result(ctx)
    report=run_plan(plan(()),'a'*32,'b'*32,worker,clock=lambda:now[0],event=lambda k,p:events.append((k,p)))
    assert not report.can_compose and not report.results
    assert not any(k=='subtask_result' for k,p in events)


def test_forged_child_identity_rejected():
    def worker(ctx):return result(ctx).model_copy(update={'child_attempt_id':'f'*32})
    report=run_plan(plan(()),'a'*32,'b'*32,worker)
    assert not report.can_compose and dict(report.states)['s01']=='failed'


def test_shared_source_dedup_keeps_all_origins_and_collision_rejects():
    report=run_plan(plan((),()),'a'*32,'b'*32,lambda ctx:result(ctx,source_id='shared'))
    assert len(report.sources)==1 and report.sources[0].origins==(('s01','support'),('s02','support'))
    with pytest.raises(ValueError,match='collision'):
        run_plan(plan((),()),'a'*32,'b'*32,lambda ctx:result(ctx,text=ctx.task.query,source_id='shared'))

def test_serial_cap_waits_for_first_branch_completion():
    entered=threading.Event();release=threading.Event();second=threading.Event()
    p=plan((),()).model_copy(update={'retrieval_concurrency':1})
    def worker(ctx):
        if ctx.task.subtask_id=='s01':entered.set();assert release.wait(5)
        else:second.set()
        return result(ctx)
    with ThreadPoolExecutor(1) as owner:
        f=owner.submit(run_plan,p,'a'*32,'b'*32,worker)
        try:assert entered.wait(5);assert not second.is_set();release.set();assert f.result(5).can_compose
        finally:release.set()
    assert second.is_set()


def test_optional_failed_dependency_blocks_required_descendant():
    report=run_plan(plan((),('s01',),optional=(1,)),'a'*32,'b'*32,lambda _:(_ for _ in ()).throw(ValueError('synthetic')))
    assert not report.can_compose and dict(report.states)=={'s01':'failed','s02':'blocked'}


def test_sink_failure_prevents_branch_launch():
    called=[]
    def sink(*_):raise RuntimeError('synthetic persistence failure')
    with pytest.raises(RuntimeError):run_plan(plan(()),'a'*32,'b'*32,lambda ctx:called.append(ctx),event=sink)
    assert called==[]
