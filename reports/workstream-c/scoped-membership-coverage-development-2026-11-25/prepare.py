"""Offline retained-response replay and preparation; cannot authorize inference."""
import hashlib
import json
from pathlib import Path
import socket
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
sys.path.insert(0, str(PROJECT))

from scripts._llama_token_count import encoding
from src.pilot.subtasks._development_lineage import canonical, canonical_hash, runtime_inputs
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks._scoped_generation import COMPOSITION_VERSION
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan

PRIOR = ROOT.parent / 'scoped-power-attribution-development-2026-11-20'
MEMBERSHIP = ROOT.parent / 'scoped-membership-rendering-2026-11-15'


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def replay():
    contract = read(PRIOR / 'qualification-contract.json')
    case = contract['cases']['cq1-a48']
    plan = Plan.model_validate_json(json.dumps(case['plan']))
    assert digest(case['corpus_path']) == plan.corpus_sha256
    counter = encoding(read(Path(contract['tokenizer_path'])))
    captures = []

    def fixed(stage, schema, instruction, inputs):
        saved = read(PRIOR / f'actual-cq1/cq1-a48.{stage}.raw.json')
        parsed = json.loads(saved['raw'])
        reservation = len(counter.encode(instruction)) + len(counter.encode(
            json.dumps(inputs, ensure_ascii=False, separators=(',', ':')))) + 1156
        assert reservation <= 4096
        captures.append({'stage': stage, 'instruction': instruction, 'inputs': inputs,
                         'reserved_tokens': reservation, 'retained_raw': saved['raw']})
        return {'raw': saved['raw'], 'parsed': schema.model_validate(parsed).model_dump()}

    report = run_plan(plan, 'a' * 32, 'b' * 32, LocalBM25Adapter(case['corpus_path']))
    callback = prepare_composer(contract, case, plan, fixed, None)
    try:
        callback(report, ModelAccess(time.monotonic() + 60))
    except ValueError as error:
        assert str(error) == 'Raw membership claim omits a requested source-listed member', str(error)
        failure = str(error)
    else:
        raise AssertionError('The incomplete retained response must fail')
    result = {'case': 'cq1-a48', 'model_calls': 0, 'safety_calls': 0, 'sockets_blocked': True,
              'request_status': 'offline reconstruction; retained responses are original',
              'original_attempt_regraded': False, 'rejected': True, 'error': failure,
              'retained_raw_sha256': digest(PRIOR / 'actual-cq1/cq1-a48.composition.raw.json'),
              'requests': captures}
    write(ROOT / 'retained-replay.json', result)


def freeze():
    contract = read(PRIOR / 'development-contract.json')
    prior_qualification = read(PRIOR / 'qualification-contract.json')
    membership = read(MEMBERSHIP / 'development-contract.json')
    contract['cases'] = {'cq1-a48': prior_qualification['cases']['cq1-a48'],
                         'cq1-a24': membership['cases']['cq1-a24']}
    contract.update(case_ids=list(contract['cases']), as_of='2026-11-25',
        output_directory=str(ROOT / 'actual-development-v1'),
        purpose='Check both explicitly requested list members, then preserve verified category-definition rendering.',
        authorization_reply='Authorize scoped membership coverage development diagnostics',
        composition_version=COMPOSITION_VERSION, model_identity_live_verified_before_grant=False,
        source_review_protocol=str(ROOT / 'source-review-protocol.md'),
        source_review_protocol_sha256=digest(ROOT / 'source-review-protocol.md'))
    # Reuse the established owned-process wrapper, scoped to these two consumed cases.
    runner = (PRIOR / 'run_case.py').read_text(encoding='utf-8').replace('cq1-a29', 'cq1-a48').replace(
        'cq1-a43', 'cq1-a24')
    (ROOT / 'run_case.py').write_text(runner, encoding='utf-8')
    pins = runtime_inputs()
    paths = [Path(__file__), ROOT / 'run_case.py', ROOT / 'source-review-protocol.md',
             ROOT / 'retained-replay.json', Path(contract['tokenizer_path']),
             PROJECT / 'tests/test_subtask_membership_coverage.py']
    for case in contract['cases'].values():
        paths.extend(Path(case[name]) for name in ('corpus_path', 'requested_scopes'))
    pins.update({str(path.resolve()): digest(path) for path in paths})
    contract['input_sha256'] = pins
    identity = {key: contract[key] for key in ('model_snapshot', 'settings', 'composition_contract')}
    contract['pipeline_identity'] = hashlib.sha256(canonical({**identity, 'runtime_inputs': runtime_inputs()}).encode()).hexdigest()
    contract['contract_sha256'] = canonical_hash(contract)
    write(ROOT / 'development-contract.json', contract)
    print(json.dumps({'contract_sha256': contract['contract_sha256'], 'pins': len(pins),
                      'execution_authorized': False}))


if __name__ == '__main__':
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('offline preparation')):
        with patch.object(socket, 'create_connection', side_effect=AssertionError('offline preparation')):
            replay()
            freeze()
