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
