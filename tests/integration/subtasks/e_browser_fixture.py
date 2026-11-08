"""Synthetic real-app lifecycle fixture; never a deployable application.

Only fixed importable callbacks are installed. Test controls must not be copied
into production API code.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import secrets
from typing import Literal

from pydantic import BaseModel, ConfigDict

WORKERS = Path(__file__).resolve().parents[2] / 'fixtures' / 'workers'
if str(WORKERS) not in sys.path:
    sys.path.insert(0, str(WORKERS))
import e_lifecycle_worker as fixed


def prepare_files(directory):
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    controls = root / 'controls'
    controls.mkdir(exist_ok=True)
    corpus = root / 'synthetic-corpus.json'
    records = [{'feed_id': f'fiction-{i}', 'title': f'Fictional source {i}',
                'clean_content': f'Fictional district {i} recorded {i + 10} units in 2020.',
                'published': '2021-01-02', 'source': f'https://example.invalid/fiction-{i}',
                'doc_name': 'synthetic.pdf', 'page_num': 0 if i == 1 else 6}
               for i in range(1, 6)]
    payload = json.dumps(records, ensure_ascii=False, indent=2) + '\n'
    if corpus.exists() and corpus.read_text(encoding='utf-8') != payload:
        raise ValueError('Fixture refuses to overwrite a different corpus')
    if not corpus.exists():
        corpus.write_text(payload, encoding='utf-8')
    return root, corpus, controls


def latest_attempt(row):
    return next((e['payload']['attempt_id'] for e in reversed(row['events'])
                 if e['kind'] == 'attempt_started'), None)


def gate_state(controls, row):
    attempt = latest_attempt(row)
    if attempt is None:
        return {'attempt_id': None, 'entered': [], 'released': []}
    stages = ['s01', 's02', 's03', 's04', 's05', 'composition', 'safety']
    def present(stage, suffix):
        return (Path(controls) / (fixed.key(row['id'], attempt, stage) + suffix)).is_file()
    return {'attempt_id': attempt,
            'entered': [s for s in stages if present(s, '.entered')],
            'released': [s for s in stages if present(s, '.release')]}


def release(controls, row, stage, *, fail=False):
    attempt = latest_attempt(row)
    if attempt is None or row['status'] != 'running':
        raise ValueError('A current running fixture attempt is required')
    stem = Path(controls) / fixed.key(row['id'], attempt, stage)
    if fail:
        Path(str(stem) + '.fail').touch()
    Path(str(stem) + '.release').touch()


class ReleaseRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    stage: Literal['s01', 's02', 's03', 's04', 's05', 'composition', 'safety']
    fail: bool = False


def install_controls(app, controls):
    from fastapi import Request, HTTPException

    def authorize(request):
        if not secrets.compare_digest(request.headers.get('x-pilot-token', ''), app.state.token):
            raise HTTPException(403, 'Synthetic fixture session token required')

    @app.get('/__fixture/runs/{run_id}')
    def inspect(run_id: str, request: Request):
        authorize(request)
        return gate_state(controls, app.state.store.get(run_id))

    @app.post('/__fixture/runs/{run_id}/release')
    def allow(run_id: str, payload: ReleaseRequest, request: Request):
        authorize(request)
        row = app.state.store.get(run_id)
        try:
            release(controls, row, payload.stage, fail=payload.fail)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None
        return gate_state(controls, row)

    app.state.fixture_controls = controls


def create_fixture_app(directory=None):
    from src.pilot.api import create_app
    from src.pilot.subtasks.api_runtime import OwnedSubtaskExecutor
    if os.getenv('AMI_PILOT_IDENTITY_FILE'):
        raise ValueError('Synthetic fixture refuses a real identity configuration')
    directory = directory or os.getenv('AMI_E_FIXTURE_ROOT') or tempfile.mkdtemp(prefix='ami-e-synthetic-')
    root, corpus, controls = prepare_files(directory)
    marker = root / 'fixture-kind.txt'
    database = root / 'synthetic.sqlite3'
    if database.exists() and not marker.is_file():
        raise ValueError('Fixture refuses an unmarked existing database')
    if marker.exists() and marker.read_text(encoding='utf-8') != 'AMI E synthetic fixture v1\n':
        raise ValueError('Unknown synthetic fixture marker')
    marker.write_text('AMI E synthetic fixture v1\n', encoding='utf-8')
    executor = OwnedSubtaskExecutor(fixed.Operation(str(controls), str(corpus)),
                                   fixed.Composer(str(controls)), fixed.Safety(str(controls)))
    app = create_app(corpus_path=corpus, database_path=database, subtask_executor=executor)
    # The real dispatcher still owns the queue/process boundary; only the
    # sequential worker callback is fixed to make accidental default requests safe.
    app.state.runtime.worker = fixed.sequential
    install_controls(app, controls)
    app.state.fixture_root = root
    (root / 'session.json').write_text(json.dumps({'token': app.state.token, 'synthetic_only': True,
                                                  'actual_provider_calls': 0}) + '\n', encoding='utf-8')
    return app
