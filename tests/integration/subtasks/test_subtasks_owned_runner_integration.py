"""D tests the real owned-process runner; all callbacks are importable fixed code."""
import hashlib
import importlib
import json
import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from src.pilot.schemas import ResearchRequest,ReviewRequest
from src.pilot.store import Store,Conflict
from src.pilot.subtasks.contracts import Plan,Subtask
from src.pilot.subtasks.runner import run_stored_plan


def fixture(tmp_path,monkeypatch,count=2):
    monkeypatch.syspath_prepend(str(Path('tests/fixtures/workers').resolve()))
    worker=importlib.import_module('subtask_integration_child');ctx=multiprocessing.get_context('spawn')
    entered=[ctx.Event() for _ in range(count)];release=[ctx.Semaphore(0) for _ in range(count)]
    corpus=tmp_path/'corpus.json';corpus.write_text(json.dumps([{'feed_id':f's{i:02}','clean_content':f'Fictional measure {i} was 12 units.'} for i in range(1,count+1)]))
    sha=hashlib.sha256(corpus.read_bytes()).hexdigest()
    plan=Plan(query='Compare fictional measures',corpus_sha256=sha,subtasks=tuple(Subtask(subtask_id=f's{i:02}',operation='retrieve',query=f'measure{i}') for i in range(1,count+1)))
    store=Store(tmp_path/'history.sqlite3');rid,_=store.create(ResearchRequest(query=plan.query,request_key='D-owned-process'),sha)
    return worker,entered,release,corpus,plan,store,rid


@pytest.mark.parametrize('mode',['success','safety','budget','corpus','cancel'])
def test_owned_runner_overlap_faults_and_no_late_draft(tmp_path,monkeypatch,mode):
    worker,entered,release,corpus,plan,store,rid=fixture(tmp_path,monkeypatch)
    cancellation=threading.Event()
    with ThreadPoolExecutor(1) as caller:
        future=caller.submit(run_stored_plan,store,rid,plan,corpus,worker.RunnerOperation(entered,release),
            worker.excessive_composer if mode=='budget' else worker.fixed_composer,
            worker.reject_safety if mode=='safety' else worker.allow_safety,cancellation=cancellation)
        try:
            assert entered[0].wait(30) and entered[1].wait(30),'Both branches must enter before either is released'
            if mode=='corpus':corpus.write_text('[]')
            if mode=='cancel':
                cancellation.set()
                with pytest.raises((ValueError,RuntimeError,Conflict)):future.result(timeout=15)
                # Both operations remain blocked: successful cancellation required killing the owned process.
            else:
                release[1].release();release[0].release()
                if mode=='success':future.result(timeout=20)
                else:
                    with pytest.raises((ValueError,RuntimeError,Conflict)):future.result(timeout=20)
        finally:
            cancellation.set()
            for gate in release:gate.release()
    row=store.get(rid)
    pid=next(e['payload']['pid'] for e in row['events'] if e['kind']=='subtask_worker_started')
    assert pid not in {p.pid for p in multiprocessing.active_children()}
    if mode=='success':
        assert row['status']=='needs_review' and row['revision']==1
        assert [c['source_ids'] for c in row['draft']['claims']]==[['s01'],['s02']]
        assert row['metrics']['model_calls']==1 and row['metrics']['guardrail_invocations']==1
        with pytest.raises(Conflict):store.export(rid)
        store.review(rid,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-D',support_confirmed=True))
        assert store.export(rid)==store.export(rid)
    else:
        assert row['status'] in {'failed','interrupted'} and row['revision']==0 and row['draft'] is None
        with pytest.raises(Conflict):store.export(rid)
        if mode=='budget':assert row['metrics']['model_calls']==4
        if mode=='safety':assert row['metrics']['guardrail_invocations']==1
        if mode=='corpus':assert row['metrics']['failure_reason']=='corpus_changed'
        if mode=='cancel':assert row['status']=='interrupted'
        if mode=='cancel':
            previous=[e['payload']['attempt_id'] for e in row['events'] if e['kind']=='attempt_started']
            store.retry(rid)
            for gate in release:gate.release()
            run_stored_plan(store,rid,plan,corpus,worker.RunnerOperation(entered,release),worker.fixed_composer,worker.allow_safety)
            current=store.get(rid)
            assert current['status']=='needs_review'
            assert [e['payload']['attempt_id'] for e in current['events'] if e['kind']=='attempt_started'][-1] not in previous
            assert not store.attempt_event(rid,previous[0],'late',{})
