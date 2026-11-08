"""Packaged opt-in runner smoke with D's deterministic callbacks; no inference."""
import hashlib,json,multiprocessing,sys,threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from src.pilot.store import Store,Conflict
from src.pilot.schemas import ResearchRequest,ReviewRequest
from src.pilot.subtasks.contracts import Plan,Subtask
from src.pilot.subtasks.runner import run_stored_plan
import subtask_integration_child as worker


def denied(fn):
    try:fn()
    except (Conflict,ValueError):return
    raise AssertionError('Invalid approval/export accepted')


def main():
    root=Path('/state');store=Store(root/'smoke.sqlite3')
    if '--verify' in sys.argv:
        saved=json.loads((root/'expected.json').read_text());row=store.get(saved['id'])
        assert hashlib.sha256(store.export(saved['id'])[0].encode()).hexdigest()==saved['export_sha256']
        assert row['status']=='approved'
        print(json.dumps({'restart_cached_export_preserved':True,'actual_provider_calls':0}));return
    corpus=root/'corpus.json';corpus.write_text(json.dumps([{'feed_id':f's{i:02}','clean_content':f'Fictional measure {i} was 12 units.'} for i in (1,2)]))
    digest=hashlib.sha256(corpus.read_bytes()).hexdigest()
    plan=Plan(query='Compare fictional measures',corpus_sha256=digest,subtasks=tuple(Subtask(subtask_id=f's{i:02}',operation='retrieve',query=f'measure{i}') for i in (1,2)))
    rid,_=store.create(ResearchRequest(query=plan.query,request_key='F-container-synthetic'),digest)
    ctx=multiprocessing.get_context('spawn');entered=[ctx.Event(),ctx.Event()];release=[ctx.Semaphore(0),ctx.Semaphore(0)]
    with ThreadPoolExecutor(1) as caller:
        future=caller.submit(run_stored_plan,store,rid,plan,corpus,worker.RunnerOperation(entered,release),worker.fixed_composer,worker.allow_safety)
        try:
            assert all(e.wait(30) for e in entered),'Both independent branches must enter before release'
            release[1].release();release[0].release();future.result(timeout=40)
        finally:
            for gate in release:gate.release()
    row=store.get(rid);assert row['status']=='needs_review' and row['revision']==1
    assert [c['source_ids'] for c in row['draft']['claims']]==[['s01'],['s02']]
    denied(lambda:store.export(rid))
    denied(lambda:store.review(rid,ReviewRequest(revision=0,decision='approve',reviewer='synthetic-F',support_confirmed=True)))
    store.review(rid,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-F',support_confirmed=True))
    content,revision=store.export(rid);assert (content,revision)==store.export(rid)
    (root/'expected.json').write_text(json.dumps({'id':rid,'export_sha256':hashlib.sha256(content.encode()).hexdigest()}))
    empty,_=store.create(ResearchRequest(query='No available fictional evidence',request_key='F-container-empty'),digest)
    store.claim(empty)
    store.save_draft(empty,{'title':'Unavailable','claims':[],'warnings':['Missing evidence']},{},{})
    denied(lambda:store.review(empty,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-F',support_confirmed=True)))
    denied(lambda:store.export(empty))
    edited,_=store.create(ResearchRequest(query='Edit a fictional measure',request_key='F-container-edited'),digest)
    store.claim(edited)
    store.save_draft(edited,row['draft'],row['sources'],{})
    store.review(edited,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-F',support_confirmed=True))
    store.save_draft(edited,row['draft'],row['sources'],{},expected_revision=1)
    denied(lambda:store.review(edited,ReviewRequest(revision=1,decision='approve',reviewer='synthetic-F',support_confirmed=True)))
    denied(lambda:store.export(edited))
    print(json.dumps({'owned_runner_overlap':True,'ordered_aggregation':True,'stale_approval_blocked':True,'empty_approval_export_blocked':True,'synthetic_decisions_only':True,'actual_provider_calls':0,'logical_model_callbacks':1,'logical_safety_callbacks':1}))


if __name__=='__main__':main()
