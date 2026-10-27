"""Recovery evidence uses synthetic human decisions, never actual user approvals."""
import json
import sqlite3

import pytest

from scripts.pilot_backup import file_sha, inspect, restore, snapshot, verify
from src.pilot.schemas import ResearchRequest, ReviewRequest
from src.pilot.store import Conflict, Store


def reviewed_store(tmp_path):
    store = Store(tmp_path / "original.sqlite3")
    rid, _ = store.create(ResearchRequest(query="What was synthetic output?", request_key="synthetic-backup-one"), "a" * 64)
    assert store.claim(rid)
    source = {"s": {"content": "Synthetic output was 7 units.", "page_num": 6}}
    draft = {"title": "Synthetic brief", "claims": [{"text": "Synthetic output was 7 units.", "source_ids": ["s"]}], "warnings": []}
    store.save_draft(rid, draft, source, {})
    store.review(rid, ReviewRequest(revision=1, decision="approve", reviewer="synthetic-test-only", support_confirmed=True))
    exported = store.export(rid)
    return store, rid, draft, source, exported


def test_online_snapshot_restore_preserves_history_and_cached_exports(tmp_path):
    store, rid, draft, sources, exported = reviewed_store(tmp_path)
    before = file_sha(store.path)
    expected = inspect(store.path)
    record = snapshot(store.path, tmp_path / "backup")
    assert verify(tmp_path / "backup") == record
    assert file_sha(store.path) == before
    restored = restore(tmp_path / "backup", tmp_path / "drill")
    assert restored["logical_sha256"] == expected["logical_sha256"]
    recovered = Store(tmp_path / "drill/pilot.sqlite3")
    assert recovered.get(rid)["reviews"] == store.get(rid)["reviews"]
    assert recovered.export(rid) == exported
    recovered.save_draft(rid, draft, sources, {}, expected_revision=1)
    with pytest.raises(Conflict, match="approved"):
        recovered.export(rid)
    assert store.export(rid) == exported
    assert recovered.get(rid)["revision"] == 2


def test_wal_snapshot_includes_committed_data_and_excludes_uncommitted_write(tmp_path):
    store, *_ = reviewed_store(tmp_path)
    with sqlite3.connect(store.path) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("INSERT INTO events(run_id,kind,payload,created) VALUES('test','committed','{}','now')")
        writer.commit()
        writer.execute("INSERT INTO events(run_id,kind,payload,created) VALUES('test','uncommitted','{}','now')")
        snapshot(store.path, tmp_path / "wal-backup")
        writer.rollback()
    assert verify(tmp_path / "wal-backup")["row_counts"]["events"] == 1


def test_corrupted_or_incomplete_backup_cannot_restore_or_overwrite(tmp_path):
    store, *_ = reviewed_store(tmp_path)
    snapshot(store.path, tmp_path / "backup")
    with pytest.raises(FileExistsError):
        snapshot(store.path, tmp_path / "backup")
    restore(tmp_path / "backup", tmp_path / "drill")
    with pytest.raises(FileExistsError):
        restore(tmp_path / "backup", tmp_path / "drill")
    (tmp_path / "backup/pilot.sqlite3").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="identity mismatch"):
        restore(tmp_path / "backup", tmp_path / "never-created")
    assert not (tmp_path / "never-created").exists()


def test_logical_manifest_tampering_and_missing_source_fail(tmp_path):
    store, *_ = reviewed_store(tmp_path)
    snapshot(store.path, tmp_path / "backup")
    path = tmp_path / "backup/manifest.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["row_counts"]["reviews"] += 1
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="logical state"):
        verify(tmp_path / "backup")
    with pytest.raises(ValueError, match="must exist"):
        snapshot(tmp_path / "absent.sqlite3", tmp_path / "missing")
    assert not (tmp_path / "missing").exists()
