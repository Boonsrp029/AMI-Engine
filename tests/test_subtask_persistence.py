"""Temporary real SQLite history; synthetic work only, no actual owner decisions."""
import threading,uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from src.pilot.store import Store,Conflict
from src.pilot.schemas import ResearchRequest,ReviewRequest
from src.pilot.subtasks.contracts import Plan,Subtask,Result,Source,digest
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.persistence import AttemptSink,progress_view

SHA='a'*64

def setup(tmp_path):
    store=Store(tmp_path/'pilot.sqlite3')
    p=Plan(query='Synthetic analyst question',corpus_sha256=SHA,subtasks=(Subtask(subtask_id='s01',operation='retrieve',query='synthetic fact'),))
    rid,_=store.create(ResearchRequest(query=p.query,request_key='synthetic-key'),SHA)
    aid=uuid.uuid4().hex;assert store.claim(rid,aid)
    sink=AttemptSink(store,p,rid,aid);sink.start()
    return store,p,rid,aid,sink


def answer(ctx):
    return Result(identity=ctx.identity,subtask_id=ctx.task.subtask_id,child_attempt_id=ctx.child_attempt_id,
        outcome='evidence',sources=(Source(source_id='synthetic',content='Synthetic fact',content_sha256=digest('Synthetic fact'),corpus_sha256=SHA,role='support'),),elapsed_seconds=0.0)


def test_persisted_completion_review_revision_and_cached_export(tmp_path):
    store,p,rid,aid,sink=setup(tmp_path)
    report=run_plan(p,rid,aid,answer,event=sink,is_current=sink.current)
    assert report.can_compose
    view=progress_view(store.get(rid));assert view['branches'][0]['status']=='completed'
    draft={'title':'Synthetic brief','claims':[{'text':'Synthetic fact','source_ids':['synthetic']}],'warnings':[]}
    sources={s.source.source_id:s.source.model_dump() for s in report.sources}
    store.save_draft(rid,draft,sources,{'synthetic':True,'model_calls':0},attempt_id=aid)
    with pytest.raises(Conflict):store.export(rid)
    store.review(rid,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-reviewer',support_confirmed=True))
    old=store.export(rid);assert store.export(rid)==old
    store.save_draft(rid,{**draft,'title':'Edited synthetic brief'},sources,{},expected_revision=1)
    with pytest.raises(Conflict):store.export(rid)
    with pytest.raises(Conflict):store.review(rid,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-reviewer',support_confirmed=True))
    with store.connection() as db:assert db.execute('SELECT content FROM exports WHERE run_id=?',(rid,)).fetchone()[0]==old[0]


@pytest.mark.parametrize('stop',['cancel','restart'])
def test_durable_stop_rejects_late_completion_and_preserves_history(tmp_path,stop):
    store,p,rid,aid,sink=setup(tmp_path);entered=threading.Event();release=threading.Event();done=threading.Event()
    def worker(ctx):
        entered.set()
        try:assert release.wait(5);return answer(ctx)
        finally:done.set()
    with ThreadPoolExecutor(1) as owner:
        future=owner.submit(run_plan,p,rid,aid,worker,event=sink,is_current=sink.current)
        try:
            assert entered.wait(5)
            if stop=='cancel':store.cancel(rid)
            else:store.recover()
            history=store.get(rid)['events']
            with pytest.raises(Conflict):future.result(5)
            assert store.get(rid)['events']==history
            assert store.get(rid)['revision']==0
            view=progress_view(store.get(rid));assert view['branches'][0]=={'subtask_id':'s01','status':'cancelled','reason':'interrupted','derived':True}
        finally:release.set();assert done.wait(5)
    assert not any(e['kind']=='subtask_result' for e in store.get(rid)['events'])
    store.retry(rid);newaid=uuid.uuid4().hex;assert store.claim(rid,newaid)
    assert not store.attempt_event(rid,aid,'subtask_result',{})
    with pytest.raises(Conflict):sink.start()
    new=AttemptSink(store,p,rid,newaid);new.start()
    report=run_plan(p,rid,newaid,answer,event=new,is_current=new.current)
    assert report.can_compose and progress_view(store.get(rid))['attempt_id']==newaid


def test_wrong_parent_plan_cannot_register(tmp_path):
    store,p,rid,aid,sink=setup(tmp_path)
    other=Plan(**{**p.model_dump(),'query':'Different question'})
    with pytest.raises(Conflict):AttemptSink(store,other,rid,aid)


def test_duplicate_registration_cannot_launch_second_plan(tmp_path):
    store,p,rid,aid,sink=setup(tmp_path)
    before=store.get(rid)['events']
    with pytest.raises(Conflict,match='already registered'):AttemptSink(store,p,rid,aid).start()
    assert store.get(rid)['events']==before
