"""Verify preparation with saved responses and blocked sockets, never inference."""
import importlib.util
import json
from pathlib import Path
import socket
import sys
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from scripts._llama_token_count import encoding
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


def read(path):
    return json.loads(path.read_bytes())


class Captured(Exception):
    pass


def main():
    contract = read(ROOT / 'development-contract.json')
    counter = encoding(read(Path(contract['tokenizer_path'])))
    checks = {}
    def callback(stage, schema, instruction, inputs):
        reserve = len(counter.encode(instruction)) + len(counter.encode(
            json.dumps(inputs, ensure_ascii=False, separators=(',', ':')))) + 1156
        assert reserve <= 4096
        checks[current_case] = {'mapping_reservation': reserve}
        raise Captured

    plans = read(ROOT / 'pool/plans-v3-explicit-coverage.json')
    scope_rows = read(ROOT / 'question-scopes/manifest.json')['cases']
    for current_case, entry in plans.items():
        case = {**entry, 'corpus_path': str(ROOT / 'pool' / entry['corpus_path']),
                'requested_scopes': str(ROOT / 'question-scopes' / scope_rows[current_case]['path']),
                'requested_scopes_sha256': scope_rows[current_case]['sha256']}
        plan = Plan.model_validate_json(json.dumps(case['plan']))
        assert digest(case['corpus_path']) == plan.corpus_sha256
        pin = {case['requested_scopes']: case['requested_scopes_sha256']}
        report = run_plan(plan, 'a' * 32, 'b' * 32, LocalBM25Adapter(case['corpus_path']))
        composer = prepare_composer({**contract, 'input_sha256': pin}, case, plan, callback, None)
        try:
            composer(report, ModelAccess(time.monotonic() + 60))
        except Captured:
            pass
        else:
            raise AssertionError('Preparation must stop before inference')
    # Prior accepted private rendering is replayed, with no new generated answer.
    current_case = 'cq1-a24'
    case = contract['cases'][current_case]
    plan = Plan.model_validate_json(json.dumps(case['plan']))
    old = ROOT.parent / 'scoped-membership-rendering-2026-11-15/actual-development-v1'
    stages = []
    def fixed(stage, schema, instruction, inputs):
        saved = read(old / f'{current_case}.{stage}.raw.json')
        reserve = len(counter.encode(instruction)) + len(counter.encode(
            json.dumps(inputs, ensure_ascii=False, separators=(',', ':')))) + 1156
        assert reserve <= 4096
        stages.append({'stage': stage, 'reservation': reserve})
        return {'raw': saved['raw'], 'parsed': schema.model_validate(json.loads(saved['raw'])).model_dump()}
    report = run_plan(plan, 'a' * 32, 'b' * 32, LocalBM25Adapter(case['corpus_path']))
    result = prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 60))
    assert result.diagnostics['application_rendered_memberships']
    assert not result.diagnostics['fallback_unit_ids']
    compiler_path = ROOT / 'compile-qualification.py'
    spec = importlib.util.spec_from_file_location('membership_qualification_compiler', compiler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with patch.object(sys, 'argv', [str(compiler_path), '--as-of', '2026-11-25',
                                   '--development-sha256', contract['contract_sha256']]):
        try:
            module.main()
        except ValueError as error:
            assert str(error) == 'Two passing current development results/assessments are missing', str(error)
        else:
            raise AssertionError('Qualification cannot compile before current development passes')
    payload = {'model_calls': 0, 'safety_calls': 0, 'sockets_blocked': True,
        'future_pool_mapper_admission': checks, 'historical_a24_replay': {
            'stages': stages, 'draft': result.draft, 'new_quality_evidence': False},
        'qualification_compiler_rejected_missing_current_development': True}
    with (ROOT / 'offline-validation.json').open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(payload, indent=2) + '\n')
    print(json.dumps({'mapper_admission_checks': len(checks),
                      'maximum_mapping_reservation': max(row['mapping_reservation'] for row in checks.values()),
                      'a24_historical_replay_passed': True, 'model_calls': 0}))


if __name__ == '__main__':
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('offline check')):
        with patch.object(socket, 'create_connection', side_effect=AssertionError('offline check')):
            main()
