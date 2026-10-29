"""Offline native-wire/lifecycle contracts. No real model or network requests."""
import copy
import io
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel
import pytest

from scripts import _mapper_transport as transport


DIGEST = 'a' * 64


def frozen():
    return {'schema': {'title': 'Answer', 'type': 'object', 'properties': {'label': {'type': 'string'}}},
        'messages': [{'type': 'system', 'content': 'Return JSON.'},
                     {'type': 'human', 'content': 'A synthetic question.'}]}


def terminal(text='{"label":"fixed"}', **extra):
    return {'model': transport.MODEL, 'message': {'role': 'assistant', 'content': text},
            'done': True, 'done_reason': 'stop', 'prompt_eval_count': 10, 'eval_count': 4, **extra}


def ndjson(*frames):
    return b''.join(json.dumps(f, ensure_ascii=False).encode() + b'\n' for f in frames)


class FakeResponse:
    def __init__(self, data, status=200, pieces=None):
        self.status = status
        self.data = io.BytesIO(data)
        self.pieces = iter(pieces) if pieces is not None else None

    def read(self, size):
        return self.data.read(size)

    def read1(self, size):
        value = next(self.pieces, b'') if self.pieces is not None else self.data.read(size)
        if isinstance(value, Exception):
            raise value
        return value


class Factory:
    def __init__(self, response, digest=DIGEST, after_digest=None):
        self.calls = []
        tags = lambda d: FakeResponse(json.dumps({'models':[{'name':transport.MODEL,'digest':d}]}).encode())
        self.responses = iter([tags(digest), response, tags(after_digest or digest)])
        self.connections = []

    def __call__(self, host, port, timeout):
        assert (host, port) == ('localhost', 11434) and timeout > 0
        parent = self
        class Connection:
            sock = None
            closed = False
            def request(self, method, path, body=None, headers=None):
                parent.calls.append((method,path,body,headers))
            def getresponse(self):
                return next(parent.responses)
            def close(self):
                self.closed = True
        connection = Connection()
        self.connections.append(connection)
        return connection


def run(response, **kwargs):
    factory = Factory(response, **kwargs)
    raw, events = [], []
    result = transport.stream_once(transport.request_body(frozen()), DIGEST, time.monotonic()+20,
        lambda r: events.append(copy.deepcopy(r)), connection_factory=factory, on_bytes=raw.append)
    return result, factory, b''.join(raw), events


def test_native_body_matches_real_pinned_sdk_serialization_with_mock_http(monkeypatch):
    monkeypatch.delenv('OLLAMA_API_KEY', raising=False)
    class Reply(BaseModel):
        label: str
    received = []
    def handler(request):
        assert request.method == 'POST' and request.url.path == '/api/chat'
        received.append(json.loads(request.content))
        return httpx.Response(200, content=ndjson(terminal()), headers={'Content-Type':'application/x-ndjson'})
    model = ChatOllama(model=transport.MODEL, temperature=0, num_ctx=4096, num_predict=900,
        client_kwargs={'transport':httpx.MockTransport(handler), 'timeout':90, 'trust_env':False})
    value = frozen();value['schema'] = Reply.model_json_schema()
    response = model.with_structured_output(Reply, include_raw=True).invoke([
        SystemMessage(content=value['messages'][0]['content']), HumanMessage(content=value['messages'][1]['content'])])
    assert response['parsed'].label == 'fixed'
    assert received == [transport.request_body(value)]


def test_stream_chunks_retain_unicode_exact_bytes_usage_and_stages():
    frames = ndjson({'model':transport.MODEL,'message':{'role':'assistant','content':'{"label":"ไทย'},'done':False},
                    terminal(' — fixed"}'))
    pieces = [frames[:11], frames[11:53], frames[53:]]
    result, factory, raw, events = run(FakeResponse(b'', pieces=pieces))
    assert result['response_complete'] and result['content'] == '{"label":"ไทย — fixed"}'
    assert result['usage'] == {'input_tokens':10,'output_tokens':4,'total_tokens':14}
    assert raw == frames and result['identity_before'] and result['identity_after']
    assert [c[0] for c in factory.calls] == ['GET','POST','GET']
    assert all(c.closed for c in factory.connections)
    stages = [s['stage'] for s in result['stages']]
    assert stages.index('invocation_started') < stages.index('response_headers') < stages.index('first_chunk') < stages.index('completed')
    assert not result['backend_cancellation_verified'] and not result['inflight_usage_unknown']


@pytest.mark.parametrize('data,code', [(b'{bad}\n','transport_or_deadline_failure'),
    (ndjson({'message':{'content':'partial'},'done':False}),'incomplete_stream'),
    (ndjson({'error':'provider text is private'}),'service_error'),
    (ndjson(terminal(eval_count=float('nan'))),'nonfinite_json'),
    (ndjson(terminal(model='other-model')),'response_model_mismatch'),
    (ndjson(terminal(message={'role':'assistant','content':'x','tool_calls':[{'name':'unexpected'}]})),'unexpected_response_message')])
