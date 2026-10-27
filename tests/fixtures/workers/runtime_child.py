"""Spawnable synthetic IPC workers. This file never invokes a model."""
import json
import os
from pathlib import Path
import time


def run(job, connection):
    from src.pilot._worker import MESSAGE_LIMIT, send
    query = job["query"]
    if query == "malformed message":
        connection.send_bytes(b"not-json")
        return
    if query == "oversized message":
        connection.send_bytes(b"x" * (MESSAGE_LIMIT + 1))
        return
    send(connection, "event", {"event": "model_request_started", "data": {"stage": "synthetic_model"}})
    if query == "hang model":
        time.sleep(60)
    send(connection, "event", {"event": "model_call", "data": {"stage": "synthetic_model", "usage": {"input_tokens": 7, "output_tokens": 3}}})
    if query == "hang guard":
        send(connection, "event", {"event": "guard_invocation_started", "data": {"internal_token_usage": None}})
        time.sleep(60)
    if query == "fail once":
        marker = Path(job["corpus_path"]).with_suffix(".failed-once")
        if not marker.exists():
            marker.write_text("synthetic test only", encoding="utf-8")
            send(connection, "failure", {"type": "SyntheticFailure"})
            raise SystemExit(1)
    raw = json.loads(Path(job["corpus_path"]).read_text(encoding="utf-8"))[0]
    sid = str(raw["feed_id"])
    result = {"draft": {"title": "Synthetic runtime brief", "claims": [{"text": raw["clean_content"], "source_ids": [sid]}], "warnings": []},
              "sources": {sid: {"source_id": sid, "content": raw["clean_content"], "page_num": 0}},
              "metrics": {"model_calls": 1, "corpus_sha256": job["corpus_sha"]}}
    if query == "empty success":
        result["draft"]["claims"] = []
    if query == "wait then finish":
        release = Path(job["corpus_path"]).with_suffix(".release")
        while not release.exists():
            time.sleep(0.02)
    send(connection, "result", result)
    if query == "result then crash":
        os._exit(7)
    if query == "result then hang":
        time.sleep(60)
    if query == "event after result":
        send(connection, "event", {"event": "late", "data": {}})
    connection.close()


def orphan_watch(job, connection):
    from src.pilot._worker import OwnerWatchdog
    watchdog = OwnerWatchdog(job["owner_pid"], time.monotonic() + 30)
    connection.send_bytes(b"ready")
    while True:
        time.sleep(1)
