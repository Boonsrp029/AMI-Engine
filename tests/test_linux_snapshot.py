"""Prevent test-container snapshots from exposing credentials or unrelated history."""
from pathlib import Path

import pytest

from scripts.check_linux_container import prepare


def test_snapshot_excludes_private_inputs_and_preserves_selected_source_bytes(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    for name in (".env", ".databricks/.databricks.env", "reports/history.json", "data/external/source.json", ".venv/site.py"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("dapi" + "0" * 32, encoding="utf-8")
    path = root / "src/example.py"
    path.parent.mkdir()
    path.write_bytes(b"# exact selected source\n")
    out = tmp_path / "snapshot"
    manifest = prepare(root, out)
    assert set(manifest["sha256"]) == {"src/example.py"}
    assert (out / "src/example.py").read_bytes() == path.read_bytes()
    assert not (out / ".env").exists() and not (out / "reports").exists()


def test_credential_shaped_selected_source_fails_before_creating_context(tmp_path):
    root = tmp_path / "project"
    (root / "src").mkdir(parents=True)
    (root / "src/unsafe.py").write_text("dapi" + "0" * 32, encoding="utf-8")
    out = tmp_path / "snapshot"
    with pytest.raises(ValueError, match="Credential-shaped"):
        prepare(root, out)
    assert not out.exists()