def test_malformed_incomplete_and_unexpected_streams_preserve_failure(data,code):
    result,factory,raw,_ = run(FakeResponse(data))
    assert result['status']=='failed' and result['error_code']==code
    assert result['model_calls_started']==1 and result['usage'] is None
    assert raw==data and len([c for c in factory.calls if c[0]=='POST'])==1
    assert result['inflight_usage_unknown'] and all(c.closed for c in factory.connections)


def test_socket_timeout_retains_partial_content_without_imputing_zero_usage():
    first=ndjson({'message':{'content':'partial'},'done':False})
    result,_,raw,_=run(FakeResponse(b'',pieces=[first,TimeoutError('private exception detail')]))
    assert result['status']=='failed' and result['content']=='partial' and result['usage'] is None
    assert result['error_code']=='transport_or_deadline_failure' and raw==first


@pytest.mark.parametrize('status',[302,429,500])
def test_http_errors_are_not_followed_or_retried(status):
    result,factory,raw,_=run(FakeResponse(b'private failure details',status))
    assert result['status']=='failed' and result['http_status']==status
    assert len(factory.calls)==2 and raw==b'private failure details'
    assert 'private failure details' not in json.dumps(result)


def test_identity_failure_before_request_performs_no_inference():
    result,factory,_,_=run(FakeResponse(ndjson(terminal())),digest='b'*64)
    assert result['model_calls_started']==0 and result['status']=='failed'
    assert [c[0] for c in factory.calls]==['GET']


def test_identity_change_after_done_keeps_completed_response_but_fails_gate():
    result,_,_,_=run(FakeResponse(ndjson(terminal())),after_digest='b'*64)
    assert result['status']=='failed' and result['response_complete'] and result['identity_after'] is None
    assert result['usage']['output_tokens']==4 and not result['inflight_usage_unknown']


def test_missing_usage_is_unknown_and_last_frame_needs_no_final_newline():
    data=terminal();data.pop('eval_count')
    result,_,_,_=run(FakeResponse(json.dumps(data).encode()))
    assert result['response_complete'] and result['usage'] is None


def test_response_cap_stops_before_unbounded_storage():
    result,_,raw,_=run(FakeResponse(b'',pieces=[b'x'*(transport.LIMIT+1)]))
    assert result['status']=='failed' and result['error_code']=='response_too_large'
    assert len(raw)==transport.LIMIT and result['usage'] is None


def test_deadline_is_cumulative_not_reset_by_chunks():
    class Clock:
        now=0
        def __call__(self):return self.now
    clock=Clock();response=FakeResponse(b'',pieces=[ndjson({'message':{'content':'partial'},'done':False})])
    original=response.read1
    def delayed(size):clock.now=18;return original(size)
    response.read1=delayed
    factory=Factory(response)
    result=transport.stream_once(transport.request_body(frozen()),DIGEST,20,connection_factory=factory,clock=clock)
    assert result['status']=='failed' and result['error_type']=='TimeoutError'
    assert len([c for c in factory.calls if c[0]=='POST'])==1


@pytest.mark.parametrize('change',['role','model','stream','options','tools'])
def test_changed_parameters_are_rejected_before_network(change):
    body=transport.request_body(frozen())
    if change=='role':body['messages'][1]['role']='tool'
    elif change=='model':body['model']='another'
    elif change=='stream':body['stream']=False
    elif change=='options':body['options']['temperature']=1
    else:body['tools']=[{'name':'execute'}]
    with pytest.raises(ValueError):transport.validate_body(body)


def test_inspect_subprocess_does_not_import_the_engine_or_provider_framework(tmp_path):
    value=tmp_path/'frozen.json';value.write_text(json.dumps(frozen()),encoding='utf-8')
    result=subprocess.run([sys.executable,'-c',
        "import sys; from scripts import _mapper_transport as t; "
        "assert not any(n.startswith(('src.pilot.engine','nemoguardrails','langchain_')) for n in sys.modules); "
        "raise SystemExit(t.main(['inspect','--input',sys.argv[1]]))",str(value)],capture_output=True,text=True,timeout=10)
    assert result.returncode==0 and json.loads(result.stdout)['model_calls']==0
    assert not json.loads(result.stdout)['engine_imported']


def test_owned_sleeping_process_is_killed_once_and_failure_is_persisted(tmp_path):
    out=tmp_path/'owned'
    result=transport.supervise([sys.executable,'-c','import time; time.sleep(10)'],out,.1)
    assert result['timed_out'] and result['returncode']!=0 and not result['retry_performed']
    assert json.loads((out/'process-result.json').read_text())==result
    with pytest.raises(FileExistsError):transport.supervise([sys.executable,'-c','pass'],out,.1)


def test_atomic_publication_failure_keeps_the_previous_record(tmp_path,monkeypatch):
    path=tmp_path/'record.json';path.write_text('{"original":true}',encoding='utf-8')
    def locked(*_):raise PermissionError('locked')
    monkeypatch.setattr(Path,'replace',locked)
    monkeypatch.setattr(transport.time,'sleep',lambda _:None)
    with pytest.raises(PermissionError):transport.write_json(path,{'new':True})
    assert path.read_text()=='{"original":true}' and list(tmp_path.glob('*.tmp'))
