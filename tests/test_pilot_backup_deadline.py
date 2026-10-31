"""Synthetic SQLite lock/copy failures do not create a verified backup."""
import json
import sqlite3
import subprocess
import sys

import pytest

from scripts import pilot_backup as backup


def empty_database(path):
    with sqlite3.connect(path) as db:
        for table in backup.TABLES:
            db.execute(f'CREATE TABLE {table}(id INTEGER)')


def test_exclusive_source_lock_has_bounded_nonzero_cli_exit_and_no_manifest(tmp_path):
    source = tmp_path / 'synthetic.sqlite3'
    empty_database(source)
    output = tmp_path / 'incomplete'
    before = backup.file_sha(source)
    with sqlite3.connect(source) as writer:
        writer.execute('BEGIN EXCLUSIVE')
        # Shorten only the test clock budget; use the real SQLite backup loop.
        code = ('from scripts import pilot_backup as b; b._COPY_TIMEOUT_SECONDS=.1; '
                f'raise SystemExit(b.main({["backup", "--database", str(source), "--output", str(output)]!r}))')
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=5)
        writer.rollback()
    assert result.returncode == 2
    assert json.loads(result.stdout) == {'status': 'unavailable', 'reason': 'SQLite snapshot copy deadline exceeded'}
    assert not result.stderr and str(source) not in result.stdout
    assert backup.file_sha(source) == before
    assert output.is_dir() and not (output / 'manifest.json').exists()
    with pytest.raises(FileNotFoundError):
        backup.verify(output)
    # An incomplete destination is not silently replaced on a later attempt.
    with pytest.raises(FileExistsError):
        backup.snapshot(source, output)
    record = backup.snapshot(source, tmp_path / 'new-after-unlock')
    assert backup.verify(tmp_path / 'new-after-unlock') == record


def test_expired_copy_never_writes_manifest_or_changes_source(tmp_path, monkeypatch):
    source = tmp_path / 'synthetic.sqlite3'
    empty_database(source)
    before = backup.file_sha(source)
    ticks = iter((0.0, 61.0))
    monkeypatch.setattr(backup.time, 'monotonic', lambda: next(ticks))
    with pytest.raises(TimeoutError, match='copy deadline'):
        backup.snapshot(source, tmp_path / 'expired')
    assert not (tmp_path / 'expired/manifest.json').exists()
    assert backup.file_sha(source) == before


def test_restore_copy_timeout_leaves_original_snapshot_verifiable(tmp_path, monkeypatch):
    source = tmp_path / 'synthetic.sqlite3'
    empty_database(source)
    saved = tmp_path / 'backup'
    expected = backup.snapshot(source, saved)
    before = {path.name: backup.file_sha(path) for path in saved.iterdir()}
    monkeypatch.setattr(backup, '_COPY_TIMEOUT_SECONDS', 0)
    with pytest.raises(TimeoutError):
        backup.restore(saved, tmp_path / 'failed-drill')
    assert not (tmp_path / 'failed-drill/manifest.json').exists()
    assert {path.name: backup.file_sha(path) for path in saved.iterdir()} == before
    assert backup.verify(saved) == expected


def test_copy_deadline_uses_monotonic_time_not_wall_time(tmp_path, monkeypatch):
    source = tmp_path / 'synthetic.sqlite3'
    empty_database(source)
    monkeypatch.setattr(backup.time, 'monotonic', lambda: 100.0)
    monkeypatch.setattr(backup.time, 'time', lambda: -10**12)
    result = backup.snapshot(source, tmp_path / 'valid')
    assert result['row_counts'] == {table: 0 for table in backup.TABLES}
    assert backup.verify(tmp_path / 'valid') == result
