"""Compare frozen request content only. No inference, tuning, or quality claim."""
import hashlib
import json
from pathlib import Path
import socket
import time

from scripts._llama_token_count import encoding
from scripts._mapper_transport import sha
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks._disclosures import DisclosureScopes, bindings_hash
from src.pilot.subtasks._scoped_generation import ScopedConcurrentComposer
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess


def main():
    def blocked(*args, **kwargs):
        raise AssertionError('Offline comparison cannot access a service')
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = socket.getaddrinfo = blocked
    root = Path('reports/workstream-c/concurrent-qualification-2026-11-06')
    output = Path(__file__).resolve().parent
    old = json.loads((root/'question-span-2026-11-07/mapper-input.json').read_text())
    proposal = json.loads((root/'question-span-2026-11-07/mapper-preflight-proposal.json').read_text())
    plan = Plan.model_validate_json(json.dumps(proposal['plan']))
    bindings = proposal['bindings']
    labels = ['wind generation in Denmark in 2015', 'Denmark retail electricity prices yesterday']
    declarations = [{'component_id': 'r1', 'subtask_id': f's0{i}', 'question_span': {
        'start': plan.query.index(label), 'end': plan.query.index(label)+len(label)}} for i, label in enumerate(labels, 1)]
    scope = DisclosureScopes.model_validate_json(json.dumps({'plan_id': plan.plan_id,
        'corpus_sha256': plan.corpus_sha256, 'question_sha256': hashlib.sha256(plan.query.encode()).hexdigest(),
        'bindings_sha256': bindings_hash(bindings), 'declaration_ref': 'Offline consumed-case caller declaration; no owner acceptance',
        'annotations': declarations}))
    report = run_plan(plan, 'a'*32, 'b'*32, LocalBM25Adapter(proposal['corpus_path']))
    captured = {}
    class Captured(Exception):
        pass
    def capture(stage, schema, instruction, inputs):
        assert stage == 'mapping' and not captured
        captured.update(schema=schema.model_json_schema(), messages=[{'type': 'system', 'content': instruction},
            {'type': 'human', 'content': json.dumps(inputs, ensure_ascii=False, separators=(',', ':'))}])
        raise Captured()
    access = ModelAccess(time.monotonic()+30)
    try:
        ScopedConcurrentComposer(plan, bindings, proposal['as_of'], capture, scope,
            complete_required_branches=proposal['complete_required_branches'])(report, access)
    except Captured:
        pass
    assert access.calls == 1 and access.guards == 0
    metadata = root/'tokenizer-metadata.json'
    assert sha(metadata) == 'fa1ba7031fa5853b7f1f766c35c2627b5e56235939d52c2694e5f8744ae71cf5'
    counter = encoding(json.loads(metadata.read_text()))
    def count(value):
        tokens = sum(len(counter.encode(m['content'])) for m in value['messages'])
        return {'message_content_tokens': tokens, 'framing_reservation': 256, 'completion_reservation': 900,
            'conservative_total': tokens+1156, 'limit': 4096,
            'schema_format_tokens_separate': len(counter.encode(json.dumps(value['schema'])))}
    before, after = count(old), count(captured)
    result = {'purpose': 'Offline payload comparison on consumed cq-p02; wire semantics changed, not a quality A/B test',
        'before': before, 'after': after, 'message_content_reduction': before['message_content_tokens']-after['message_content_tokens'],
        'old_input_sha256': sha(root/'question-span-2026-11-07/mapper-input.json'),
        'tokenizer_sha256': sha(metadata), 'actual_model_calls': 0, 'server_observed_after_tokens': None,
        'model_quality': 'unverified', 'Codex_context_savings': 'not measured; this compares AMI mapper payloads',
        'runtime_activation': 'pending A handoff; existing caller remains unchanged'}
    for name, data in [('offline-scoped-mapper-input.json', captured), ('offline-scoped-request-declaration.json', scope.model_dump(mode='json')),
                       ('offline-context-comparison.json', result)]:
        with (output/name).open('x', encoding='utf-8') as handle:
            handle.write(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
