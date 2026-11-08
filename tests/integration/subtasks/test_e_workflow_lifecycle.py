"""D owns real lifecycle joins for E; fixed callbacks, no provider requests."""
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from types import SimpleNamespace
from fastapi.testclient import TestClient

from e_browser_fixture import prepare_files, gate_state, release, install_controls, fixed, create_fixture_app
from src.pilot.engine import Corpus
from src.pilot.schemas import ResearchRequest
from src.pilot.store import Store
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.persistence import progress_view
from src.pilot.subtasks.runner import run_stored_plan


def wait_for(read, predicate, timeout=35):
    """Poll an observable boundary; elapsed time is only a hang watchdog."""
    until = time.monotonic() + timeout
    tick = threading.Event()
    while time.monotonic() < until:
        value = read()
        if predicate(value):
            return value
        tick.wait(.02)
    raise AssertionError(f'Controlled state was not reached; last snapshot: {value!r}')


def test_fixture_controls_are_test_only_authenticated_and_attempt_scoped(tmp_path):
    from src.pilot.api import create_app
    root, path, controls = prepare_files(tmp_path)
    corpus = Corpus(path)
    engine = SimpleNamespace(corpus=corpus, run=lambda *_: (_ for _ in ()).throw(AssertionError('Forbidden')))
    api = create_app(engine=engine, database_path=root / 'controls.sqlite3', run_inline=True)
    with TestClient(api, base_url='http://127.0.0.1') as client:
        assert client.get('/__fixture/runs/' + 'a' * 32).status_code == 404
    install_controls(api, controls)
    with TestClient(api, base_url='http://127.0.0.1') as client:
        store = api.state.store
        rid, _ = store.create(ResearchRequest(query='Fictional control check', request_key='fixture-control-check'), corpus.sha)
        store.claim(rid, 'a' * 32)
        url = f'/__fixture/runs/{rid}'
        headers = {'x-pilot-token': api.state.token}
        assert client.get(url).status_code == 403
        assert client.post(url + '/release', json={'stage': 's01'}).status_code == 403
        assert client.post(url + '/release', headers=headers, json={'stage': '../../outside'}).status_code == 422
        assert client.post(url + '/release', headers=headers, json={'stage': 's01', 'unexpected': True}).status_code == 422
        response = client.post(url + '/release', headers=headers, json={'stage': 's01'})
        assert response.status_code == 200 and response.json()['released'] == ['s01']
        store.cancel(rid)
        store.retry(rid)
        store.claim(rid, 'b' * 32)
        assert client.get(url, headers=headers).json()['released'] == []
        assert len(list(controls.glob('*.release'))) == 1


def bounded_request(key='E-D-http-bounded'):
    return {'query': 'Compare fictional district observations in 2020', 'request_key': key,
            'subtasks': [{'subtask_id': f's{i:02}', 'operation': 'retrieve', 'query': f'district {i}',
                          'timeout_seconds': 180.0} for i in (1, 2)]}


def run_api(client, headers, rid):
    return client.get(f'/api/runs/{rid}/progress', headers=headers).json()


def finish_api(client, headers, rid):
    prefix = f'/__fixture/runs/{rid}'
    # Retried queued rows retain historical attempt events. Wait for the
    # authoritative current-running projection, not merely any old attempt ID.
    wait_for(lambda: run_api(client, headers, rid),
             lambda r: r['run']['status'] == 'running' and r['progress']['attempt_current']
             and r['progress']['attempt_id'] is not None)
    for stage in ('s01', 's02', 'composition', 'safety'):
        response = client.post(prefix + '/release', headers=headers, json={'stage': stage})
        assert response.status_code == 200, response.text
    return wait_for(lambda: run_api(client, headers, rid), lambda r: r['run']['status'] == 'needs_review')


def test_finish_helper_does_not_release_historical_queued_attempt():
    snapshots = iter([
        {'run': {'status': 'queued'}, 'progress': {'attempt_current': False, 'attempt_id': 'old'}},
        {'run': {'status': 'running'}, 'progress': {'attempt_current': True, 'attempt_id': 'new'}},
        {'run': {'status': 'needs_review'}, 'progress': {'attempt_current': False, 'attempt_id': 'new'}},
    ])
    observed = []
    class Client:
        def get(self, url, headers):
            assert url.endswith('/progress')
            current = next(snapshots)
            observed.append(current['run']['status'])
            return SimpleNamespace(json=lambda: current)
        def post(self, url, headers, json):
            assert observed == ['queued', 'running'], 'No release before current running attempt'
            return SimpleNamespace(status_code=200, text='ok')
    done = finish_api(Client(), {}, 'synthetic-run')
    assert done['run']['status'] == 'needs_review'


