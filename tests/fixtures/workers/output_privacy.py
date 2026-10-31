"""Native child-only fixture. Never redirect the pytest/owner process."""
import ctypes
import logging
import os
import sys
import time
from types import ModuleType

MARKER = "synthetic-private-worker-dependency-message"


def run(output, closed=False):
    from src.pilot import _worker
    module = ModuleType("src.pilot.engine")
    class Corpus:
        def __init__(self, path):self.sha = "a" * 64
    class Engine:
        def __init__(self, corpus):pass
        def run(self, query, event):
            logging.getLogger("synthetic.dependency").error(MARKER)
            print(MARKER, file=sys.stderr, flush=True)
            print(MARKER, flush=True)
            os.write(1, MARKER.encode());os.write(2, MARKER.encode())
            if sys.platform == "win32":
                from ctypes import wintypes
                kernel = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel.GetStdHandle.argtypes = [wintypes.DWORD];kernel.GetStdHandle.restype = wintypes.HANDLE
                kernel.WriteFile.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
                kernel.WriteFile.restype = wintypes.BOOL
                data = MARKER.encode();written = wintypes.DWORD()
                for kind in (-11, -12):
                    assert kernel.WriteFile(kernel.GetStdHandle(kind), data, len(data), ctypes.byref(written), None)
            raise RuntimeError(MARKER)
    module.Corpus, module.PilotEngine = Corpus, Engine
    sys.modules["src.pilot.engine"] = module
    class Capture:
        def send_bytes(self, data):
            from pathlib import Path
            Path(output).write_bytes(data)
        def close(self):pass
    if closed:
        os.close(1);os.close(2)
    _worker.run({"owner_pid": os.getppid(), "deadline": time.monotonic()+15,
        "corpus_path": "synthetic-unused", "corpus_sha": "a"*64, "query": "Synthetic public research question"}, Capture())
