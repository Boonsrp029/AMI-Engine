"""Existing-event-table adapter; no schema changes or worker-side database access."""
import json

from .contracts import Identity, Plan, Progress, Result, DependencyRef, TERMINAL, transition, digest
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
        payload=value.model_dump(mode='json')
        with self.store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if not self.store._current_attempt(db,self.identity.run_id,self.identity.attempt_id):
                raise Conflict('Subtask parent attempt is no longer current')
            history=[]
            for row in db.execute('SELECT kind,payload FROM events WHERE run_id=? ORDER BY seq',(self.identity.run_id,)):
                record=json.loads(row['payload'])
                if record.get('attempt_id')==self.identity.attempt_id:
                    history.append((row['kind'],{k:v for k,v in record.items() if k!='attempt_id'}))
            if not any(k=='subtask_plan' and v['identity']==self.identity.model_dump() for k,v in history):
                raise Conflict('No plan registered for this attempt')
            progress=[v for k,v in history if k=='subtask_progress']
            same=[v for v in progress if v['subtask_id']==value.subtask_id]
            if kind=='subtask_progress':
                previous=next((v for v in progress if v['ordinal']==value.ordinal),None)
                if previous is not None:
                    if previous==payload:return
                    raise Conflict('Progress ordinal was reused with different data')
                if value.ordinal!=len(progress)+1:raise Conflict('Progress ordinal is out of order')
                if same:
                    if same[-1]['child_attempt_id']!=value.child_attempt_id:raise Conflict('Child attempt changed')
                    transition(same[-1]['status'],value.status)
                elif value.status!='queued':raise Conflict('First child status must be queued')
            else:
                if not same or same[-1]['status']!='completed' or same[-1]['child_attempt_id']!=value.child_attempt_id:
                    raise Conflict('Result requires matching completed child')
                prior=[v for k,v in history if k=='subtask_result' and v['subtask_id']==value.subtask_id]
                if prior:
                    if prior[-1]==payload:return
                    raise Conflict('Completed result cannot be replaced')
            db.execute('INSERT INTO events(run_id,kind,payload,created) VALUES(?,?,?,?)',
                (self.identity.run_id,kind,json.dumps({**payload,'attempt_id':self.identity.attempt_id}),now()))


def progress_view(row, *, detailed=False):
    """Read-only view of latest attempt; interruption overlays are explicitly derived.

    No result is restarted or silently credited after an interrupted parent.
    """
    try:
        view=_project_progress(row)
    except (ValueError,KeyError,TypeError,AttributeError):
        if not detailed:raise
        return {'availability':'unavailable','mode':'unavailable','run_id':row['id'],
            'parent_status':row['status'],'corpus_sha256':row['corpus_sha'],
            'attempt_id':None,'plan_id':None,'plan':None,'phase':'unavailable',
            'branches':[],'reason':'invalid_progress_records','attempt_current':False}
    if detailed:return view
    legacy={'attempt_id':view['attempt_id'],'branches':[
        {k:branch[k] for k in ('subtask_id','status','reason','derived')} for branch in view['branches']]}
    if view['attempt_id'] is not None:legacy['plan_id']=view['plan_id']
    return legacy


