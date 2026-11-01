"""Startup preflight failures occur before Docker can create an empty mount."""
import json
from types import SimpleNamespace

import pytest

from scripts import start_pilot_desktop as start


@pytest.mark.parametrize('kind', ['missing', 'directory', 'invalid_json'])
def test_bad_corpus_never_invokes_docker(tmp_path, monkeypatch, kind):
    path = tmp_path / 'corpus.json'
    if kind == 'directory': path.mkdir()
    if kind == 'invalid_json': path.write_text('not JSON', encoding='utf-8')
    monkeypatch.setattr(start.subprocess, 'run', lambda *a, **k: pytest.fail('Docker must not run'))
    with pytest.raises(SystemExit) as exc:
        start.main(['--image', 'local-image', '--corpus', str(path)])
    assert exc.value.code == 2


def test_obsolete_main_image_is_rejected_before_compose(tmp_path, monkeypatch):
    path = tmp_path / 'corpus.json';path.write_text('[]', encoding='utf-8')
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        return SimpleNamespace(stdout=json.dumps([{'Config': {'Cmd': ['python', 'main.py']}}]))
    monkeypatch.setattr(start.subprocess, 'run', run)
    with pytest.raises(SystemExit): start.main(['--image', 'old-image', '--corpus', str(path)])
    assert len(calls) == 1 and calls[0][:3] == ['docker', 'image', 'inspect']


def test_check_mode_uses_absolute_source_and_never_starts_service(tmp_path, monkeypatch):
    path = tmp_path / 'corpus.json';path.write_text('[]', encoding='utf-8')
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(stdout=json.dumps([{'Config': {'Cmd': ['python', '-m', 'src.pilot.launch']}}]))
    monkeypatch.setattr(start.subprocess, 'run', run)
    assert start.main(['--image', 'local-image', '--corpus', str(path), '--check']) == 0
    assert len(calls) == 2 and calls[-1][0][-2:] == ['config', '--quiet']
    assert calls[-1][1]['env']['AMI_PILOT_CORPUS_FILE'] == str(path.resolve())
