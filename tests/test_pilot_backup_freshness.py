"""Backup age is independent of integrity, restoration time and corpus age."""
from datetime import datetime, timedelta, timezone
import json

import pytest

from scripts import pilot_backup as backup
from src.pilot.store import Store

NOW = datetime(2026, 10, 30, 3, tzinfo=timezone.utc)


@pytest.fixture
def saved(tmp_path):
    source = Store(tmp_path / "synthetic.sqlite3")
    directory = tmp_path / "backup"
    backup.snapshot(source.path, directory)
    return directory


def set_metadata(directory, **changes):
    path = directory / "manifest.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record.update(changes)
    path.write_text(json.dumps(record), encoding="utf-8")


@pytest.mark.parametrize("seconds,status", [(0, "fresh"), (86400, "fresh"), (86400.001, "stale")])
def test_verified_age_boundary_and_no_snapshot_writes(saved, seconds, status):
    set_metadata(saved, created_utc=(NOW - timedelta(seconds=seconds)).isoformat())
    before = {p.name: backup.file_sha(p) for p in saved.iterdir()}
    result = backup.check_freshness(saved, now=NOW)
    assert result["status"] == status and result["age_seconds"] == seconds
    assert result["alert_delivery_performed"] is False
    assert {p.name: backup.file_sha(p) for p in saved.iterdir()} == before


def test_timezone_offsets_compare_instants_not_wall_clock(saved):
    set_metadata(saved, created_utc="2026-10-30T09:00:00+07:00")
    result = backup.check_freshness(saved, now=NOW)
    assert result["age_seconds"] == 3600 and result["backup_created_utc"] == "2026-10-30T02:00:00+00:00"


@pytest.mark.parametrize("stamp", [None, "bad timestamp", "2026-10-30T02:00:00", "2026-10-30T03:00:01+00:00",
    "0001-01-01T00:00:00+14:00"])
def test_invalid_naive_and_future_timestamps_cannot_pass(saved, stamp):
    set_metadata(saved, created_utc=stamp)
    with pytest.raises(ValueError):backup.check_freshness(saved, now=NOW)


@pytest.mark.parametrize("limit", [0, -1, 25, True, float("nan"), float("inf"), 10**1000])
def test_invalid_limits_cannot_weaken_24_hour_contract(saved, limit):
    with pytest.raises(ValueError):backup.check_freshness(saved, limit, now=NOW)


def test_operator_can_tighten_but_not_loosen_age_target(saved):
    set_metadata(saved, created_utc=(NOW-timedelta(hours=2)).isoformat())
    assert backup.check_freshness(saved, 1, now=NOW)["status"] == "stale"
    assert backup.check_freshness(saved, 24, now=NOW)["status"] == "fresh"


def test_restore_timestamp_does_not_refresh_old_backup(saved, tmp_path):
    set_metadata(saved, created_utc=(NOW-timedelta(days=2)).isoformat())
    restored = tmp_path / "restored"
    backup.restore(saved, restored)
    with pytest.raises(ValueError, match="original backup"):
        backup.check_freshness(restored, now=NOW)
    assert backup.check_freshness(saved, now=NOW)["status"] == "stale"


def test_parent_reference_cannot_be_disguised_as_original_backup(saved):
    set_metadata(saved, kind="backup", parent_manifest_sha256="a"*64)
    with pytest.raises(ValueError, match="original backup"):
        backup.check_freshness(saved, now=NOW)


def test_corrupt_recent_snapshot_is_unavailable_not_fresh(saved, capsys):
    (saved/"pilot.sqlite3").write_bytes(b"synthetic-corruption")
    assert backup.main(["check-freshness", "--snapshot", str(saved)]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "unavailable" and str(saved) not in json.dumps(result)


@pytest.mark.parametrize("content", [None, "[]", '{"private": "synthetic-secret"}'])
def test_missing_or_malformed_snapshot_yields_sanitized_nonzero(tmp_path, capsys, content):
    if content is not None:
        (tmp_path/"manifest.json").write_text(content, encoding="utf-8")
    assert backup.main(["check-freshness", "--snapshot", str(tmp_path)]) == 2
    text = capsys.readouterr().out
    assert json.loads(text)["status"] == "unavailable"
    assert str(tmp_path) not in text and "synthetic-secret" not in text


def test_cli_exit_codes_and_original_verify_output_are_preserved(saved, capsys):
    assert backup.main(["check-freshness", "--snapshot", str(saved)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "fresh"
    set_metadata(saved, created_utc="2000-01-01T00:00:00+00:00")
    assert backup.main(["check-freshness", "--snapshot", str(saved)]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "stale"
    assert backup.main(["verify", "--snapshot", str(saved)]) == 0
    assert json.loads(capsys.readouterr().out) == backup.verify(saved)


def test_naive_check_clock_does_not_silently_use_host_timezone(saved):
    with pytest.raises(ValueError, match="timezone"):
        backup.check_freshness(saved, now=NOW.replace(tzinfo=None))
