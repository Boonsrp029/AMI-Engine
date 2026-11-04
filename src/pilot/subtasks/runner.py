"""Explicit-plan owned-process runner. Trusted adapters only; no default LLM client."""
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import threading
import time
import uuid

from src.pilot._runtime import RuntimeLease, ProcessRuntime
from src.pilot._worker import send, OwnerWatchdog, MESSAGE_LIMIT, isolate_console
from src.pilot.schemas import validate_citations
from src.pilot.store import Conflict
from .contracts import Plan
from .persistence import AttemptSink
from .scheduler import run_plan


class ModelAccess:
    """One serialized callback at a time; four main calls, one safety invocation.

    Adapters must route their provider calls through main(). This is a trusted
    integration API, not a sandbox for arbitrary Python code.
    """
    def __init__(self,deadline,event=lambda *_:None):
        self.deadline=deadline;self.calls=0;self.guards=0;self.lock=threading.Lock();self.event=event

    def _call(self,fn,guard):
        with self.lock:
            if time.monotonic()>=self.deadline:raise TimeoutError('Parent deadline')
            if guard:
                if self.guards>=1:raise RuntimeError('Safety budget exhausted')
                self.guards+=1
            else:
                if self.calls>=4:raise RuntimeError('Main call budget exhausted')
                self.calls+=1
            self.event('guard_invocation_started' if guard else 'model_request_started',{'stage':'subtask_safety' if guard else 'subtask_compose'})
            value=fn()
            if time.monotonic()>=self.deadline:raise TimeoutError('Parent deadline')
            return value

    def main(self,fn):return self._call(fn,False)
    def guard(self,fn):return self._call(fn,True)


def _corpus(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _child(job,connection,operation,compose,safety):
    try:
        isolate_console()
        watchdog=OwnerWatchdog(job['owner_pid'],job['deadline'])
        plan=Plan.model_validate_json(job['plan'])
        if _corpus(job['corpus_path'])!=plan.corpus_sha256:raise ValueError('Corpus changed')
        event=lambda k,p:send(connection,'event',{'event':k,'data':p})
        report=run_plan(plan,job['run_id'],job['attempt_id'],operation,event=event,deadline_at=job['deadline'])
        if not report.can_compose:raise ValueError('Required branch or deadline failed')
        access=ModelAccess(job['deadline'],event)
        draft=compose(report,access)
        sources={s.source.source_id:s.source.model_dump() for s in report.sources}
        if report.missing_branches:
            draft={**draft,'warnings':list(draft.get('warnings',[]))+[f'Subtask {sid} did not complete; this brief is partial.' for sid in report.missing_branches]}
        draft=validate_citations(draft,sources)
        # Empty-claim abstention preserves the existing no-safety-call policy.
        if draft['claims'] and access.guard(lambda:safety(draft,sources)) is not True:
            raise ValueError('Safety rejected draft')
        if _corpus(job['corpus_path'])!=plan.corpus_sha256:raise ValueError('Corpus changed')
        metrics={'corpus_sha256':plan.corpus_sha256,'plan_id':plan.plan_id,'workflow':'ami-subtasks-v1',
            'model_calls':access.calls,'guardrail_invocations':access.guards,'token_usage_complete':False,
            'missing_branches':list(report.missing_branches)}
        send(connection,'result',{'draft':draft,'sources':sources,'metrics':metrics})
    except Exception as exc:
        try:send(connection,'failure',{'type':type(exc).__name__})
        except Exception:pass
        raise SystemExit(1) from None
    finally:connection.close()


def run_stored_plan(store,run_id,plan,corpus_path,operation,compose,safety,*,cancellation=None):
    """Explicit opt-in; callback functions/objects must be spawn-pickleable.

    Parent is the sole DB writer and waits for a clean child exit before saving.
    Reuses the sequential runtime lease, preventing whole-request overlap.
    """
    plan=Plan.model_validate_json(plan.model_dump_json())
    lease=RuntimeLease(store.path);lease.acquire()
    attempt=uuid.uuid4().hex;process=None;receiver=sender=None;claimed=False
    started=time.monotonic();deadline=started+plan.deadline_seconds;reason='worker_error'
    try:
        if not store.claim(run_id,attempt):raise Conflict('Parent is not queued')
        claimed=True;sink=AttemptSink(store,plan,run_id,attempt);sink.start()
        if _corpus(corpus_path)!=plan.corpus_sha256:reason='corpus_changed';raise ValueError('Corpus changed')
        ctx=multiprocessing.get_context('spawn');receiver,sender=ctx.Pipe(duplex=False)
        job={'owner_pid':os.getpid(),'deadline':deadline,'plan':plan.model_dump_json(),'run_id':run_id,
            'attempt_id':attempt,'corpus_path':str(Path(corpus_path).resolve())}
        process=ctx.Process(target=_child,args=(job,sender,operation,compose,safety),daemon=True)
        process.start();sender.close()
        if not store.attempt_event(run_id,attempt,'subtask_worker_started',{'pid':process.pid}):raise Conflict('Parent stopped')
        candidate=None;pipe_open=True;messages=0;counts={'model_request_started':0,'guard_invocation_started':0}
        while True:
            if cancellation is not None and cancellation.is_set():reason='canceled';break
            if not sink.current():raise Conflict('Parent stopped or superseded')
            if time.monotonic()>=deadline:reason='deadline';break
            try: ready=pipe_open and receiver.poll(.02)
            except (BrokenPipeError,EOFError,OSError):
                pipe_open=False;ready=False
            if ready:
                try:message=json.loads(receiver.recv_bytes(MESSAGE_LIMIT).decode('utf-8'))
                except (EOFError,BrokenPipeError):pipe_open=False;continue
                messages+=1
                if messages>128 or set(message)!={'kind','payload'}:raise ValueError('Invalid worker message')
                kind,payload=message['kind'],message['payload']
                if kind=='event' and candidate is None:
                    if payload['event'] in counts:
                        counts[payload['event']]+=1
                        if counts['model_request_started']>4 or counts['guard_invocation_started']>1:raise ValueError('Worker call budget exceeded')
                    sink(payload['event'],payload['data'])
                elif kind=='result' and candidate is None:candidate=payload
                else:raise ValueError('Worker failed or invalid message')
                continue
            if not process.is_alive():
                process.join()
                if process.exitcode!=0 or candidate is None:
                    if process.exitcode==124:reason='deadline'
                    break
                if _corpus(corpus_path)!=plan.corpus_sha256:reason='corpus_changed';break
                if candidate['metrics']['corpus_sha256']!=plan.corpus_sha256:break
                if candidate['metrics']['model_calls']!=counts['model_request_started'] or candidate['metrics']['guardrail_invocations']!=counts['guard_invocation_started']:raise ValueError('Call accounting mismatch')
                store.save_draft(run_id,candidate['draft'],candidate['sources'],
                    {**candidate['metrics'],'attempt_id':attempt,'execution_elapsed_seconds':time.monotonic()-started},attempt_id=attempt)
                return attempt
            if not pipe_open:time.sleep(.01)
        raise RuntimeError('Concurrent parent failed')
    finally:
        try:
            if process is not None:ProcessRuntime.stop_process(process)
            if claimed:store.finish_attempt(run_id,attempt,reason,time.monotonic()-started)
        finally:
            if receiver is not None:receiver.close()
            if sender is not None:sender.close()
            lease.release()
