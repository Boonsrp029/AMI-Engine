"""Freeze the reviewed shared-unit regression fix before any execution grant."""
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from src.pilot.subtasks._development_lineage import canonical, canonical_hash, runtime_inputs
from src.pilot.subtasks.qualification import digest
from scripts._llama_token_count import encoding


def main():
    contract_path = ROOT / 'development-contract.json'
    contract = json.loads(contract_path.read_text(encoding='utf-8'))
    if (ROOT / 'grant.json').exists() or Path(contract['output_directory']).exists():
        raise ValueError('Cannot revise an authorized or executed contract')
    previous = ROOT / 'development-contract-candidate.json'
    with previous.open('xb') as stream:
        stream.write(contract_path.read_bytes())
    expected_changes = {str(ROOT.parents[2] / relative) for relative in (
        'src/pilot/subtasks/_request_focus.py', 'src/pilot/subtasks/_scoped_generation.py',
        'tests/test_subtask_membership_coverage.py', 'docs/concurrency/c-explicit-membership-2026-11-25.md')}
    changes = {path for path, sha in contract['input_sha256'].items() if digest(path) != sha}
    if changes != expected_changes:
        raise ValueError('Unexpected candidate drift')
    for path in changes:
        contract['input_sha256'][path] = digest(path)
    spec = importlib.util.spec_from_file_location('explicit_membership_offline_preparation', ROOT / 'prepare.py')
    preparation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preparation)
    counter = encoding(json.loads(Path(contract['tokenizer_path']).read_bytes()))
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('offline refresh')):
        with patch.object(socket, 'create_connection', side_effect=AssertionError('offline refresh')):
            results = [preparation.replay(contract, 'cq1-a48', preparation.PRIOR / 'actual-development-v1', counter,
                                           fixed_members=True),
                preparation.replay(contract, 'cq1-a24', ROOT.parent / 'scoped-membership-rendering-2026-11-15/actual-development-v1', counter)]
            checks = preparation.admission(contract, counter)
    for name, value in (
        ('offline-replays.json', {'sockets_blocked': True, 'actual_model_calls': 0, 'results': results}),
        ('mapper-admission.json', {'actual_model_calls': 0, 'sockets_blocked': True, 'checks': checks,
                                 'maximum_reservation': max(row['reserved'] for row in checks.values())}),
    ):
        path = ROOT / name
        with path.with_name(path.stem + '-candidate.json').open('xb') as stream:
            stream.write(path.read_bytes())
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        contract['input_sha256'][str(path)] = digest(path)
    contract['input_sha256'][str(Path(__file__).resolve())] = digest(__file__)
    identity = {key: contract[key] for key in ('model_snapshot', 'settings', 'composition_contract')}
    contract['pipeline_identity'] = hashlib.sha256(canonical({**identity, 'runtime_inputs': runtime_inputs()}).encode()).hexdigest()
    contract['contract_sha256'] = canonical_hash(contract)
    contract_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'contract_sha256': contract['contract_sha256'], 'pins': len(contract['input_sha256']),
                      'actual_model_calls': 0, 'execution_authorized': False}))


if __name__ == '__main__':
    main()