def test_http_bounded_creation_dedup_and_approval_export(tmp_path):
    app = create_fixture_app(tmp_path)
    with TestClient(app, base_url='http://127.0.0.1') as client:
        headers = {'x-pilot-token': app.state.token}
        session = client.get('/api/session', headers=headers).json()
        assert session['capabilities'] == {'sequential': True, 'bounded_subtasks': True}
        assert session['workflow_modes']['bounded_subtasks'] == 'owned_runner'
        payload = bounded_request()
        with ThreadPoolExecutor(2) as pool:
            responses = list(pool.map(lambda _: client.post('/api/runs/subtasks', headers=headers, json=payload), range(2)))
        assert all(r.status_code == 202 for r in responses)
        ids = [r.json()['id'] for r in responses]
        assert ids[0] == ids[1] and sorted(r.json()['created'] for r in responses) == [False, True]
        rid = ids[0]
        assert client.get('/api/runs/by-request/' + payload['request_key'], headers=headers).json() == {'id': rid, 'workflow': 'bounded_subtasks'}
        assert client.post('/api/runs', headers=headers,
                           json={k: payload[k] for k in ('query', 'request_key')}).status_code == 409
        assert client.post('/api/runs/subtasks', headers=headers,
                           json={**payload, 'retrieval_concurrency': 1}).status_code == 409
        prefix = f'/api/runs/{rid}'
        row = wait_for(lambda: client.get(f'/__fixture/runs/{rid}', headers=headers).json(),
                       lambda r: {'s01', 's02'} <= set(r['entered']))
        assert client.get(prefix + '/export', headers=headers).status_code == 409
        done = finish_api(client, headers, rid)
        assert len([e for e in done['run']['events'] if e['kind'] == 'attempt_started']) == 1
        assert len([e for e in done['run']['events'] if e['kind'] == 'subtask_submission']) == 1
        assert done['progress']['parent_status'] == 'needs_review'
        review = {'revision': 1, 'decision': 'approve', 'reviewer': 'synthetic-D', 'support_confirmed': True}
        assert client.post(prefix + '/review', headers=headers, json=review).status_code == 200
        cached = client.get(prefix + '/export', headers=headers).content
        assert b'fiction-1' in cached and b'PDF page 7' in cached
        assert client.get(prefix + '/export', headers=headers).content == cached
        edited = {**done['run']['draft'], 'title': 'Synthetic revised bounded brief'}
        assert client.put(prefix + '/draft', headers=headers, json={'revision': 1, 'draft': edited}).status_code == 200
        assert client.post(prefix + '/review', headers=headers, json=review).status_code == 409
        assert client.get(prefix + '/export', headers=headers).status_code == 409
        assert client.post(prefix + '/review', headers=headers, json={**review, 'revision': 2}).status_code == 200
        final = client.get(prefix + '/export', headers=headers).content
    restarted = create_fixture_app(tmp_path)
    with TestClient(restarted, base_url='http://127.0.0.1') as client:
        headers = {'x-pilot-token': restarted.state.token}
        assert client.get(prefix + '/export', headers=headers).content == final
        assert client.get('/api/runs/by-request/' + payload['request_key'], headers=headers).json()['id'] == rid
        with restarted.state.store.connection() as db:
            assert db.execute('SELECT content FROM exports WHERE run_id=? AND revision=1', (rid,)).fetchone()['content'].encode() == cached


