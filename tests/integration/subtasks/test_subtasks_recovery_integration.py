"""D process recovery and fault-boundary integration; isolated synthetic storage."""
import importlib
import multiprocessing
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from src.pilot.store import Store,Conflict
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.persistence import AttemptSink,progress_view
from src.pilot.schemas import ResearchRequest,ReviewRequest
from test_subtasks_execution_integration import setup,result,start,SHA


def test_killed_coordinator_recovers_history_and_explicit_retry(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(str(Path('tests/fixtures/workers').resolve()))
    worker=importlib.import_module('subtask_integration_child')
    store,plan,rid,aid,sink=setup(tmp_path,count=1)
    old,_=store.create(ResearchRequest(query='Preserve approved synthetic history',request_key='preserved-history'),SHA)
    assert store.claim(old,uuid.uuid4().hex)
    draft={'title':'Preserved synthetic brief','claims':[{'text':'Synthetic history','source_ids':['s']}],'warnings':[]}
    store.save_draft(old,draft,{'s':{'source_id':'s','content':'Synthetic history'}},{})
    store.review(old,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-D',support_confirmed=True));cached=store.export(old)
    ctx=multiprocessing.get_context('spawn');parent,child=ctx.Pipe()
    process=ctx.Process(target=worker.blocked_branch,args=(str(store.path),plan.model_dump_json(),rid,aid,child))
    process.start();child.close()
    try:
        assert parent.poll(15),'Child never reached controlled operation boundary'
        message=parent.recv();assert message['stage']=='entered' and process.is_alive()
        process.terminate();process.join(10);assert not process.is_alive()
        recovered=Store(store.path);recovered.recover()
        assert recovered.get(rid)['status']=='interrupted' and recovered.get(rid)['draft'] is None
        assert progress_view(recovered.get(rid))['branches'][0]['status']=='cancelled'
        assert recovered.export(old)==cached
        recovered.retry(rid);new=uuid.uuid4().hex;assert recovered.claim(rid,new)
        current=AttemptSink(recovered,plan,rid,new);current.start()
        report=run_plan(plan,rid,new,result,event=current,is_current=current.current)
        assert report.can_compose
        assert not recovered.attempt_event(rid,aid,'late',{})
        assert len([e for e in recovered.get(rid)['events'] if e['kind']=='subtask_result'])==1
        assert recovered.export(old)==cached
    finally:
        if process.is_alive():process.terminate();process.join(10)
        parent.close();process.close()


def test_parent_cancel_never_starts_queued_branch(tmp_path):
    args=setup(tmp_path,cap=1);entered=threading.Event();release=threading.Event();second=threading.Event()
    def operation(ctx):
        if ctx.task.subtask_id=='s02':second.set()
        entered.set();assert release.wait(10);return result(ctx)
    with ThreadPoolExecutor(1) as pool:
        future=start(pool,args,operation)
        try:
            assert entered.wait(10);args[0].cancel(args[2]);release.set()
            try:future.result(timeout=10)
            except Conflict:pass
        finally:release.set()
    assert not second.is_set()
    assert not [e for e in args[0].get(args[2])['events'] if e['kind']=='subtask_result']


def test_sink_failure_cannot_return_success_or_create_draft(tmp_path):
    store,plan,rid,aid,sink=setup(tmp_path,count=1)
    def failed_sink(kind,payload):
        if kind=='subtask_result':raise OSError('Synthetic persistence outage')
        sink(kind,payload)
    with pytest.raises(OSError):run_plan(plan,rid,aid,result,event=failed_sink,is_current=sink.current)
    store.finish_attempt(rid,aid,'invalid_message')
    assert store.get(rid)['status']=='failed' and store.get(rid)['draft'] is None
    with pytest.raises(Conflict):store.export(rid)


def test_cross_branch_source_collision_prevents_aggregate_publication(tmp_path):
    store,plan,rid,aid,sink=setup(tmp_path)
    def operation(ctx):
        answer=result(ctx);source=answer.sources[0].model_copy(update={'source_id':'collision'})
        return answer.model_copy(update={'sources':(source,)})
    with pytest.raises(ValueError,match='collision'):
        run_plan(plan,rid,aid,operation,event=sink,is_current=sink.current)
    assert store.get(rid)['draft'] is None
    with pytest.raises(Conflict):store.export(rid)
