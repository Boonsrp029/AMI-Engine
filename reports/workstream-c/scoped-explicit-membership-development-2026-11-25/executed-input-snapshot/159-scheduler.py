"""Coordinator-owned bounded branch execution. No models, database or public API."""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import dataclass
from datetime import datetime, timezone
import threading
import time
import uuid

from .contracts import Plan, Identity, Subtask, Result, Progress, DependencyRef, TERMINAL, transition, digest


@dataclass(frozen=True)
class Context:
    identity: Identity
    task: Subtask
    child_attempt_id: str
    dependencies: tuple[Result, ...]
    deadline: float
    cancellation: threading.Event
    parent_cancellation: threading.Event
    clock: object

    def cancelled(self):
        return self.cancellation.is_set() or self.parent_cancellation.is_set() or self.clock() >= self.deadline

    @property
    def dependency_refs(self):
        return tuple(DependencyRef(subtask_id=r.subtask_id, child_attempt_id=r.child_attempt_id,
            result_sha256=digest(r.model_dump_json())) for r in self.dependencies)


@dataclass(frozen=True)
class AggregateSource:
    source: object
    origins: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class Report:
    identity: Identity
    status: str
    states: tuple[tuple[str, str], ...]
    results: tuple[Result, ...]
    sources: tuple[AggregateSource, ...]
    missing_branches: tuple[str, ...]
    can_compose: bool


def aggregate(results):
    """Plan/rank order, retaining per-branch support/context roles."""
    sources, positions, origins = [], {}, []
    for result in results:
        for source in result.sources:
            if source.source_id in positions:
                i = positions[source.source_id]
                if sources[i].model_dump(exclude={'role'}) != source.model_dump(exclude={'role'}):
                    raise ValueError('Source identity collision')
                origins[i].append((result.subtask_id, source.role))
            else:
                positions[source.source_id] = len(sources)
                sources.append(source); origins.append([(result.subtask_id, source.role)])
    return tuple(AggregateSource(s,tuple(o)) for s,o in zip(sources,origins))


