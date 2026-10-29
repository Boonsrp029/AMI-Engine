"""Synthetic intake limits; no inference, external service or real review data."""
import asyncio
import json
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

from src.pilot.api import create_app
from src.pilot.engine import Corpus


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    monkeypatch.delenv('AMI_PILOT_IDENTITY_FILE', raising=False)
    corpus = Corpus('tests/fixtures/release/smoke_corpus.json')
    calls = []
    def run(query, event):
        calls.append(query)
        return {'draft': {'title': 'Synthetic', 'claims': [], 'warnings': ['No evidence.']},
                'sources': {}, 'metrics': {'model_calls': 0}}
    app = create_app(engine=SimpleNamespace(corpus=corpus, run=run), database_path=tmp_path/'pilot.sqlite3', run_inline=True)
    with TestClient(app, base_url='http://127.0.0.1') as client:
        yield app, client, calls


def request(app_client, parts, **headers):
    app, client, _ = app_client
    return client.post('/api/runs', content=iter(parts), headers={'X-Pilot-Token': app.state.token,
        'Content-Type': 'application/json', **headers})


def test_headerless_chunked_body_cannot_bypass_the_100kb_limit(app_client):
    body = json.dumps({'query': 'Synthetic body limit question', 'request_key': 'synthetic-body-one'}).encode()
    response = request(app_client, [b' ' * 60_000, b' ' * 40_000, body])
    assert response.status_code == 413
    assert not app_client[2] and app_client[0].state.store.list() == []


def test_small_chunked_request_retains_existing_behavior(app_client):
    body = json.dumps({'query': 'Synthetic body limit question', 'request_key': 'synthetic-body-two'}).encode()
    response = request(app_client, [body[:20], body[20:]])
    assert response.status_code == 202
    assert app_client[2] == ['Synthetic body limit question']


def test_actual_bytes_are_checked_even_if_declared_length_is_too_small(app_client):
    response = request(app_client, [b' ' * 100_001], **{'Content-Length': '1'})
    assert response.status_code == 413
    assert not app_client[2]


def test_negative_content_length_is_rejected_without_creating_a_task(app_client):
    body = json.dumps({'query': 'Synthetic body limit question', 'request_key': 'synthetic-body-three'}).encode()
    response = request(app_client, [body], **{'Content-Length': '-1'})
    assert response.status_code == 400
    assert not app_client[2]


def test_existing_authentication_still_precedes_body_consumption(app_client):
    _, client, calls = app_client
    assert client.post('/api/runs', content=iter([b' ' * 100_001])).status_code == 403
    assert not calls


def test_oversized_declared_body_is_rejected_without_reading_it():
    from src.pilot._request_body import RequestBodyLimit
    async def scenario():
        sent = []
        async def unreachable(*_):
            pytest.fail('Body or application must not be reached')
        async def send(message): sent.append(message)
        await RequestBodyLimit(unreachable)({'type': 'http', 'headers': [(b'content-length', b'100001')]}, unreachable, send)
        assert sent[0]['status'] == 413
    asyncio.run(scenario())


@pytest.mark.parametrize('chunks,expected', [([b'x' * 100_000], 200), ([b'x' * 50_000, b'x' * 50_001], 413),
                                           (['é'.encode() * 50_001], 413)])
def test_actual_limit_counts_bytes_and_includes_the_final_chunk(chunks, expected):
    from src.pilot._request_body import RequestBodyLimit
    async def scenario():
        messages = iter([{'type': 'http.request', 'body': data, 'more_body': i < len(chunks)-1}
                         for i, data in enumerate(chunks)])
        sent, received = [], []
        async def receive(): return next(messages)
        async def send(message): sent.append(message)
        async def app(scope, receive, send):
            received.append(await receive())
            await send({'type': 'http.response.start', 'status': 200, 'headers': []})
        await RequestBodyLimit(app)({'type': 'http', 'headers': []}, receive, send)
        assert sent[0]['status'] == expected
        assert bool(received) == (expected == 200)
        if received: assert received[0]['body'] == b''.join(chunks) and not received[0]['more_body']
    asyncio.run(scenario())


def test_stalled_upload_has_a_bounded_wait_and_does_not_start_the_application():
    from src.pilot._request_body import RequestBodyLimit
    async def scenario():
        sent = []
        async def receive():
            await asyncio.Event().wait()
        async def send(message): sent.append(message)
        async def app(*_): pytest.fail('Timed-out body must not reach the application')
        await asyncio.wait_for(RequestBodyLimit(app, timeout_seconds=0.01)(
            {'type': 'http', 'headers': []}, receive, send), timeout=1)
        assert sent[0]['status'] == 408
    asyncio.run(scenario())


def test_disconnect_abandons_body_without_executing_application():
    from src.pilot._request_body import RequestBodyLimit
    async def scenario():
        async def receive(): return {'type': 'http.disconnect'}
        async def unreachable(*_): pytest.fail('Disconnected request must not execute or respond')
        await RequestBodyLimit(unreachable)({'type': 'http', 'headers': []}, receive, unreachable)
    asyncio.run(scenario())
