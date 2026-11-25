"""Prepare new offline evidence and a separate contract, with sockets blocked."""
import hashlib
import json
from pathlib import Path
import shutil
import socket
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
PRIOR = ROOT.parent / 'scoped-membership-coverage-development-2026-11-25'
sys.path.insert(0, str(PROJECT))

from scripts._llama_token_count import encoding
from src.pilot.subtasks._development_lineage import canonical, canonical_hash, runtime_inputs
from src.pilot.subtasks._fact_selection import SPAN_MAPPING_VERSION
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks._scoped_generation import COMPOSITION_VERSION
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


class Captured(Exception):
    pass


def replay(contract, case_id, saved_directory, counter, *, fixed_members=False):
    case = contract['cases'][case_id]
    plan = Plan.model_validate_json(json.dumps(case['plan']))
    captures = []

    def fixed(stage, schema, instruction, inputs):
        saved_path = saved_directory / f'{case_id}.{stage}.raw.json'
        saved = read(saved_path)
        parsed = json.loads(saved['raw'])
        reservation = len(counter.encode(instruction)) + len(counter.encode(
            json.dumps(inputs, ensure_ascii=False, separators=(',', ':')))) + 1156
        assert reservation <= 4096
        entry = {'stage': stage, 'reservation': reservation,
                 'original_raw_file_sha256': digest(saved_path), 'inputs': inputs}
        if stage == 'composition' and fixed_members:
            try:
                schema.model_validate(parsed)
            except ValueError:
                entry['old_raw_rejected_by_new_schema'] = True
            else:
                raise AssertionError('The old free-text claim must fail the new field contract')
            unit, = inputs['units']
            parsed = {'title': 'Analyst research brief', 'claims': [{'unit_id': unit['unit_id'],
                'component_id': unit['component_id'], 'targets': unit['required_membership']['targets']}]}
            entry['composition_authorship'] = 'assistant-authored fixed fields; not actual model generation'
        captures.append(entry)
        return {'raw': json.dumps(parsed), 'parsed': schema.model_validate(parsed).model_dump()}

    report = run_plan(plan, 'a' * 32, 'b' * 32, LocalBM25Adapter(case['corpus_path']))
    result = prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 60))
    assert result.diagnostics['application_rendered_memberships']
    assert not result.diagnostics['fallback_unit_ids']
    return {'case_id': case_id, 'actual_model_calls': 0, 'nemo_calls': 0, 'requests_reconstructed': True,
            'captures': captures, 'fixed_response_draft': result.draft,
            'raw_composer_output': result.diagnostics['raw_composer_output'],
            'application_rendering': result.diagnostics['application_rendered_memberships'],
            'new_model_quality_evidence': False, 'original_attempt_regraded': False}


def admission(contract, counter):
    results = {}
    plans = read(ROOT / 'pool/plans-v3-explicit-coverage.json')
    scopes = read(ROOT / 'question-scopes/manifest.json')['cases']
    for cid, entry in plans.items():
        case = {**entry, 'corpus_path': str(ROOT / 'pool' / entry['corpus_path']),
            'requested_scopes': str(ROOT / 'question-scopes' / scopes[cid]['path']),
            'requested_scopes_sha256': scopes[cid]['sha256']}
        plan = Plan.model_validate_json(json.dumps(case['plan']))
        assert digest(case['corpus_path']) == plan.corpus_sha256
        def capture(stage, schema, instruction, inputs):
            assert stage == 'mapping'
            reserved = len(counter.encode(instruction)) + len(counter.encode(
                json.dumps(inputs, ensure_ascii=False, separators=(',', ':')))) + 1156
            assert reserved <= 4096
            results[cid] = {'reserved': reserved}
            raise Captured
        binding = {case['requested_scopes']: case['requested_scopes_sha256']}
        report = run_plan(plan, 'a' * 32, 'b' * 32, LocalBM25Adapter(case['corpus_path']))
        try:
            prepare_composer({**contract, 'input_sha256': binding}, case, plan, capture, None)(
                report, ModelAccess(time.monotonic() + 60))
        except Captured:
            pass
        else:
            raise AssertionError('Admission must stop before any model response')
    return results


def main():
    if (ROOT / 'development-contract.json').exists():
        raise ValueError('Already prepared; preserve the frozen directory')
    prior = read(PRIOR / 'development-contract.json')
    for name in ('pool', 'question-scopes'):
        shutil.copytree(PRIOR / name, ROOT / name)
    for name in ('run_case.py', 'run_qualification_case.py', 'compile-qualification.py',
                 'pool-freeze-audit.json', 'new-source-provenance.json', 'eia-glossary-n.html', 'eia-glossary-n.txt'):
        shutil.copyfile(PRIOR / name, ROOT / name)
    contract = {**prior, 'as_of': '2026-11-25', 'mapping_version': SPAN_MAPPING_VERSION,
        'composition_version': COMPOSITION_VERSION, 'output_directory': str(ROOT / 'actual-development-v1'),
        'purpose': 'Verify two required exact member fields and source rendering, then category-definition parity.',
        'authorization_reply': 'Authorize scoped explicit membership development diagnostics',
        'source_review_protocol': str(ROOT / 'source-review-protocol.md'),
        'source_review_protocol_sha256': digest(ROOT / 'source-review-protocol.md'),
        'model_identity_live_verified_before_grant': False}
    pins = runtime_inputs()
    for case in contract['cases'].values():
        for name in ('corpus_path', 'requested_scopes'):
            pins[case[name]] = digest(case[name])
    contract['input_sha256'] = pins
    counter = encoding(read(Path(contract['tokenizer_path'])))
    results = [replay(contract, 'cq1-a48', PRIOR / 'actual-development-v1', counter, fixed_members=True),
        replay(contract, 'cq1-a24', ROOT.parent / 'scoped-membership-rendering-2026-11-15/actual-development-v1', counter)]
    write(ROOT / 'offline-replays.json', {'sockets_blocked': True, 'actual_model_calls': 0, 'results': results})
    checks = admission(contract, counter)
    write(ROOT / 'mapper-admission.json', {'actual_model_calls': 0, 'sockets_blocked': True, 'checks': checks,
        'maximum_reservation': max(row['reserved'] for row in checks.values())})
    paths = [Path(__file__), Path(contract['tokenizer_path']), ROOT / 'source-review-protocol.md',
        PROJECT / 'tests/test_subtask_membership_coverage.py',
        PROJECT / 'docs/concurrency/c-explicit-membership-2026-11-25.md']
    paths += [p for p in ROOT.iterdir() if p.is_file() and p.suffix in {'.py', '.json', '.html', '.txt'}
              and p.name not in {'offline-tests.txt', 'before-sha256.json'}]
    paths += list((ROOT / 'pool').iterdir()) + list((ROOT / 'question-scopes').iterdir())
    pins.update({str(path.resolve()): digest(path) for path in paths if path.is_file()})
    identity = {key: contract[key] for key in ('model_snapshot', 'settings', 'composition_contract')}
    contract['pipeline_identity'] = hashlib.sha256(canonical({**identity, 'runtime_inputs': runtime_inputs()}).encode()).hexdigest()
    contract['contract_sha256'] = canonical_hash(contract)
    write(ROOT / 'development-contract.json', contract)
    print(json.dumps({'contract_sha256': contract['contract_sha256'], 'pins': len(pins),
        'offline_replays': len(results), 'mapper_admission': len(checks), 'execution_authorized': False}))


if __name__ == '__main__':
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('offline preparation')):
        with patch.object(socket, 'create_connection', side_effect=AssertionError('offline preparation')):
            main()
