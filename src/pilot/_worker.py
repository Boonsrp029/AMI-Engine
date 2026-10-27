"""Owned process entrypoint. No database access and no heavy imports at module load."""
import json
import os
import sys
import threading
import time


MESSAGE_LIMIT = 1_048_576


class OwnerWatchdog:
    """Use an identity-bound Windows process handle, or POSIX parent identity."""
    def __init__(self, owner_pid, deadline):
        self.stopped = threading.Event()
        self.deadline = deadline
        self.close = lambda: None
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.WaitForSingleObject.restype = wintypes.DWORD
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel.CloseHandle.restype = wintypes.BOOL
            handle = kernel.OpenProcess(0x00100000, False, owner_pid)  # SYNCHRONIZE only.
            if not handle:
                raise RuntimeError("Cannot monitor the worker owner")
            self.alive = lambda: kernel.WaitForSingleObject(handle, 0) == 0x102
            self.close = lambda: kernel.CloseHandle(handle)
        else:
            self.alive = lambda: os.getppid() == owner_pid
        self.thread = threading.Thread(target=self.watch, daemon=True, name="ami-owner-watchdog")
        self.thread.start()

    def watch(self):
        try:
            while not self.stopped.wait(0.1):
                if time.monotonic() >= self.deadline:
                    os._exit(124)
                if not self.alive():
                    os._exit(125)
        finally:
            self.close()

    def stop(self):
        self.stopped.set()
        self.thread.join(timeout=1)


def send(connection, kind, payload):
    encoded = json.dumps({"kind": kind, "payload": payload}, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MESSAGE_LIMIT:
        raise ValueError("Worker message exceeds its bound")
    connection.send_bytes(encoded)


def run(job, connection):
    watchdog = None
    try:
        watchdog = OwnerWatchdog(job["owner_pid"], job["deadline"])
        from src.pilot.launch import configure_event_loop
        configure_event_loop()
        from src.pilot.engine import Corpus, PilotEngine
        corpus = Corpus(job["corpus_path"])
        if corpus.sha != job["corpus_sha"]:
            raise ValueError("Pinned worker corpus changed")
        result = PilotEngine(corpus).run(job["query"], lambda kind, payload: send(
            connection, "event", {"event": kind, "data": payload}))
        send(connection, "result", result)
    except Exception as exc:
        try:
            send(connection, "failure", {"type": type(exc).__name__})
        except Exception:
            pass
        raise SystemExit(1) from None
    finally:
        connection.close()
        # Keep the daemon watchdog alive through interpreter/native cleanup.
        # The OS releases its handle on process exit; stopping it here would
        # leave cleanup hangs unmonitored if the parent subsequently died.
