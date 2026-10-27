"""Disposable parent for an actual owner-death watchdog test; no model calls."""
import json
import multiprocessing
import os
from pathlib import Path
import sys
import time


if __name__ == "__main__":
    sys.path.insert(0, sys.argv[2])
    from runtime_child import orphan_watch
    context = multiprocessing.get_context("spawn")
    receive, send = context.Pipe(duplex=False)
    process = context.Process(target=orphan_watch, args=({"owner_pid": os.getpid()}, send))
    process.start()
    send.close()
    if not receive.poll(10) or receive.recv_bytes() != b"ready":
        process.kill()
        process.join(5)
        raise SystemExit(1)
    target = Path(sys.argv[1])
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps({"child_pid": process.pid, "owner_pid": os.getpid()}), encoding="utf-8")
    temporary.replace(target)
    time.sleep(30)
