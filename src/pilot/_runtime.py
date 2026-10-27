"""Single-instance SQLite queue dispatcher with owned, fenced process attempts."""
from datetime import datetime, timezone
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import re
import sys
import threading
import time
import traceback
import uuid

from src.pilot._worker import MESSAGE_LIMIT, run
from src.pilot.store import Conflict


class RuntimeLease:
    def __init__(self, database):
        self.path = Path(str(database) + ".runtime.lock")
        self.file = None

    def acquire(self):
        handle = self.path.open("a+b")
        try:
            handle.seek(0, 2)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            raise RuntimeError("Another analyst runtime owns this database") from None
        self.file = handle

    def release(self):
        if self.file is not None:
            self.file.close()  # OS releases the process-owned lock; never delete a lock file.
            self.file = None


class ProcessRuntime:
    def __init__(self, store, corpus_path, corpus_sha, *, deadline_seconds=180, worker=run):
        if not 0 < deadline_seconds <= 180:
            raise ValueError("Execution deadline must be positive and no greater than 180 seconds")
        self.store, self.corpus_path, self.corpus_sha = store, str(Path(corpus_path).resolve()), corpus_sha
        self.deadline_seconds, self.worker = deadline_seconds, worker
        self.context = multiprocessing.get_context("spawn")
        self.lease = RuntimeLease(store.path)
        self.stopping, self.wake = threading.Event(), threading.Event()
        self.lock = threading.RLock()
        self.active, self.thread = None, None

    def start(self):
        if self.thread is not None:
            raise RuntimeError("Analyst runtime already started")
        self.lease.acquire()
        try:
            self.store.recover()
            self.thread = threading.Thread(target=self.dispatch, daemon=True, name="ami-dispatcher")
            self.thread.start()
        except Exception:
            self.lease.release()
            raise

    def submit(self, run_id):
        if self.stopping.is_set():
            raise RuntimeError("Analyst runtime is stopping")
        self.wake.set()  # Persisted SQLite queue, not an in-memory work queue.

    @staticmethod
    def stop_process(process):
        if process.pid is None:
            return
        if process.is_alive():
            process.kill()
        process.join(timeout=5)
        if process.is_alive():
            raise RuntimeError("Owned worker could not be stopped")

    def cancel(self, run_id):
        with self.lock:
            elapsed = time.monotonic() - self.active["started"] if self.active and self.active["run_id"] == run_id else None
            attempt_id = self.store.cancel(run_id, elapsed_seconds=elapsed)
            if self.active and self.active["run_id"] == run_id and self.active["attempt_id"] == attempt_id:
                self.stop_process(self.active["process"])
        self.wake.set()

    def shutdown(self):
        if self.lease.file is None:
            return
        self.stopping.set()
        self.wake.set()
        with self.lock:
            if self.active:
                active = self.active
                self.stop_process(active["process"])
                self.store.finish_attempt(active["run_id"], active["attempt_id"], "shutdown", time.monotonic() - active["started"])
        if self.thread is not None:
            self.thread.join(timeout=10)
            if self.thread.is_alive():
                raise RuntimeError("Analyst dispatcher did not stop")
        self.store.recover("Application stopped; safe retry is available")
        self.lease.release()

    def dispatch(self):
        while not self.stopping.is_set():
            pending = self.store.next_queued()
            if pending is None:
                self.wake.wait(0.2)
                self.wake.clear()
                continue
            try:
                self.execute(pending)
            except Exception:
                # Unexpected controller failures must not trigger an automatic retry.
                self.stopping.set()
                break

    def execute(self, pending):
        run_id, attempt_id = pending["id"], uuid.uuid4().hex
        started = time.monotonic()
        receiver, sender = self.context.Pipe(duplex=False)
        process, reason, candidate = None, None, None
        try:
            with self.lock:
                if self.stopping.is_set() or not self.store.claim(run_id, attempt_id):
                    return
                if pending["corpus_sha"] != self.corpus_sha or hashlib.sha256(Path(self.corpus_path).read_bytes()).hexdigest() != self.corpus_sha:
                    reason = "corpus_changed"
                    return
                job = {"query": pending["query"], "owner_pid": os.getpid(), "deadline": started + self.deadline_seconds,
                       "corpus_path": self.corpus_path, "corpus_sha": self.corpus_sha}
                process = self.context.Process(target=self.worker, args=(job, sender), daemon=True, name="ami-workflow")
                process.start()
                sender.close()
                self.active = {"run_id": run_id, "attempt_id": attempt_id, "process": process, "started": started}
                self.store.attempt_event(run_id, attempt_id, "worker_started", {"pid": process.pid, "deadline_seconds": self.deadline_seconds})
            messages, pipe_open = 0, True
            while True:
                if time.monotonic() >= started + self.deadline_seconds:
                    reason = "deadline"
                    break
                if self.stopping.is_set():
                    reason = "shutdown"
                    break
                ready = False
                if pipe_open:
                    try:
                        ready = receiver.poll(0.05)
                    except (BrokenPipeError, EOFError):
                        pipe_open = False  # Windows may signal sender closure from poll().
                if ready:
                    try:
                        message = json.loads(receiver.recv_bytes(maxlength=MESSAGE_LIMIT).decode("utf-8"))
                    except (EOFError, BrokenPipeError):
                        pipe_open = False
                        continue
                    messages += 1
                    if messages > 128 or not isinstance(message, dict) or set(message) != {"kind", "payload"} or not isinstance(message["payload"], dict):
                        reason = "invalid_message"
                        break
                    kind, payload = message["kind"], message["payload"]
                    if kind == "event" and candidate is None and set(payload) == {"event", "data"} and isinstance(payload["event"], str) and re.fullmatch(r"[a-z_]{1,80}", payload["event"]) and isinstance(payload["data"], dict):
                        if not self.store.attempt_event(run_id, attempt_id, payload["event"], payload["data"]):
                            break
                    elif kind == "result" and candidate is None and {"draft", "sources", "metrics"} <= payload.keys():
                        candidate = payload
                    elif kind == "failure":
                        reason = "worker_error"
                        break
                    else:
                        reason = "invalid_message"
                        break
                    continue  # Drain buffered messages before inspecting process exit.
                # multiprocessing Process polling/reaping is not safe concurrently
                # with cancellation's kill/join on the same object (POSIX waitpid).
                # Every lifecycle access shares the owner's lock.
                with self.lock:
                    exited = not process.is_alive()
                    if exited:
                        process.join(timeout=1)
                        if process.exitcode != 0:
                            reason = "deadline" if process.exitcode == 124 else "worker_exit"
                if exited:
                    break
                if not pipe_open:
                    time.sleep(0.02)
            if self.stopping.is_set() and reason is None:
                reason = "shutdown"
            if reason is None and candidate is not None:
                if hashlib.sha256(Path(self.corpus_path).read_bytes()).hexdigest() != self.corpus_sha:
                    reason = "corpus_changed"
                elif candidate["metrics"].get("corpus_sha256") != self.corpus_sha:
                    reason = "invalid_message"
                else:
                    metrics = {**candidate["metrics"], "attempt_id": attempt_id, "execution_elapsed_seconds": time.monotonic() - started,
                               "queue_wait_seconds": max(0, (datetime.now(timezone.utc) - datetime.fromisoformat(pending["updated"])).total_seconds() - (time.monotonic() - started)),
                               "execution_deadline_seconds": self.deadline_seconds}
                    self.store.save_draft(run_id, candidate["draft"], candidate["sources"], metrics, attempt_id=attempt_id)
            elif reason is None:
                reason = "worker_exit"
        except Conflict:
            pass  # Cancellation/retry won the persisted state transition; never accept a late result.
        except Exception as exc:
            reason = "invalid_message"
            self.store.attempt_event(run_id, attempt_id, "runtime_failure", {"type": type(exc).__name__,
                "locations": [{"function": frame.name, "line": frame.lineno} for frame in traceback.extract_tb(exc.__traceback__)]})
        finally:
            with self.lock:
                if process is not None:
                    self.stop_process(process)
            receiver.close()
            sender.close()
            if reason is not None:
                self.store.finish_attempt(run_id, attempt_id, reason, time.monotonic() - started)
            with self.lock:
                if self.active and self.active["attempt_id"] == attempt_id:
                    self.active = None
