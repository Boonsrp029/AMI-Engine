"""Existing-event-table adapter; no schema changes or worker-side database access."""
import json

from .contracts import Identity, Plan, Progress, Result, TERMINAL
from src.pilot.store import Conflict, now


class AttemptSink:
    def __init__(self,store,plan,run_id,attempt_id):
        self.store,self.plan=store,Plan.model_validate_json(plan.model_dump_json())
        self.identity=Identity(run_id=run_id,attempt_id=attempt_id,plan_id=plan.plan_id,corpus_sha256=plan.corpus_sha256)
        row=store.get(run_id)
        if row['query']!=plan.query or row['corpus_sha']!=plan.corpus_sha256:
            raise Conflict('Subtask plan differs from parent request')

    def current(self):
        with self.store.connection() as db:
            return self.store._current_attempt(db,self.identity.run_id,self.identity.attempt_id)

    def start(self):
        # Registration and duplicate exclusion share the current-attempt transaction.
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if not self.store._current_attempt(db,self.identity.run_id,self.identity.attempt_id):
                raise Conflict('Subtask parent attempt is no longer current')
            previous=db.execute("SELECT payload FROM events WHERE run_id=? AND kind='subtask_plan'",(self.identity.run_id,))
            if any(json.loads(row['payload']).get('attempt_id')==self.identity.attempt_id for row in previous):
                raise Conflict('A subtask plan is already registered for this attempt')
            payload={'identity':self.identity.model_dump(),'plan':self.plan.model_dump(mode='json'),'attempt_id':self.identity.attempt_id}
            db.execute('INSERT INTO events(run_id,kind,payload,created) VALUES(?,?,?,?)',
                (self.identity.run_id,'subtask_plan',json.dumps(payload),now()))

    def _write(self,kind,payload):
        if not self.store.attempt_event(self.identity.run_id,self.identity.attempt_id,kind,payload):
            raise Conflict('Subtask parent attempt is no longer current')

    def __call__(self,kind,payload):
        if kind in {'model_request_started','guard_invocation_started'}:
            expected='subtask_compose' if kind=='model_request_started' else 'subtask_safety'
            if payload!={'stage':expected}:raise ValueError('Invalid stage marker')
            self._write(kind,payload);return
        if kind=='subtask_progress': value=Progress.model_validate_json(json.dumps(payload))
        elif kind=='subtask_result':value=Result.model_validate_json(json.dumps(payload))
        else:raise ValueError('Unsupported subtask event')
        if value.identity!=self.identity or value.subtask_id not in {t.subtask_id for t in self.plan.subtasks}:
            raise Conflict('Subtask event identity mismatch')
        self._write(kind,value.model_dump(mode='json'))


def progress_view(row):
    """Read-only view of latest attempt; interruption overlays are explicitly derived.

    No result is restarted or silently credited after an interrupted parent.
    """
    attempts=[e['payload']['attempt_id'] for e in row['events'] if e['kind']=='attempt_started']
    if not attempts:return {'attempt_id':None,'branches':[]}
    attempt=attempts[-1];states={};order=[];plan_id=None
    for event in row['events']:
        p=event['payload']
        if p.get('attempt_id')!=attempt:continue
        if event['kind']=='subtask_plan':
            plan_id=p['identity']['plan_id'];order=[t['subtask_id'] for t in p['plan']['subtasks']]
        elif event['kind']=='subtask_progress':
            value=Progress.model_validate_json(json.dumps({k:v for k,v in p.items() if k!='attempt_id'}))
            if value.identity.attempt_id!=attempt or value.identity.plan_id!=plan_id:
                raise ValueError('Persisted subtask identity mismatch')
            states[value.subtask_id]={'subtask_id':value.subtask_id,'status':value.status,'reason':value.reason,'derived':False}
    for sid in order:
        if sid not in states:states[sid]={'subtask_id':sid,'status':'queued','reason':'none','derived':True}
        if row['status'] not in {'running'} and states[sid]['status'] not in TERMINAL:
            states[sid]={'subtask_id':sid,'status':'cancelled','reason':'interrupted','derived':True}
    return {'attempt_id':attempt,'plan_id':plan_id,'branches':[states[s] for s in order]}
