"""No-inference container smoke: non-root app, truthful readiness and restart storage.

Creates and removes only its own uniquely named container and disposable volume.
Never modifies the owner's review database or records a human approval.
An optional verified snapshot is mounted read-only and restored into disposable storage.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import uuid


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument("--output", type=Path, default=Path(".ci-artifacts"))
    parser.add_argument("--review-snapshot", type=Path, help="Optional local-only verified snapshot; never supplied by CI")
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=False)
    name = "ami-pilot-smoke-" + uuid.uuid4().hex
    volume = name + "-state"
    fixture = Path("tests/fixtures/release/smoke_corpus.json").resolve()
    report = {"synthetic_only": True, "model_generation_calls": 0, "image": args.image,
              "human_decisions_created": 0, "status": "started"}
    created_container = created_volume = False
    exports, snapshot_sha = [], None
    database = "/state/pilot.sqlite3"
    if args.review_snapshot is not None:
        if __package__:
            from .pilot_backup import verify
        else:
            from pilot_backup import verify
        verified = verify(args.review_snapshot)
        snapshot_sha = verified["database_sha256"]
        with closing(sqlite3.connect((args.review_snapshot.resolve() / "pilot.sqlite3").as_uri() + "?mode=ro", uri=True)) as db:
            exports = db.execute("SELECT run_id,revision,content FROM exports ORDER BY run_id").fetchall()
        database = "/state/restored/pilot.sqlite3"
        report.update(synthetic_only=False, restored_snapshot_sha256=snapshot_sha, original_snapshot_read_only=True)

    def docker(*parts):
        return subprocess.run(["docker", *parts], check=True, capture_output=True, text=True).stdout.strip()

    def request(path, method="GET", payload=None, token=None, raw=False):
        headers = {"X-Pilot-Token": token} if token else {}
        body = None if payload is None else json.dumps(payload).encode()
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = Request(f"http://127.0.0.1:{args.port}{path}", data=body, headers=headers, method=method)
        try:
            response = urlopen(req, timeout=4)
        except HTTPError as exc:
            response = exc
        with response:
            return response.status, response.read() if raw else json.load(response)

    def healthy():
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                code, data = request("/health")
                if code == 200:
                    return data
            except (URLError, OSError):
                pass
            time.sleep(1)
        raise RuntimeError("Container did not become live within 90 seconds")

    try:
        docker("volume", "create", volume)
        created_volume = True
        created_container = True  # A failed start may still leave the named container.
        command = ["run", "--detach", "--name", name, "--publish", f"127.0.0.1:{args.port}:8000",
               "--read-only", "--tmpfs", "/tmp", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
               "--mount", f"type=volume,source={volume},target=/state",
               "--mount", f"type=bind,source={fixture},target=/data/market_chunks.json,readonly",
               "--env", "OLLAMA_BASE_URL=http://127.0.0.1:1", "--env", f"AMI_PILOT_DB={database}"]
        if args.review_snapshot is not None:
            command += ["--mount", f"type=bind,source={args.review_snapshot.resolve()},target=/backup,readonly"]
        command.append(args.image)
        if args.review_snapshot is not None:
            command += ["python", "-c", "from pathlib import Path\nfrom scripts.pilot_backup import restore\n"
                        "if not Path('/state/restored/pilot.sqlite3').is_file(): restore('/backup','/state/restored')\n"
                        "from src.pilot.launch import main\nmain(['--host','0.0.0.0'])"]
        docker(*command)
        health = healthy()
        assert docker("exec", name, "id", "-u") == "10001"
        status, readiness = request("/ready")
        assert status == 503 and readiness["checks"] == {"storage": "ready", "model": "unavailable", "runtime": "ready"}
        def session_token():
            code, body = request("/", raw=True)
            assert code == 200
            match = re.search(rb"\b(?:const|let)\s+token='([a-f0-9]{48})'", body)
            if match is None:
                raise ValueError("Supervised bootstrap marker absent; this smoke expects identity configuration to be unset")
            return match[1].decode()
        token = session_token()
        code, rejected = request("/api/runs", "POST", {"query": "Give me personal financial advice", "request_key": "synthetic-scope-rejection"}, token)
        assert code == 202
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            _, rejected_run = request("/api/runs/" + rejected["id"], token=token)
            if rejected_run["status"] not in {"queued", "running"}:
                break
            time.sleep(0.2)
        assert rejected_run["status"] == "needs_review" and rejected_run["draft"]["claims"] == []
        assert rejected_run["metrics"]["model_calls"] == rejected_run["metrics"]["guardrail_invocations"] == 0
        assert request("/api/runs/" + rejected["id"] + "/export", token=token, raw=True)[0] == 409
        # Insert an already-running synthetic row atomically: the new persisted
        # queue dispatcher must never observe this row as queued and execute it.
        create = """import sys,uuid
from src.pilot.store import Store,now
s=Store(sys.argv[2]); r=uuid.uuid4().hex
with s.connection() as db:
 db.execute('INSERT INTO runs(id,request_key,query,corpus_sha,status,created,updated) VALUES(?,?,?,?,?,?,?)',
  (r,'synthetic-container-smoke','Synthetic packaging recovery check',sys.argv[1],'running',now(),now()))
print(r)
"""
        run_id = docker("exec", name, "python", "-c", create, health["corpus_sha256"], database)
        assert len(run_id) == 32 and all(c in "0123456789abcdef" for c in run_id)
        docker("restart", name)
        healthy()
        verify = (
            f"import sys; from src.pilot.store import Store; s=Store('{database}'); "
            "r=s.get(sys.argv[1]); assert r['status']=='interrupted'; "
            "assert r['revision']==0 and not r['reviews']; print('persistent-interrupted-task')"
        )
        assert docker("exec", name, "python", "-c", verify, run_id) == "persistent-interrupted-task"
        token = session_token()
        cached = []
        for rid, revision, content in exports:
            status, body = request(f"/api/runs/{rid}/export", token=token, raw=True)
            assert status == 200 and body == content.encode("utf-8")
            cached.append({"run_id": rid, "revision": revision, "content_sha256": hashlib.sha256(body).hexdigest()})
        if args.review_snapshot is not None:
            assert hashlib.sha256((args.review_snapshot / "pilot.sqlite3").read_bytes()).hexdigest() == snapshot_sha
        report.update(status="passed", non_root=True, missing_model_readiness_503=True,
                      persistent_restart_recovery=True, corpus_sha256=health["corpus_sha256"],
                      real_worker_scope_rejection_zero_calls=True, cached_export_checks=cached,
                      bootstrap_token_recorded=False)
        (args.output / "image-inspect.json").write_text(docker("image", "inspect", args.image) + "\n", encoding="utf-8")
    except Exception as exc:
        report.update(status="failed", error_type=type(exc).__name__)
        raise
    finally:
        if created_container:
            logs = subprocess.run(["docker", "logs", name], capture_output=True, text=True)
            (args.output / "container.log").write_text(logs.stdout + logs.stderr, encoding="utf-8")
            subprocess.run(["docker", "rm", "--force", name], capture_output=True, check=False)
        if created_volume:
            cleanup = subprocess.run(["docker", "volume", "rm", volume], capture_output=True, check=False)
            report["volume_cleanup_succeeded"] = cleanup.returncode == 0
        (args.output / "container-smoke.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
