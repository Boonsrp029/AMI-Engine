"""Controlled SQLite transaction ordering for D review/export races."""
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import threading
import pytest
from src.pilot.store import Conflict
from src.pilot.schemas import ReviewRequest
from test_subtasks_execution_integration import reviewed_candidate


@pytest.mark.parametrize('pair',['review_edit','export_edit'])
@pytest.mark.parametrize('first',['decision','edit'])
def test_transaction_order_preserves_exact_revision(tmp_path,monkeypatch,pair,first):
    store,rid,draft,source=reviewed_candidate(tmp_path)
    review=ReviewRequest(revision=1,decision='approve',reviewer='synthetic-D',support_confirmed=True)
    if pair=='export_edit':store.review(rid,review)
    connection=store.connection;local=threading.local();held=threading.Event();second=threading.Event();release=threading.Event()
    class Proxy:
        def __init__(self,db):self.db=db
        def __getattr__(self,name):return getattr(self.db,name)
        def execute(self,sql,*args):
            if sql.startswith('BEGIN IMMEDIATE'):
                if getattr(local,'role',None)=='second':second.set()
                result=self.db.execute(sql,*args)
                if getattr(local,'role',None)=='first':held.set();assert release.wait(10)
                return result
            return self.db.execute(sql,*args)
    @contextmanager
    def controlled():
        with connection() as db:yield Proxy(db)
    monkeypatch.setattr(store,'connection',controlled)
    def action(kind,role):
        local.role=role
        try:
            if kind=='edit':return ('edited',store.save_draft(rid,draft,{source.source_id:source.model_dump()},{},expected_revision=1))
            if pair=='review_edit':store.review(rid,review);return ('approved',1)
            return ('exported',store.export(rid))
        except Conflict:return ('conflict',None)
    with ThreadPoolExecutor(2) as pool:
        a=pool.submit(action,first,'first')
        try:
            assert held.wait(10)
            b=pool.submit(action,'edit' if first=='decision' else 'decision','second')
            assert second.wait(10);assert not b.done()
            release.set();results=[a.result(timeout=10),b.result(timeout=10)]
        finally:release.set()
    row=store.get(rid);assert row['revision']==2 and row['status']=='needs_review'
    with pytest.raises(Conflict):store.export(rid)
    if first=='edit':assert results[1][0]=='conflict'
    elif pair=='review_edit':assert results[0]==('approved',1)
    else:
        assert results[0][0]=='exported' and results[0][1][1]==1
        with store.connection() as db:
            saved=db.execute('SELECT content FROM exports WHERE run_id=? AND revision=1',(rid,)).fetchone()
            assert saved['content']==results[0][1][0]