def test_http_failure_retry_cancellation_and_restart(tmp_path):
    app = create_fixture_app(tmp_path)
    payload = bounded_request('E-D-http-recovery')
    with TestClient(app, base_url='http://127.0.0.1') as client:
        headers = {'x-pilot-token': app.state.token}
        rid = client.post('/api/runs/subtasks', headers=headers, json=payload).json()['id']
        prefix = f'/api/runs/{rid}'
        state = wait_for(lambda: client.get(f'/__fixture/runs/{rid}', headers=headers).json(),
                         lambda r: 's01' in r['entered'])
        first = state['attempt_id']
        assert client.post(f'/__fixture/runs/{rid}/release', headers=headers,
                           json={'stage': 's01', 'fail': True}).status_code == 200
        failed = wait_for(lambda: run_api(client, headers, rid), lambda r: r['run']['status'] == 'failed')
        assert failed['run']['draft'] is None
        assert client.get(prefix + '/export', headers=headers).status_code == 409
        assert client.post(prefix + '/retry', headers=headers).status_code == 202
        second = wait_for(lambda: client.get(f'/__fixture/runs/{rid}', headers=headers).json(),
                          lambda r: r['attempt_id'] not in (None, first) and 's01' in r['entered'])
        assert second['released'] == []
        assert client.post(prefix + '/cancel', headers=headers).status_code == 200
        interrupted = wait_for(lambda: run_api(client, headers, rid), lambda r: r['run']['status'] == 'interrupted')
        assert interrupted['run']['draft'] is None
    # Restart uses A's real shutdown/recovery, the same DB and a fresh session.
    restarted = create_fixture_app(tmp_path)
    with TestClient(restarted, base_url='http://127.0.0.1') as client:
        headers = {'x-pilot-token': restarted.state.token}
        assert client.get(prefix, headers=headers).json()['status'] == 'interrupted'
        assert client.post(prefix + '/retry', headers=headers).status_code == 202
        done = finish_api(client, headers, rid)
        attempts = [e['payload']['attempt_id'] for e in done['run']['events'] if e['kind'] == 'attempt_started']
        assert len(attempts) == len(set(attempts)) == 3
        assert done['run']['status'] == 'needs_review'
        assert not restarted.state.store.attempt_event(rid, first, 'late', {})


def test_http_active_shutdown_recovers_without_automatic_retry(tmp_path):
    app = create_fixture_app(tmp_path)
    with TestClient(app, base_url='http://127.0.0.1') as client:
        headers = {'x-pilot-token': app.state.token}
        rid = client.post('/api/runs/subtasks', headers=headers,
                          json=bounded_request('E-D-http-active-shutdown')).json()['id']
        active = wait_for(lambda: client.get(f'/__fixture/runs/{rid}', headers=headers).json(),
                          lambda r: 's01' in r['entered'])
        first = active['attempt_id']
        # Exiting the real lifespan while blocked exercises runtime shutdown.
    restarted = create_fixture_app(tmp_path)
    with TestClient(restarted, base_url='http://127.0.0.1') as client:
        headers = {'x-pilot-token': restarted.state.token}
        row = client.get(f'/api/runs/{rid}', headers=headers).json()
        assert row['status'] == 'interrupted' and row['draft'] is None and row['revision'] == 0
        assert len([e for e in row['events'] if e['kind'] == 'attempt_started']) == 1
        assert client.post(f'/api/runs/{rid}/retry', headers=headers).status_code == 202
        done = finish_api(client, headers, rid)
        assert done['progress']['attempt_id'] != first
        assert done['run']['status'] == 'needs_review'


def test_fixture_sequential_request_uses_only_fixed_worker(tmp_path):
    app = create_fixture_app(tmp_path)
    with TestClient(app, base_url='http://127.0.0.1') as client:
        headers = {'x-pilot-token': app.state.token}
        response = client.post('/api/runs', headers=headers,
                               json={'query': 'Fictional sequential observation', 'request_key': 'E-D-sequential-default'})
        assert response.status_code == 202
        rid = response.json()['id']
        row = wait_for(lambda: run_api(client, headers, rid), lambda r: r['run']['status'] == 'needs_review')
        assert row['progress']['mode'] == 'sequential' and row['progress']['branches'] == []
        assert row['run']['draft']['title'] == 'Synthetic sequential brief'
        assert row['run']['metrics']['model_calls'] == 0
        assert client.get(f'/api/runs/{rid}/export', headers=headers).status_code == 409


