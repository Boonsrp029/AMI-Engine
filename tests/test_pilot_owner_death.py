"""Kill only a disposable owned parent; verify its monitored synthetic child exits."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest


@pytest.mark.skipif(sys.platform != "win32" and not hasattr(os, "pidfd_open"), reason="Needs Windows process handles or Linux pidfds")
def test_worker_exits_after_its_owner_is_terminated(tmp_path):
    marker = tmp_path / "child.json"
    parent = subprocess.Popen([sys.executable, "tests/fixtures/workers/orphan_owner.py", str(marker), str(Path.cwd())],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    child_handle, close, terminate = None, lambda: None, lambda: None
    try:
        deadline = time.monotonic() + 15
        while not marker.exists() and time.monotonic() < deadline and parent.poll() is None:
            time.sleep(0.05)
        assert marker.exists(), "Disposable owner did not establish the watchdog"
        pid = json.loads(marker.read_text(encoding="utf-8"))["child_pid"]
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.WaitForSingleObject.restype = wintypes.DWORD
            kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            child_handle = kernel.OpenProcess(0x00100001, False, pid)  # SYNCHRONIZE plus owned-test cleanup.
            assert child_handle
            close = lambda: kernel.CloseHandle(child_handle)
            terminate = lambda: kernel.TerminateProcess(child_handle, 99)
            exited = lambda: kernel.WaitForSingleObject(child_handle, 5000) == 0
        else:
            import select
            import signal
            child_handle = os.pidfd_open(pid)
            close = lambda: os.close(child_handle)
            terminate = lambda: signal.pidfd_send_signal(child_handle, signal.SIGKILL)
            exited = lambda: bool(select.select([child_handle], [], [], 5)[0])
        parent.kill()
        parent.wait(timeout=5)
        assert exited(), "Monitored child survived owner termination"
    finally:
        if parent.poll() is None:
            parent.kill()
        parent.wait(timeout=5)
        if child_handle is not None:
            try:
                terminate()  # A signaled/exited handle is harmless; no PID-based broad cleanup.
            except ProcessLookupError:
                pass
            finally:
                close()
