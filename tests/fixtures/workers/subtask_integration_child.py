"""Spawnable D-only synthetic coordinator, no inference or external service."""
def blocked_branch(database,plan_json,run_id,attempt_id,connection):
    from src.pilot.store import Store
    from src.pilot.subtasks.contracts import Plan,Result,Source,digest
    from src.pilot.subtasks.scheduler import run_plan
    from src.pilot.subtasks.persistence import AttemptSink
    plan=Plan.model_validate_json(plan_json);store=Store(database);sink=AttemptSink(store,plan,run_id,attempt_id)
    def operation(ctx):
        connection.send({'stage':'entered','child_attempt_id':ctx.child_attempt_id})
        connection.recv()  # Parent controls this boundary; never timed by sleeps.
        text='Synthetic resumed branch evidence'
        return Result(identity=ctx.identity,subtask_id=ctx.task.subtask_id,child_attempt_id=ctx.child_attempt_id,
            outcome='evidence',sources=(Source(source_id='fixed',content=text,content_sha256=digest(text),corpus_sha256=plan.corpus_sha256,role='support'),),elapsed_seconds=0.0)
    try:run_plan(plan,run_id,attempt_id,operation,event=sink,is_current=sink.current)
    finally:connection.close()
class RunnerOperation:
    def __init__(self,entered,release,mode='normal'):
        self.entered,self.release,self.mode=entered,release,mode
    def __call__(self,ctx):
        from src.pilot.subtasks.contracts import Result,Source,digest
        i=int(ctx.task.subtask_id[-1])-1
        self.entered[i].set()
        self.release[i].acquire()  # Deliberately non-cooperative; owned process must contain it.
        text=f'Fictional measure {i+1} was 12 units.'
        source=Source(source_id=ctx.task.subtask_id,content=text,content_sha256=digest(text),corpus_sha256=ctx.identity.corpus_sha256,role='support')
        return Result(identity=ctx.identity,subtask_id=ctx.task.subtask_id,child_attempt_id=ctx.child_attempt_id,
            dependencies=ctx.dependency_refs,outcome='evidence',sources=(source,),elapsed_seconds=0.0)


def fixed_composer(report,access):
    return access.main(lambda:{'title':'Synthetic owned-process brief','claims':[
        {'text':s.source.content,'source_ids':[s.source.source_id]} for s in report.sources],'warnings':[]})


def excessive_composer(report,access):
    for _ in range(5):access.main(lambda:None)
    raise AssertionError('Fifth callback should have been rejected')


def allow_safety(draft,sources):return True

def reject_safety(draft,sources):return False
