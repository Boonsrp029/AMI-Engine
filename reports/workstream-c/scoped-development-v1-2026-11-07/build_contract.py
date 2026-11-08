"""Freeze exact applied source and data after offline checks. Never issue grants."""
import hashlib
import json
from pathlib import Path

from src.pilot.subtasks._development_lineage import runtime_inputs
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks._composition_instruction import CONCURRENT_COMPOSITION_VERSION
from src.pilot.subtasks._title_scope import TITLE_SCOPE_VERSION


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def main():
    here = Path(__file__).resolve().parent
    project = Path.cwd().resolve()
    prior = project/'reports/workstream-c/scoped-disclosures-2026-11-07'
    prep = json.loads((prior/'prepared-development-data/preparation.json').read_text())
    caller = project/'src/pilot/subtasks/qualification_runner.py'
    assert 'prepare_composer(' in caller.read_text(), 'A activation must be applied'
    full = (prior/'activated-full-offline-tests.txt').read_text()
    assert 'passed, 14 warnings in' in full and 'FAILED ' not in full, 'Applied-revision full checks required'
    c = {'phase': 'development', 'composition_contract': prep['composition_contract'],
        'case_ids': ['cq-p01', 'cq-p02'], 'cases': {cid: row['frozen_case'] for cid, row in prep['cases'].items()},
        'as_of': '2026-11-07', 'model_snapshot': prep['model_snapshot'], 'settings': prep['settings'],
        'project_root': str(project), 'output_directory': str(here/'actual-development-v1'),
        'limits': {'main_calls_per_case': 4, 'nemo_per_case': 1, 'seconds_per_case': 180, 'retries': 0},
        'warmups': 0, 'mapping_version': 'cq-mapper-v7-scoped-disclosures',
        'disclosure_version': 'cq-scoped-disclosures-v1', 'wire_version': 'cq-scoped-selection-v1',
        'composition_version': CONCURRENT_COMPOSITION_VERSION, 'title_scope_version': TITLE_SCOPE_VERSION,
        'purpose': 'Actual scoped two-case development gate; no CQ1 authorization',
        'authorization_reply': 'Authorize scoped v1 two-case development diagnostic',
        'input_sha256': runtime_inputs(), 'model_identity_live_verified_before_grant': False,
        'source_review_protocol': str(here/'source-review-protocol.md'),
        'source_review_protocol_sha256': sha(here/'source-review-protocol.md')}
    c['tokenizer_path'] = str(project/'reports/workstream-c/concurrent-qualification-2026-11-06/tokenizer-metadata.json')
    c['tokenizer_sha256'] = sha(c['tokenizer_path'])
    assert c['tokenizer_sha256'] == 'fa1ba7031fa5853b7f1f766c35c2627b5e56235939d52c2694e5f8744ae71cf5'
    c['input_sha256'].update(prep['input_sha256'])
    for path in [*project.glob('config/**/*.py'), project/'scripts/_llama_token_count.py', Path(c['tokenizer_path']),
                 here/'run_case.py', here/'source-review-protocol.md', prior/'activated-full-offline-tests.txt',
                 prior/'landed-ready-tests.txt', prior/'prepared-development-data/preparation.json']:
        c['input_sha256'][str(path.resolve())] = sha(path)
    for case in c['cases'].values():
        corpus = Path(case['corpus_path']).resolve()
        c['input_sha256'][str(corpus)] = sha(corpus)
        plan = Plan.model_validate_json(json.dumps(case['plan']))
        assert sha(corpus) == plan.corpus_sha256
        # Admission/sidecar/deadline checks only. No model or safety invocation.
        prepare_composer(c, case, plan.model_copy(update={'deadline_seconds': 150.0}), None, None)
    c['pipeline_identity'] = hashlib.sha256(canonical({'runtime_inputs': runtime_inputs(),
        'model_snapshot': c['model_snapshot'], 'settings': c['settings'], 'composition_contract': c['composition_contract']}).encode()).hexdigest()
    c['pipeline_identity_method'] = 'canonical runtime inputs/model/settings/composition contract; per-case sidecars separately pinned'
    c['contract_sha256'] = hashlib.sha256(canonical(c).encode()).hexdigest()
    assert not Path(c['output_directory']).exists()
    with (here/'development-contract.json').open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(c, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'contract_sha256': c['contract_sha256'], 'pinned_files': len(c['input_sha256']),
        'execution_authorized': False, 'new_model_calls': 0}))


if __name__ == '__main__':
    main()