def _project_progress(row):
    attempts=[e['payload']['attempt_id'] for e in row['events'] if e['kind']=='attempt_started']
    attempt=attempts[-1] if attempts else None
    view={'availability':'no_plan','mode':'sequential','run_id':row['id'],
        'parent_status':row['status'],'corpus_sha256':row['corpus_sha'],
        'attempt_id':attempt,'plan_id':None,'plan':None,'branches':[],
        'phase':row['status'],'reason':'no_subtask_plan',
        'attempt_current':attempt is not None and row['status']!='queued'}
    if attempt is None:
        if any(e['kind'] in {'subtask_plan','subtask_progress','subtask_result'} for e in row['events']):
            raise ValueError('Subtask records lack a parent attempt')
        submissions=[e['payload'] for e in row['events'] if e['kind']=='subtask_submission']
        if len(submissions)>1:raise ValueError('Duplicate workflow submission')
        if submissions:
            submission=submissions[0]
            plan=Plan.model_validate_json(json.dumps(submission['plan']))
            if (submission.get('workflow')!='bounded_subtasks' or submission.get('plan_id')!=plan.plan_id
                    or plan.query!=row['query'] or plan.corpus_sha256!=row['corpus_sha']):
                raise ValueError('Submitted workflow plan identity mismatch')
            if row['status']=='queued':
                status,reason='queued','none'
            elif row['status']=='interrupted':
                status,reason='cancelled','interrupted'
            else:
                status,reason='failed','operation_failed'
            branches=[{'subtask_id':task.subtask_id,'operation':task.operation,
                'required':task.required,'depends_on':list(task.dependencies),'status':status,
                'reason':reason,'derived':True,'child_attempt_id':None,'outcome':None}
                for task in plan.subtasks]
            view.update(availability='available',mode='subtasks',reason='none',
                plan_id=plan.plan_id,
                plan={'plan_id':plan.plan_id,**plan.model_dump(mode='json',exclude={'query','subtasks','corpus_sha256'}),
                    'subtask_count':len(plan.subtasks)},
                branches=branches,phase=row['status'],attempt_current=False)
        return view
    Identity(run_id=row['id'],attempt_id=attempt,plan_id='0'*64,corpus_sha256=row['corpus_sha'])
    history=[e for e in row['events'] if e['payload'].get('attempt_id')==attempt]
    plans=[e['payload'] for e in history if e['kind']=='subtask_plan']
    if not plans:
        if any(e['kind'] in {'subtask_progress','subtask_result'} for e in history):
            raise ValueError('Subtask records lack a plan')
        return view
    if len(plans)!=1:raise ValueError('Duplicate attempt plan')
    plan=Plan.model_validate_json(json.dumps(plans[0]['plan']))
    identity=Identity(run_id=row['id'],attempt_id=attempt,plan_id=plan.plan_id,corpus_sha256=row['corpus_sha'])
    if Identity.model_validate_json(json.dumps(plans[0]['identity']))!=identity or plan.query!=row['query'] or plan.corpus_sha256!=row['corpus_sha']:
        raise ValueError('Persisted plan identity mismatch')
    submissions=[e['payload'] for e in row['events'] if e['kind']=='subtask_submission']
    if submissions and (len(submissions)!=1 or submissions[0].get('plan_id')!=plan.plan_id
            or Plan.model_validate_json(json.dumps(submissions[0].get('plan'))).plan_id!=plan.plan_id):
        raise ValueError('Attempt plan differs from submitted workflow')
    tasks={t.subtask_id:t for t in plan.subtasks};states={};children={};outcomes={};results={};ordinal=0
    phase='retrieval'
    for event in history:
        p=event['payload']
        if event['kind']=='subtask_progress':
            value=Progress.model_validate_json(json.dumps({k:v for k,v in p.items() if k!='attempt_id'}))
            if value.identity!=identity or value.subtask_id not in tasks or value.ordinal!=ordinal+1:
                raise ValueError('Persisted subtask identity mismatch')
            sid=value.subtask_id;ordinal=value.ordinal
            if sid in states:
                transition(states[sid]['status'],value.status)
                if children[sid]!=value.child_attempt_id:raise ValueError('Child attempt changed')
            elif value.status!='queued':raise ValueError('First child state is not queued')
            children[sid]=value.child_attempt_id
            states[value.subtask_id]={'subtask_id':value.subtask_id,'status':value.status,'reason':value.reason,'derived':False}
        elif event['kind']=='subtask_result':
            result=Result.model_validate_json(json.dumps({k:v for k,v in p.items() if k!='attempt_id'}))
            sid=result.subtask_id
            if result.identity!=identity or states.get(sid,{}).get('status')!='completed' or children.get(sid)!=result.child_attempt_id or sid in outcomes:
                raise ValueError('Result differs from completed child')
            expected=tuple(DependencyRef(subtask_id=d,child_attempt_id=results[d].child_attempt_id,
                result_sha256=digest(results[d].model_dump_json())) for d in tasks[sid].dependencies)
            if result.dependencies!=expected:raise ValueError('Result dependency provenance mismatch')
            results[sid]=result
            outcomes[sid]=result.outcome
        elif event['kind']=='model_request_started' and p.get('stage')=='subtask_compose':phase='composition'
        elif event['kind']=='guard_invocation_started' and p.get('stage')=='subtask_safety':phase='safety'
    for sid,task in tasks.items():
        if sid not in states:states[sid]={'subtask_id':sid,'status':'queued','reason':'none','derived':True}
        if row['status'] not in {'running'} and states[sid]['status'] not in TERMINAL:
            states[sid]={'subtask_id':sid,'status':'cancelled','reason':'interrupted','derived':True}
        states[sid].update(operation=task.operation,required=task.required,depends_on=list(task.dependencies),
            child_attempt_id=children.get(sid),outcome=outcomes.get(sid))
    if phase in {'composition','safety'} and (any(s['status'] not in TERMINAL for s in states.values())
            or any(t.required and states[sid]['status']!='completed' for sid,t in tasks.items())
            or any(s['status']=='completed' and sid not in outcomes for sid,s in states.items())):
        raise ValueError('Composition marker precedes accepted branch results')
    if row['status']!='running':phase=row['status']
    elif phase=='retrieval' and len(outcomes)==len(tasks):phase='awaiting_composition'
    view.update(availability='available',mode='subtasks',reason='none',plan_id=plan.plan_id,
        plan={'plan_id':plan.plan_id,**plan.model_dump(mode='json',exclude={'query','subtasks','corpus_sha256'}),
              'subtask_count':len(tasks)},branches=list(states.values()),phase=phase)
    return view
