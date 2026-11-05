"""E integration: actual API/storage, synthetic branches, no real reviewer/model."""
from test_pilot_identity import configured,headers
from test_subtask_progress_api import seed,fixed_result
from src.pilot.subtasks.scheduler import run_plan


def test_progress_read_never_bypasses_parent_review_or_revision_controls(configured):
    app,client,calls,_=configured
    store=app.state.store;rid,aid,plan,sink=seed(store,'a'*64)
    run_plan(plan,rid,aid,fixed_result,event=sink,is_current=sink.current)
    url=f'/api/runs/{rid}'
    before=store.get(rid)
    snapshot=client.get(url+'/progress',headers=headers('reader')).json()
    assert snapshot['run']['status']=='running'
    assert all(b['status']=='completed' for b in snapshot['progress']['branches'])
    assert snapshot['progress']['phase']=='awaiting_composition'
    assert store.get(rid)==before
    review={'revision':0,'decision':'approve','reviewer':'reviewer-test','support_confirmed':True}
    assert client.post(url+'/review',headers=headers('reviewer'),json=review).status_code==422
    assert client.post(url+'/review',headers=headers('reviewer'),json={**review,'revision':1}).status_code==409
    assert client.get(url+'/export',headers=headers('reviewer')).status_code==409
    source={'synthetic':{'source_id':'synthetic','title':'Synthetic source','content':'Synthetic fact','page_num':6}}
    draft={'title':'Synthetic checked candidate','claims':[{'text':'Synthetic fact','source_ids':['synthetic']}],'warnings':[]}
    store.save_draft(rid,draft,source,{'model_calls':0},attempt_id=aid)
    ready=client.get(url+'/progress',headers=headers('reader')).json()
    assert ready['run']['status']=='needs_review' and ready['run']['revision']==1
    assert client.post(url+'/review',headers=headers('reviewer'),json={**review,'revision':1}).status_code==200
    cached=client.get(url+'/export',headers=headers('reviewer')).content
    assert b'PDF page 7' in cached
    assert client.get(url+'/progress',headers=headers('reader')).json()['run']['status']=='approved'
    assert client.get(url+'/export',headers=headers('reviewer')).content==cached
    edited=client.put(url+'/draft',headers=headers('analyst'),json={'revision':1,'draft':{**draft,'title':'Synthetic edited revision'}})
    assert edited.status_code==200
    assert client.post(url+'/review',headers=headers('reviewer'),json={**review,'revision':1}).status_code==409
    assert client.get(url+'/export',headers=headers('reviewer')).status_code==409
    with store.connection() as db:
        assert db.execute('SELECT content FROM exports WHERE run_id=? AND revision=1',(rid,)).fetchone()[0].encode()==cached
    assert calls==[]
