"""Preparation data only: no grant, executable contract, service or inference."""
import hashlib
import json
from pathlib import Path
import socket
import time

from scripts._mapper_transport import sha, request_body
from scripts._llama_token_count import encoding
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks._disclosures import DisclosureScopes, bindings_hash
from src.pilot.subtasks._scoped_activation import prepare_composer, CONTRACT_VERSION
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.runner import ModelAccess


def main():
    def blocked(*args, **kwargs):
        raise AssertionError('Offline preparation cannot contact services')
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = socket.getaddrinfo = blocked
    here = Path(__file__).resolve().parent
    out = here/'prepared-development-data'
    out.mkdir(exist_ok=False)
    root = Path('reports/workstream-c/concurrent-qualification-2026-11-06')
    old = json.loads((root/'title-lineage-2026-11-07/development-contract-v7.json').read_text())
    tokenizer = root/'tokenizer-metadata.json'
    assert sha(tokenizer) == old['tokenizer_sha256']
    counter = encoding(json.loads(tokenizer.read_text()))
    labels = {'cq-p01': ['observed electricity demand in Canada in 2016', 'projected electricity demand in Japan through 2036'],
              'cq-p02': ['wind generation in Denmark in 2015', 'Denmark retail electricity prices yesterday']}
    result = {'status': 'prepared data; A activation and combined validation pending; not an execution contract',
        'composition_contract': CONTRACT_VERSION, 'as_of': old['as_of'], 'model_snapshot': old['model_snapshot'],
        'settings': old['settings'], 'cases': {}, 'input_sha256': {}, 'actual_model_calls': 0,
        'execution_authorized': False, 'budget_proposal': {'main_calls_total': 8, 'nemo_invocations_total': 2,
            'seconds_per_case': 180, 'retries': 0, 'warmups': 0},
        'stop_policy': 'cq-p01 once; cq-p02 only after all first-case gates pass; stop on first failure; no CQ1 authorization',
        'scope_authorship': 'caller-declared preparation annotations, membership checked; not model-produced or owner-adjudicated'}
    for cid, texts in labels.items():
        frozen = dict(old['cases'][cid])
        plan = Plan.model_validate_json(json.dumps(frozen['plan']))
        assert sha(Path(frozen['corpus_path'])) == plan.corpus_sha256
        scope = DisclosureScopes.model_validate_json(json.dumps({'plan_id': plan.plan_id,
            'corpus_sha256': plan.corpus_sha256, 'question_sha256': hashlib.sha256(plan.query.encode()).hexdigest(),
            'bindings_sha256': bindings_hash(frozen['bindings']),
            'declaration_ref': 'C prepared development question labels; not owner acceptance',
            'annotations': [{'component_id': 'r1', 'subtask_id': f's0{i}', 'question_span': {
                'start': plan.query.index(text), 'end': plan.query.index(text)+len(text)}} for i, text in enumerate(texts, 1)]}))
        sidecar = (out/f'{cid}.scopes.json').resolve()
        sidecar.write_text(scope.model_dump_json(indent=2)+'\n', encoding='utf-8')
        frozen.update(requested_scopes=str(sidecar), requested_scopes_sha256=sha(sidecar))
        result['input_sha256'][str(sidecar)] = sha(sidecar)
        captured = {}
        class Captured(Exception):
            pass
        def capture(stage, schema, instruction, inputs):
            assert stage == 'mapping' and not captured
            captured.update(schema=schema.model_json_schema(), messages=[{'type': 'system', 'content': instruction},
                {'type': 'human', 'content': json.dumps(inputs, ensure_ascii=False, separators=(',', ':'))}])
            raise Captured()
        runtime = plan.model_copy(update={'deadline_seconds': 150.0})
        report = run_plan(runtime, 'a'*32, 'b'*32, LocalBM25Adapter(frozen['corpus_path']))
        access = ModelAccess(time.monotonic()+30)
        try:
            prepare_composer(result, frozen, runtime, capture, None)(report, access)
        except Captured:
            pass
        assert captured and access.calls == 1 and access.guards == 0
        body = request_body(captured)
        content = sum(len(counter.encode(m['content'])) for m in captured['messages'])
        assert content+1156 <= 4096
        for suffix, value in [('mapper-input', captured), ('native-body', body)]:
            path = out/f'{cid}.{suffix}.json'
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
            result['input_sha256'][str(path.resolve())] = sha(path)
        result['cases'][cid] = {'frozen_case': frozen, 'declared_scope_labels': texts,
            'offline_runtime_cap_for_binding_check': 150, 'message_content_tokens': content,
            'conservative_budget': content+1156, 'grammar_tokens_separate': len(counter.encode(json.dumps(captured['schema']))),
            'current_model_identity_live_verified': False, 'actual_generation': False}
    result['remaining'] = ['A applies/reviews activation patch', 'Combined source/admission checks',
        'Final runtime/config/scope pins and source-review protocol in executable contract', 'New direct generation grant']
    (out/'preparation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({cid: {'budget': c['conservative_budget'], 'scope_labels': c['declared_scope_labels']}
        for cid, c in result['cases'].items()}))


if __name__ == '__main__':
    main()