def run_plan(plan, run_id, attempt_id, operation, *, event=lambda *_: None,
             cancellation=None, clock=time.monotonic, is_current=lambda: True, deadline_at=None):
    """Opt-in internal runner. Caller owns attempt-fenced persistence and hard process stop.

    Operations receive a Context and return a Result. They must cooperate with
    cancellation; timed-out threads are never accepted or counted as free slots.
    No callback is called from worker threads. A sink failure aborts the runner.
    """
    plan = Plan.model_validate_json(plan.model_dump_json())
    identity = Identity(run_id=run_id,attempt_id=attempt_id,plan_id=plan.plan_id,corpus_sha256=plan.corpus_sha256)
    cancel = cancellation if cancellation is not None else threading.Event()
    started = clock(); deadline = started + plan.deadline_seconds
    if deadline_at is not None: deadline = min(deadline,deadline_at)
    states = {}; results = {}; contexts = {}; futures = {}; ordinal = 0; abort = None
    pool = ThreadPoolExecutor(max_workers=plan.retrieval_concurrency, thread_name_prefix='ami-subtask')

    def publish(task, state, reason='none'):
        nonlocal ordinal
        if task.subtask_id in states: transition(states[task.subtask_id],state)
        states[task.subtask_id] = state; ordinal += 1
        progress = Progress(identity=identity,subtask_id=task.subtask_id,
            child_attempt_id=contexts[task.subtask_id].child_attempt_id,ordinal=ordinal,
            status=state,created_at=datetime.now(timezone.utc),reason=reason)
        event('subtask_progress',progress.model_dump(mode='json'))

    try:
        for task in plan.subtasks:
            contexts[task.subtask_id] = Context(identity,task,uuid.uuid4().hex,(),deadline,threading.Event(),cancel,clock)
            publish(task,'queued')
            if task.dependencies: publish(task,'waiting_on_dependency')
        while any(s not in TERMINAL for s in states.values()):
            now = clock()
            if not is_current(): cancel.set()
            if cancel.is_set(): abort = 'cancelled'
            elif now >= deadline: abort = 'deadline'
            # Check every active deadline before accepting any completion.
            for task in plan.subtasks:
                sid = task.subtask_id
                if states[sid]=='running' and now >= contexts[sid].deadline:
                    contexts[sid].cancellation.set();publish(task,'failed','branch_deadline')
            # Propagate failures even through optional ancestors.
            changed = True
            while changed:
                changed = False
                for task in plan.subtasks:
                    if states[task.subtask_id] in {'queued','waiting_on_dependency'} and any(
                            states[d] in {'failed','cancelled','blocked'} for d in task.dependencies):
                        publish(task,'blocked','dependency_failed');changed = True
            if any(t.required and states[t.subtask_id] in {'failed','blocked','cancelled'} for t in plan.subtasks):
                abort = abort or 'failed'
            if abort:
                for task in plan.subtasks:
                    if states[task.subtask_id] not in TERMINAL:
                        contexts[task.subtask_id].cancellation.set()
                        publish(task,'cancelled','parent_deadline' if abort=='deadline' else ('required_branch_failed' if abort=='failed' else 'parent_cancelled'))
                break
            for task in plan.subtasks:
                sid = task.subtask_id
                f = futures.get(sid)
                if states[sid]!='running' or f is None or not f.done(): continue
                try:
                    raw = f.result()
                    value = Result.model_validate_json(raw.model_dump_json())
                    ctx = contexts[sid]
                    if (value.identity != identity or value.subtask_id != sid or value.child_attempt_id != ctx.child_attempt_id
                            or value.dependencies != ctx.dependency_refs):
                        raise ValueError('Result does not match launched attempt')
                except Exception:
                    publish(task,'failed','operation_failed')
                    if task.required: break
                else:
                    # Cancellation may have arrived while parsing a completion.
                    if not is_current(): cancel.set()
                    if cancel.is_set():
                        contexts[sid].cancellation.set();publish(task,'cancelled','parent_cancelled')
                    elif clock() >= contexts[sid].deadline:
                        contexts[sid].cancellation.set();publish(task,'failed','branch_deadline')
                    else:
                        results[sid] = value
                        publish(task,'completed')
                        event('subtask_result',value.model_dump(mode='json'))
            if any(t.required and states[t.subtask_id]=='failed' for t in plan.subtasks): continue
            for task in plan.subtasks:
                sid = task.subtask_id
                if states[sid] not in {'queued','waiting_on_dependency'}: continue
                if not all(states[d]=='completed' for d in task.dependencies): continue
                # An expired thread retains its slot until it actually exits.
                if max(sum(not f.done() for f in futures.values()),sum(s=='running' for s in states.values())) >= plan.retrieval_concurrency: break
                if cancel.is_set() or clock() >= deadline: break
                ctx = contexts[sid]
                contexts[sid] = Context(identity,task,ctx.child_attempt_id,tuple(results[d] for d in task.dependencies),
                    min(deadline,clock()+task.timeout_seconds),ctx.cancellation,cancel,clock)
                publish(task,'running')
                futures[sid] = pool.submit(operation,contexts[sid])
            pending = [f for f in futures.values() if not f.done()]
            if pending: wait(pending,timeout=.01,return_when=FIRST_COMPLETED)
        ordered = tuple(results[t.subtask_id] for t in plan.subtasks if t.subtask_id in results)
        missing = tuple(t.subtask_id for t in plan.subtasks if states[t.subtask_id]!='completed')
        if cancel.is_set(): abort = 'cancelled'
        elif clock() >= deadline: abort = abort or 'deadline'
        can_compose = abort is None and all(not t.required or states[t.subtask_id]=='completed' for t in plan.subtasks)
        return Report(identity,abort or ('partial' if missing else 'completed'),tuple(states.items()),ordered,
                      aggregate(ordered),missing,can_compose)
    finally:
        for ctx in contexts.values(): ctx.cancellation.set()
        pool.shutdown(wait=False,cancel_futures=True)
