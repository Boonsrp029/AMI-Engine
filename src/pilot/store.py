"""SQLite task history, revision checks and idempotent approved exports."""

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from src.pilot.schemas import validate_citations
from src.pilot._presentation import pdf_page_label


class Conflict(ValueError):
    pass


class QueueFull(Conflict):
    pass


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path, queue_limit=None):
        if queue_limit is not None and (type(queue_limit) is not int or queue_limit < 1):
            raise ValueError("Queue limit must be a positive integer")
        self.queue_limit = queue_limit
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
                    query TEXT NOT NULL, corpus_sha TEXT NOT NULL, status TEXT NOT NULL,
                    revision INTEGER NOT NULL DEFAULT 0, draft TEXT, sources TEXT NOT NULL DEFAULT '{}',
                    metrics TEXT NOT NULL DEFAULT '{}', error TEXT, created TEXT NOT NULL, updated TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS revisions (
                    run_id TEXT, revision INTEGER, draft TEXT, sources TEXT, digest TEXT, created TEXT,
                    PRIMARY KEY(run_id, revision));
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, kind TEXT, payload TEXT, created TEXT);
                CREATE TABLE IF NOT EXISTS reviews (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, revision INTEGER,
                    decision TEXT, payload TEXT, created TEXT);
                CREATE TABLE IF NOT EXISTS exports (
                    run_id TEXT, revision INTEGER, content TEXT, created TEXT,
                    PRIMARY KEY(run_id, revision));
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, run_id):
        with self.connection() as db:
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            result = dict(row)
            for key in ("draft", "sources", "metrics"):
                result[key] = json.loads(result[key]) if result[key] else None
            result["events"] = [dict(r) | {"payload": json.loads(r["payload"])} for r in db.execute(
                "SELECT * FROM events WHERE run_id=? ORDER BY seq", (run_id,))]
            result["reviews"] = [dict(r) | {"payload": json.loads(r["payload"])} for r in db.execute(
                "SELECT * FROM reviews WHERE run_id=? ORDER BY seq", (run_id,))]
            return result

    def list(self):
        with self.connection() as db:
            return [dict(r) for r in db.execute(
                "SELECT id,query,status,revision,created FROM runs ORDER BY created DESC LIMIT 100")]

    def create(self, request, corpus_sha):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM runs WHERE request_key=?", (request.request_key,)).fetchone()
            if old:
                if old["query"] != request.query or old["corpus_sha"] != corpus_sha:
                    raise Conflict("Request key is already used for different input")
                return old["id"], False
            self._check_queue_capacity(db)
            run_id = uuid.uuid4().hex
            db.execute("INSERT INTO runs(id,request_key,query,corpus_sha,status,created,updated) VALUES(?,?,?,?,?,?,?)",
                       (run_id, request.request_key, request.query, corpus_sha, "queued", now(), now()))
            return run_id, True

    def claim(self, run_id, attempt_id=None):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            claimed = db.execute("UPDATE runs SET status='running',updated=? WHERE id=? AND status='queued'",
                                 (now(), run_id)).rowcount == 1
            if claimed and attempt_id is not None:
                db.execute("INSERT INTO events(run_id,kind,payload,created) VALUES(?,?,?,?)",
                           (run_id, "attempt_started", json.dumps({"attempt_id": attempt_id}), now()))
            return claimed

    def next_queued(self):
        with self.connection() as db:
            row = db.execute("SELECT id,query,corpus_sha,updated FROM runs WHERE status='queued' ORDER BY created,id LIMIT 1").fetchone()
            return dict(row) if row else None

    @staticmethod
    def _current_attempt(db, run_id, attempt_id):
        row = db.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
        event = db.execute("SELECT payload FROM events WHERE run_id=? AND kind='attempt_started' ORDER BY seq DESC LIMIT 1",
                           (run_id,)).fetchone()
        return bool(row and row["status"] == "running" and event and json.loads(event["payload"])["attempt_id"] == attempt_id)

    def attempt_event(self, run_id, attempt_id, kind, payload):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if not self._current_attempt(db, run_id, attempt_id):
                return False
            db.execute("INSERT INTO events(run_id,kind,payload,created) VALUES(?,?,?,?)",
                       (run_id, kind, json.dumps({**payload, "attempt_id": attempt_id}, ensure_ascii=False), now()))
            return True

    @staticmethod
    def _attempt_metrics(db, run_id, attempt_id, elapsed_seconds):
        events = [(row["kind"], json.loads(row["payload"])) for row in db.execute(
            "SELECT kind,payload FROM events WHERE run_id=? ORDER BY seq", (run_id,))]
        events = [(kind, payload) for kind, payload in events if payload.get("attempt_id") == attempt_id]
        return {"partial": True, "execution_elapsed_seconds": elapsed_seconds, "attempt_id": attempt_id,
                "model_calls": max(sum(kind == "model_request_started" for kind, _ in events),
                                   sum(kind in {"model_call", "model_failure"} for kind, _ in events)),
                "guardrail_invocations": sum(kind == "guard_invocation_started" for kind, _ in events),
                "token_usage_complete": False, "inflight_usage_unknown": attempt_id is not None, "monetary_cost": None,
                "known_input_tokens": sum((p.get("usage") or {}).get("input_tokens", 0) for _, p in events),
                "known_output_tokens": sum((p.get("usage") or {}).get("output_tokens", 0) for _, p in events)}

    def finish_attempt(self, run_id, attempt_id, reason, elapsed_seconds=0):
        errors = {"deadline": "Execution deadline exceeded; safe retry is available",
                  "canceled": "Task canceled; safe retry is available", "shutdown": "Application stopped; safe retry is available",
                  "worker_exit": "Worker did not exit cleanly; inspect history before retrying",
                  "worker_error": "Worker failed; inspect history before retrying",
                  "invalid_message": "Worker communication failed validation; inspect history before retrying",
                  "corpus_changed": "The corpus changed; create a new task with current provenance"}
        if reason not in errors:
            raise ValueError("Unknown worker termination reason")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if not self._current_attempt(db, run_id, attempt_id):
                return False
            metrics = {**self._attempt_metrics(db, run_id, attempt_id, elapsed_seconds), "failure_reason": reason}
            db.execute("INSERT INTO events(run_id,kind,payload,created) VALUES(?,?,?,?)",
                       (run_id, "attempt_stopped", json.dumps({"attempt_id": attempt_id, "reason": reason, "elapsed_seconds": elapsed_seconds}), now()))
            db.execute("UPDATE runs SET status=?,error=?,metrics=?,updated=? WHERE id=?",
                       ("interrupted" if reason in {"canceled", "shutdown"} else "failed", errors[reason], json.dumps(metrics), now(), run_id))
            return True

    def cancel(self, run_id, elapsed_seconds=None):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            if row["status"] not in {"queued", "running"}:
                raise Conflict("Only queued or running tasks may be canceled")
            attempt = db.execute("SELECT payload FROM events WHERE run_id=? AND kind='attempt_started' ORDER BY seq DESC LIMIT 1", (run_id,)).fetchone()
            attempt_id = json.loads(attempt["payload"])["attempt_id"] if row["status"] == "running" and attempt else None
            metrics = {**self._attempt_metrics(db, run_id, attempt_id, elapsed_seconds), "failure_reason": "canceled"}
            db.execute("UPDATE runs SET status='interrupted',error='Task canceled; safe retry is available',metrics=?,updated=? WHERE id=?",
                       (json.dumps(metrics), now(), run_id))
            db.execute("INSERT INTO events(run_id,kind,payload,created) VALUES(?,?,?,?)",
                       (run_id, "task_canceled", json.dumps({"attempt_id": attempt_id, "previous_status": row["status"]}), now()))
            return attempt_id

    def recover(self, message="Application restarted; safe retry is available"):
        with self.connection() as db:
            db.execute("UPDATE runs SET status='interrupted',error=?,updated=? WHERE status IN ('running','queued')", (message, now()))

    def retry(self, run_id):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None or row["status"] not in {"failed", "interrupted"}:
                raise Conflict("Only failed or interrupted tasks may be retried")
            self._check_queue_capacity(db)
            if not db.execute("UPDATE runs SET status='queued',error=NULL,updated=? WHERE id=? "
                              "AND status IN ('failed','interrupted')", (now(), run_id)).rowcount:
                raise Conflict("Only failed or interrupted tasks may be retried")

    def _check_queue_capacity(self, db):
        # Called only inside the same write transaction as admission/retry.
        if self.queue_limit is not None and db.execute(
                "SELECT count(*) FROM runs WHERE status='queued'").fetchone()[0] >= self.queue_limit:
            raise QueueFull("The analyst queue is full; wait for an existing task to start or finish")

    def event(self, run_id, kind, payload):
        # Payloads are structured summaries, never provider headers or exception strings.
        with self.connection() as db:
            db.execute("INSERT INTO events(run_id,kind,payload,created) VALUES(?,?,?,?)",
                       (run_id, kind, json.dumps(payload, ensure_ascii=False), now()))

    def fail(self, run_id, error):
        with self.connection() as db:
            events = list(db.execute("SELECT kind,payload FROM events WHERE run_id=?", (run_id,)))
            metrics = {"partial": True, "model_calls": sum(e["kind"] in ("model_call", "model_failure") for e in events),
                       "token_usage_complete": False, "monetary_cost": None}
            db.execute("UPDATE runs SET status='failed',error=?,metrics=?,updated=? WHERE id=? AND status='running'",
                       (error, json.dumps(metrics), now(), run_id))

    def save_draft(self, run_id, draft, sources, metrics, expected_revision=None, attempt_id=None):
        draft = validate_citations(draft, sources)
        encoded = json.dumps(draft, ensure_ascii=False)
        source_json = json.dumps(sources, ensure_ascii=False)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT status,revision FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            if expected_revision is None:
                if row["status"] != "running":
                    raise Conflict("Task is not running")
                if attempt_id is not None and not self._current_attempt(db, run_id, attempt_id):
                    raise Conflict("The worker attempt is no longer current")
            elif row["revision"] != expected_revision or row["status"] not in ("needs_review", "approved", "rejected"):
                raise Conflict("The draft has changed; reload before editing")
            revision = row["revision"] + 1
            digest = hashlib.sha256((encoded + source_json).encode()).hexdigest()
            db.execute("INSERT INTO revisions VALUES(?,?,?,?,?,?)",
                       (run_id, revision, encoded, source_json, digest, now()))
            db.execute("UPDATE runs SET status='needs_review',revision=?,draft=?,sources=?,metrics=?,error=NULL,updated=? WHERE id=?",
                       (revision, encoded, source_json, json.dumps(metrics), now(), run_id))
        return revision

    def review(self, run_id, request):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            if row["status"] != "needs_review" or row["revision"] != request.revision:
                raise Conflict("Review requires the current unreviewed revision")
            if request.decision == "approve" and (not request.support_confirmed or not json.loads(row["draft"])["claims"]):
                raise Conflict("Approval requires claims and explicit confirmation of source support")
            db.execute("INSERT INTO reviews(run_id,revision,decision,payload,created) VALUES(?,?,?,?,?)",
                       (run_id, request.revision, request.decision, request.model_dump_json(), now()))
            db.execute("UPDATE runs SET status=?,updated=? WHERE id=?",
                       ("approved" if request.decision == "approve" else "rejected", now(), run_id))

    def export(self, run_id):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(run_id)
            if row["status"] != "approved":
                raise Conflict("Only the current human-approved revision can be exported")
            old = db.execute("SELECT content FROM exports WHERE run_id=? AND revision=?", (run_id, row["revision"])).fetchone()
            if old:
                return old["content"], row["revision"]
            draft, sources = json.loads(row["draft"]), json.loads(row["sources"])
            lines = [f"# {draft['title']}", "", f"Run {run_id}; approved revision {row['revision']}", ""]
            for claim in draft["claims"]:
                lines.extend([f"{claim['text']} [{', '.join(claim['source_ids'])}]", ""])
            lines += ["## Evidence gaps", ""]
            for warning in draft["warnings"]:
                lines.extend([warning, ""])
            lines += ["## Sources", ""]
            for source_id, source in sources.items():
                lines.extend([f"{source_id}: {source.get('title', '')}; {source.get('published') or 'date unknown'}; "
                              f"{source.get('url', '')}; {pdf_page_label(source.get('page_num'))}", ""])
            content = "\n".join(lines) + "\n"
            db.execute("INSERT INTO exports VALUES(?,?,?,?)", (run_id, row["revision"], content, now()))
            return content, row["revision"]
