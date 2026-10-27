"""Online SQLite snapshots and non-overwriting restore drills; no approvals are created."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import time


TABLES = ("runs", "revisions", "events", "reviews", "exports")


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", timeout=10, uri=True)


def inspect(path):
    """Check storage and fingerprint all persisted rows, including cached exports."""
    with closing(readonly(path)) as db:
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise ValueError("SQLite integrity check failed")
        contents = {}
        for table in TABLES:
            # Identifiers are the fixed application table names above, never input.
            cursor = db.execute(f"SELECT * FROM {table}")
            columns = [description[0] for description in cursor.description]
            rows = sorted(json.dumps(list(row), ensure_ascii=False) for row in cursor)
            contents[table] = {"columns": columns, "rows": rows}
    digest = hashlib.sha256(json.dumps(contents, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return {"logical_sha256": digest, "row_counts": {t: len(v["rows"]) for t, v in contents.items()}}


def snapshot(source, destination, kind="backup", parent_manifest=None):
    """Always create a new directory. On failure retain incomplete evidence."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file():
        raise ValueError("Source database must exist")
    if destination == source or source.is_relative_to(destination):
        raise ValueError("Snapshot directory must not contain the source database")
    started = time.perf_counter()
    destination.mkdir(parents=True, exist_ok=False)
    target = destination / "pilot.sqlite3"
    with closing(readonly(source)) as incoming, closing(sqlite3.connect(target)) as outgoing:
        incoming.backup(outgoing)
    state = inspect(target)
    record = {"format": "ami-pilot-sqlite-v1", "kind": kind,
              "created_utc": datetime.now(timezone.utc).isoformat(), "database": "pilot.sqlite3",
              "database_sha256": file_sha(target), **state,
              "elapsed_seconds": time.perf_counter() - started,
              "parent_manifest_sha256": parent_manifest,
              "scope": "SQLite history and cached exports only; corpus/model/config require separate pinned copies"}
    (destination / "manifest.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def verify(directory):
    directory = Path(directory).resolve()
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != "ami-pilot-sqlite-v1" or manifest.get("database") != "pilot.sqlite3":
        raise ValueError("Unsupported snapshot manifest")
    database = directory / "pilot.sqlite3"
    if database.is_symlink() or file_sha(database) != manifest["database_sha256"]:
        raise ValueError("Snapshot database identity mismatch")
    state = inspect(database)
    if any(state[key] != manifest[key] for key in ("logical_sha256", "row_counts")):
        raise ValueError("Snapshot logical state mismatch")
    return manifest


def restore(directory, destination):
    directory = Path(directory).resolve()
    expected = verify(directory)
    restored = snapshot(directory / "pilot.sqlite3", destination, kind="restore-drill",
                        parent_manifest=file_sha(directory / "manifest.json"))
    if any(restored[key] != expected[key] for key in ("logical_sha256", "row_counts")):
        raise ValueError("Restored history differs from verified snapshot")
    return restored


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    backup = sub.add_parser("backup")
    backup.add_argument("--database", type=Path, required=True)
    backup.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("verify")
    check.add_argument("--snapshot", type=Path, required=True)
    drill = sub.add_parser("restore")
    drill.add_argument("--snapshot", type=Path, required=True)
    drill.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = (snapshot(args.database, args.output) if args.command == "backup" else
              verify(args.snapshot) if args.command == "verify" else restore(args.snapshot, args.output))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
