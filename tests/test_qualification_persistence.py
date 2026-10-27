"""Bounded filesystem retry is separate from model/workflow retries."""
import json
from pathlib import Path
import sys
import threading

import pytest

from src.pilot import qualify


def test_transient_replace_denial_retries_only_the_same_serialized_snapshot(monkeypatch, tmp_path):
    path = tmp_path / "progress.json"
    path.write_text('{"old": true}', encoding="utf-8")
    replace, calls, sleeps = Path.replace, [], []
    def denied_once(source, target):
        calls.append(source)
        if len(calls) == 1:
            raise PermissionError("Synthetic sharing denial")
        return replace(source, target)
    monkeypatch.setattr(Path, "replace", denied_once)
    monkeypatch.setattr(qualify.time, "sleep", sleeps.append)
    qualify.write(path, {"new": "Unicode ไทย"})
    assert json.loads(path.read_text(encoding="utf-8")) == {"new": "Unicode ไทย"}
    assert len(calls) == 2 and calls[0] == calls[1] and sleeps == [0.02]
    assert not list(tmp_path.glob("*.tmp"))


def test_permanent_denial_preserves_old_report_and_pending_snapshot(monkeypatch, tmp_path):
    path = tmp_path / "progress.json"
    path.write_bytes(b'{"previous":true}')
    sleeps, calls = [], []
    def denied(source, target):
        calls.append(source)
        raise PermissionError("Synthetic permanent denial")
    monkeypatch.setattr(Path, "replace", denied)
    monkeypatch.setattr(qualify.time, "sleep", sleeps.append)
    with pytest.raises(PermissionError):
        qualify.write(path, {"new": True})
    assert path.read_bytes() == b'{"previous":true}'
    assert len(calls) == 4 and len(set(calls)) == 1 and sleeps == [0.02, 0.1, 0.3]
    assert json.loads(calls[0].read_text(encoding="utf-8")) == {"new": True}


@pytest.mark.skipif(sys.platform != "win32", reason="Actual Windows sharing semantics")
def test_actual_non_delete_sharing_reader_releases_during_bounded_retry(tmp_path):
    import ctypes
    from ctypes import wintypes
    path = tmp_path / "progress.json"
    path.write_bytes(b'{"old":true}')
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                                  wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateFileW(str(path), 0x80000000, 1, None, 3, 0x80, None)
    assert handle not in {None, ctypes.c_void_p(-1).value}
    timer = threading.Timer(0.05, lambda: kernel.CloseHandle(handle))
    timer.start()
    try:
        qualify.write(path, {"new": True})
        assert json.loads(path.read_text(encoding="utf-8")) == {"new": True}
    finally:
        timer.join(timeout=1)