def test_fixture_callbacks_publish_real_progress_before_review(tmp_path):
    root, path, controls = prepare_files(tmp_path)
    corpus = Corpus(path)
    store = Store(root / 'synthetic.sqlite3')
    plan = Plan(query='Compare fictional districts', corpus_sha256=corpus.sha, subtasks=(
        Subtask(subtask_id='s01', operation='retrieve', query='district 1', timeout_seconds=180.),
        Subtask(subtask_id='s02', operation='retrieve', query='district 2', timeout_seconds=180.),
        Subtask(subtask_id='s03', operation='retrieve', query='district 3',
                dependencies=('s01',), timeout_seconds=180.)))
    rid, _ = store.create(ResearchRequest(query=plan.query, request_key='E-D-fixed-worker'), corpus.sha)
    read = lambda: store.get(rid)
    cancellation = threading.Event()
    with ThreadPoolExecutor(1) as caller:
        task = caller.submit(run_stored_plan, store, rid, plan, path, fixed.Operation(str(controls), str(path)),
                             fixed.Composer(str(controls)), fixed.Safety(str(controls)), cancellation=cancellation)
        try:
            row = wait_for(read, lambda r: {'s01', 's02'} <= set(gate_state(controls, r)['entered'])
                           and [b['status'] for b in progress_view(r, detailed=True)['branches']]
                           == ['running', 'running', 'waiting_on_dependency'])
            branches = progress_view(row, detailed=True)['branches']
            assert [b['status'] for b in branches] == ['running', 'running', 'waiting_on_dependency']
            release(controls, row, 's02')
            release(controls, row, 's01')
            row = wait_for(read, lambda r: 's03' in gate_state(controls, r)['entered'])
            release(controls, row, 's03')
            row = wait_for(read, lambda r: 'composition' in gate_state(controls, r)['entered']
                           and progress_view(r, detailed=True)['phase'] == 'composition')
            assert row['draft'] is None and row['status'] == 'running'
            assert all(b['status'] == 'completed' for b in progress_view(row, detailed=True)['branches'])
            release(controls, row, 'composition')
            row = wait_for(read, lambda r: 'safety' in gate_state(controls, r)['entered'])
            assert row['draft'] is None
            release(controls, row, 'safety')
            task.result(timeout=20)
        finally:
            cancellation.set()
    row = read()
    assert row['status'] == 'needs_review' and row['revision'] == 1
    assert [c['source_ids'] for c in row['draft']['claims']] == [['fiction-1'], ['fiction-2'], ['fiction-3']]
    # Counters count synthetic gateway callbacks, not actual model invocations.
    assert row['metrics']['model_calls'] == 1 and row['metrics']['guardrail_invocations'] == 1
    assert row['reviews'] == []
    # Until A's creation-route contract lands, this deliberately starts the
    # bounded run programmatically and verifies the real existing review API.
    from src.pilot.api import create_app
    def forbidden_generation(*_):
        raise AssertionError('No generation is permitted in this fixture')
    def app():
        return create_app(engine=SimpleNamespace(corpus=corpus, run=forbidden_generation),
                          database_path=store.path, run_inline=True)
    api = app()
    headers = {'x-pilot-token': api.state.token}
    url = f'/api/runs/{rid}'
    with TestClient(api, base_url='http://127.0.0.1') as client:
        before = client.get(url + '/progress', headers=headers).json()
        assert before['progress']['parent_status'] == 'needs_review'
        assert client.get(url + '/export', headers=headers).status_code == 409
        review = {'revision': 1, 'decision': 'approve', 'reviewer': 'synthetic-D', 'support_confirmed': True}
        assert client.post(url + '/review', headers=headers, json={**review, 'support_confirmed': False}).status_code == 409
        assert client.post(url + '/review', headers=headers, json=review).status_code == 200
        cached = client.get(url + '/export', headers=headers)
        assert cached.status_code == 200 and b'PDF page 1' in cached.content and b'PDF page 7' in cached.content
        assert client.get(url + '/export', headers=headers).content == cached.content
        edited = {**row['draft'], 'title': 'Synthetic corrected title'}
        assert client.put(url + '/draft', headers=headers, json={'revision': 1, 'draft': edited}).json() == {'revision': 2}
        assert client.post(url + '/review', headers=headers, json=review).status_code == 409
        assert client.get(url + '/export', headers=headers).status_code == 409
        assert client.post(url + '/review', headers=headers,
                           json={**review, 'revision': 2, 'decision': 'reject'}).status_code == 200
        assert client.get(url + '/export', headers=headers).status_code == 409
        assert client.put(url + '/draft', headers=headers, json={'revision': 2, 'draft': edited}).json() == {'revision': 3}
        assert client.post(url + '/review', headers=headers, json={**review, 'revision': 3}).status_code == 200
        final = client.get(url + '/export', headers=headers).content
        assert final != cached.content
    restarted = app()
    with TestClient(restarted, base_url='http://127.0.0.1') as client:
        headers = {'x-pilot-token': restarted.state.token}
        assert client.get(url + '/export', headers=headers).content == final
        snapshot = client.get(url, headers=headers).json()
        assert snapshot['revision'] == 3 and len(snapshot['reviews']) == 3
    with store.connection() as db:
        assert db.execute('SELECT content FROM exports WHERE run_id=? AND revision=1', (rid,)).fetchone()['content'].encode() == cached.content
