"""Private, stdlib-only diagnostic transport. Not an application model adapter.

Importing or inspecting a request never performs inference. Service execution
requires a separately authorized, hash-pinned protocol and a new output folder.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid


MODEL = 'ami-llama3.1:8b-4k'
OPTIONS = {'num_ctx': 4096, 'num_predict': 900, 'temperature': 0.0}
LIMIT = 1_000_000


class TransportFailure(ValueError):
    pass


def _reject_constant(_):
    raise TransportFailure('nonfinite_json')


def _loads(value):
    return json.loads(value, parse_constant=_reject_constant)


def read_json(path):
    payload = Path(path).read_bytes()
    if len(payload) > LIMIT:
        raise TransportFailure('input_too_large')
    return _loads(payload)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    """Atomic same-directory publication; filesystem retries never retry inference."""
    path = Path(path)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    for i, delay in enumerate((0, .02, .1, .3)):
        if delay:
            time.sleep(delay)
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if i == 3:
                raise


def request_body(frozen):
    if not isinstance(frozen, dict) or set(frozen) != {'messages', 'schema'}:
        raise TransportFailure('invalid_frozen_input')
    messages = frozen['messages']
    if not isinstance(messages, list) or len(messages) != 2 or not isinstance(frozen['schema'], dict):
        raise TransportFailure('invalid_frozen_input')
    converted = []
    for expected, message in zip(('system', 'human'), messages, strict=True):
        if (not isinstance(message, dict) or set(message) != {'type', 'content'}
                or message['type'] != expected or not isinstance(message['content'], str)):
            raise TransportFailure('invalid_mapper_message')
        converted.append({'role': 'user' if expected == 'human' else 'system', 'content': message['content']})
    result = {'model': MODEL, 'stream': True, 'options': dict(OPTIONS),
              'format': frozen['schema'], 'messages': converted, 'tools': []}
    if len(json.dumps(result, ensure_ascii=False, allow_nan=False).encode()) > LIMIT:
        raise TransportFailure('request_too_large')
    return result


def validate_body(body):
    if (not isinstance(body, dict) or set(body) != {'model', 'stream', 'options', 'format', 'messages', 'tools'}
            or body['model'] != MODEL or body['stream'] is not True
            or body['options'] != OPTIONS or body['tools'] != []):
        raise TransportFailure('changed_model_request')
    frozen = {'schema': body['format'], 'messages': [
        {'type': 'human' if m.get('role') == 'user' else m.get('role'), 'content': m.get('content')}
        for m in body['messages']]}
    if request_body(frozen) != body:
        raise TransportFailure('changed_model_messages')


def _remaining(deadline, clock):
    value = deadline - clock()
    if not math.isfinite(value) or value <= 0:
        raise TimeoutError('diagnostic_deadline')
    return value


def _connection(factory, timeout):
    # Direct HTTPConnection does not consult proxy variables or follow redirects.
    # Endpoint, host, port and paths cannot come from source/model content.
    return factory('localhost', 11434, timeout=timeout)


def verify_identity(digest, deadline, factory, clock):
    if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
        raise TransportFailure('invalid_model_pin')
    connection = _connection(factory, min(2, _remaining(deadline, clock)))
    try:
        connection.request('GET', '/api/tags')
        response = connection.getresponse()
        if response.status != 200:
            raise TransportFailure('model_metadata_unavailable')
        data = response.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise TransportFailure('model_metadata_too_large')
        body = _loads(data)
        matches = [m for m in body.get('models', []) if isinstance(m, dict)
                   and m.get('name', m.get('model')) == MODEL]
        if len(matches) != 1 or matches[0].get('digest') != digest:
            raise TransportFailure('model_identity_mismatch')
    finally:
        connection.close()


def stream_once(body, digest, deadline, emit=lambda _: None, *, connection_factory=http.client.HTTPConnection,
                clock=time.monotonic, on_bytes=lambda _: None):
    """One invocation, bounded stream and truthful partial/failure record.

    The owner process supplies a hard subprocess deadline as a second boundary.
    Closing a connection does not establish server-side request cancellation.
    """
    validate_body(body)
    started = clock()
    record = {'transport': 'ollama-native-stream-v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'started', 'model_calls_started': 0, 'response_complete': False, 'content': '',
        'finish': None, 'usage': None, 'chunks_received': 0, 'bytes_received': 0,
        'identity_before': None, 'identity_after': None, 'inflight_usage_unknown': False, 'started_monotonic': started,
        'backend_cancellation_verified': False, 'stages': []}
    connection = None
    last_progress = started
    def mark(stage):
        record['stages'].append({'stage': stage, 'elapsed_seconds': clock() - started})
        emit(record)
    def frame(line):
        if not line.strip():
            return
        data = _loads(line)
        if not isinstance(data, dict) or data.get('error'):
            raise TransportFailure('service_error')
        if data.get('model', MODEL) != MODEL:
            raise TransportFailure('response_model_mismatch')
        message = data.get('message') or {}
        if not isinstance(message, dict) or message.get('role', 'assistant') != 'assistant' or message.get('tool_calls'):
            raise TransportFailure('unexpected_response_message')
        text = message.get('content') or ''
        if not isinstance(text, str):
            raise TransportFailure('invalid_response_content')
        record['content'] += text
        record['chunks_received'] += 1
        if record['chunks_received'] == 1:
            mark('first_chunk')
        if data.get('done') is True:
            record['response_complete'] = True
            record['finish'] = {k: data[k] for k in ('model', 'created_at', 'done', 'done_reason', 'total_duration',
                'load_duration', 'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration') if k in data}
            counts = [data.get('prompt_eval_count'), data.get('eval_count')]
            if all(type(n) is int and n >= 0 for n in counts):
                record['usage'] = {'input_tokens': counts[0], 'output_tokens': counts[1], 'total_tokens': sum(counts)}
            mark('response_done')
    try:
        mark('worker_ready')
        verify_identity(digest, deadline - 1, connection_factory, clock)
        record['identity_before'] = True
        mark('identity_before_verified')
        # Reserve time for after-response identity verification and publication.
        call_deadline = deadline - 3
        connection = _connection(connection_factory, _remaining(call_deadline, clock))
        encoded = json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
        record['model_calls_started'] = 1
        record['inflight_usage_unknown'] = True
        mark('invocation_started')
        connection.request('POST', '/api/chat', body=encoded, headers={'Content-Type': 'application/json'})
        mark('request_written')
        response = connection.getresponse()
        record['http_status'] = response.status
        mark('response_headers')
        if response.status != 200:
            # Keep bounded native error bytes privately; never expose provider
            # error text or headers as a user-facing diagnostic message.
            on_bytes(response.read(min(LIMIT, 65536)))
            raise TransportFailure('redirect_forbidden' if 300 <= response.status < 400 else 'http_status_failure')
        pending = b''
        while not record['response_complete']:
            remaining = _remaining(call_deadline, clock)
            if connection.sock is not None:
                connection.sock.settimeout(remaining)
            part = response.read1(65536)
            if not part:
                if pending:
                    frame(pending)
                    pending = b''
                if not record['response_complete']:
                    raise TransportFailure('incomplete_stream')
                break
            retained = max(0, LIMIT - record['bytes_received'])
            on_bytes(part[:retained])
            record['bytes_received'] += len(part)
            if record['bytes_received'] > LIMIT:
                raise TransportFailure('response_too_large')
            if record['bytes_received'] == len(part):
                mark('first_body_bytes')
            pending += part
            while b'\n' in pending:
                line, pending = pending.split(b'\n', 1)
                frame(line)
                if record['response_complete']:
                    if pending.strip():
                        raise TransportFailure('data_after_completion')
                    break
            if clock() - last_progress >= 1:
                mark('stream_progress')
                last_progress = clock()
        record['inflight_usage_unknown'] = False
        connection.close()
        connection = None
        verify_identity(digest, deadline - .5, connection_factory, clock)
        record['identity_after'] = True
        record['status'] = 'completed_transport; engine validation pending'
        mark('completed')
    except Exception as error:
        record['status'] = 'failed'
        record['error_type'] = type(error).__name__
        record['error_code'] = str(error) if isinstance(error, TransportFailure) else 'transport_or_deadline_failure'
        # A complete done frame establishes completion even if later identity
        # verification fails; missing terminal metadata never implies zero usage.
        record['inflight_usage_unknown'] = bool(record['model_calls_started'] and not record['response_complete'])
        mark('failed')
    finally:
        if connection is not None:
            connection.close()
    record['elapsed_seconds'] = clock() - started
    emit(record)
    return record


def supervise(command, output, seconds):
    """Bound one owned child; never restart on timeout or operate on a saved PID."""
    output = Path(output)
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('A positive finite process budget is required')
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    write_json(output/'started.json', {'seconds': seconds, 'started_utc': datetime.now(timezone.utc).isoformat(),
                                      'monotonic_started': started})
    with (output/'stdout.txt').open('wb') as stdout, (output/'stderr.txt').open('wb') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        spawned = time.monotonic()
        timeout = False
        try:
            code = process.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            timeout = True
            process.kill()
            code = process.wait()
    result = {'returncode': code, 'timed_out': timeout, 'elapsed_seconds': time.monotonic()-started,
              'spawn_returned_monotonic': spawned, 'process_finished_monotonic': time.monotonic(),
              'backend_cancellation_verified': False, 'retry_performed': False}
    write_json(output/'process-result.json', result)
    return result


def main(argv=None):
    entry = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['inspect', 'service'])
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--contract', type=Path)
    parser.add_argument('--contract-sha256')
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--deadline', type=float)
    args = parser.parse_args(argv)
    if args.mode == 'inspect':
        body = request_body(read_json(args.input))
        print(json.dumps({'model': MODEL, 'options': OPTIONS, 'stream': True,
            'body_sha256': hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
            'model_calls': 0, 'engine_imported': 'src.pilot.engine' in sys.modules}))
        return 0
    if not all([args.output, args.contract, args.contract_sha256, args.authorization, args.deadline]):
        parser.error('service requires a hash-pinned authorized protocol, owned output and deadline')
    if sha(args.contract) != args.contract_sha256:
        raise TransportFailure('changed_contract')
    contract, authorization = read_json(args.contract), read_json(args.authorization)
    request_bytes = args.input.read_bytes()
    if (authorization.get('contract_sha256') != args.contract_sha256
            or authorization.get('human_reply') != contract['authorization_reply']
            or len(request_bytes) > LIMIT
            or hashlib.sha256(request_bytes).hexdigest() != contract['native_body_sha256']):
        raise TransportFailure('missing_or_changed_authorization')
    output = args.output.resolve()
    if not output.is_relative_to(args.contract.resolve().parent.parent) or not output.is_dir():
        raise TransportFailure('invalid_owned_output')
    if any((output/name).exists() for name in ('service-result.json', 'service-progress.json', 'response.ndjson')):
        raise TransportFailure('service_attempt_already_started')
    remaining = args.deadline-time.monotonic()
    if not 0 < remaining <= 60:
        raise TransportFailure('invalid_service_deadline')
    with (output/'response.ndjson').open('xb') as raw:
        def retain(part):
            raw.write(part)
            raw.flush()
        result = stream_once(_loads(request_bytes), contract['model_digest'], args.deadline,
            lambda value: write_json(output/'service-progress.json', {**value, 'worker_entry_monotonic': entry,
                'bootstrap_to_stream_seconds': value['started_monotonic']-entry, 'raw_stream_file': 'response.ndjson'}),
            on_bytes=retain)
    result['raw_stream_file'] = 'response.ndjson'
    result.update(worker_entry_monotonic=entry, bootstrap_to_stream_seconds=result['started_monotonic']-entry)
    write_json(output/'service-result.json', result)
    print(json.dumps({'status': result['status'], 'model_calls_started': result['model_calls_started'],
                      'response_complete': result['response_complete']}))
    return 0 if result['status'].startswith('completed_transport') else 1


if __name__ == '__main__':
    raise SystemExit(main())
