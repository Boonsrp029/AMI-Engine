"""Reconstruct a rejected safety input with saved responses and a fixed judge."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
from langchain_core.language_models.fake import FakeListLLM
from nemoguardrails.integrations.langchain.llm_adapter import LangChainLLMAdapter
from pydantic import Field
from scripts._llama_token_count import encoding
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.runner import ModelAccess
from src.utils import guardrails_runner as module


class RecordingJudge(FakeListLLM):
    prompts: list[str] = Field(default_factory=list)

    async def _acall(self, prompt, **kwargs):
        self.prompts.append(prompt)
        return await super()._acall(prompt, **kwargs)


def main():
    contract = json.loads((ROOT / 'development-contract.json').read_text())
    output = ROOT / 'actual-development-v1'
    def digest(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    assert all(digest(path) == sha for path, sha in contract['input_sha256'].items())
    frozen = contract['cases']['cq1-a48']
    plan = Plan.model_validate_json(json.dumps(frozen['plan']))
    saved = {stage: json.loads((output / f'cq1-a48.{stage}.raw.json').read_text())
             for stage in ('mapping', 'composition')}
    requests = []
    def replay(stage, schema, instruction, inputs):
        requests.append({'stage': stage, 'instruction': instruction, 'inputs': inputs,
                         'raw_response_sha256': digest(output / f'cq1-a48.{stage}.raw.json')})
        return {'raw': saved[stage]['raw'], 'parsed': schema.model_validate(json.loads(saved[stage]['raw'])).model_dump()}
    report = run_plan(plan, 'a' * 32, 'b' * 32, LocalBM25Adapter(frozen['corpus_path']))
    result = prepare_composer(contract, frozen, plan, replay, None)(report, ModelAccess(time.monotonic() + 60))
    sources = {entry.source.source_id: entry.source.model_dump() for entry in report.sources}
    context = '\n'.join(source['content'] for source in sources.values())
    safety = json.loads((output / 'cq1-a48.safety.json').read_text())
    assert hashlib.sha256(context.encode()).hexdigest() == safety['context_sha256']
    claim = '\n'.join(row['text'] for row in result.draft['claims'])
    assert claim == safety['raw_output']
    judge = RecordingJudge(responses=['NO'])
    real_rails = module.LLMRails
    with patch.dict(os.environ, {'AGENT_LLM_PROVIDER': 'ollama', 'AGENT_LLM_MODEL': contract['model_snapshot']['model']}):
        with patch.object(module, 'LLMRails', lambda config: real_rails(config, llm=LangChainLLMAdapter(judge))):
            guard = module.GuardrailsRunner()
            fixed = guard.validate_output(claim, context, plan.query)
    assert len(judge.prompts) == 1 and fixed['passed_guardrails'] is False
    prompt = judge.prompts[0]
    quote = requests[-1]['inputs']['units'][0]['evidence'][0]['quote']
    assert quote in context and quote in prompt and claim in prompt
    counter = encoding(json.loads(Path(contract['tokenizer_path']).read_bytes()))
    record = {'contract_sha256': contract['contract_sha256'], 'case_id': 'cq1-a48',
        'actual_model_calls_in_diagnosis': 0, 'real_nemo_calls_in_diagnosis': 0, 'fixed_judge_calls': 1,
        'context_hash_matches_actual_safety_record': True,
        'supporting_quote_present_in_full_context': True,
        'supporting_quote_present_in_reconstructed_judge_prompt': True,
        'context_characters': len(context), 'reconstructed_prompt_tokens': len(counter.encode(prompt)),
        'context_limit': 4096, 'fact_check_completion_limit': 32,
        'prompt_status': 'offline reconstruction; not captured HTTP traffic',
        'draft_from_actual_model_fields': result.draft, 'raw_composer_fields': json.loads(saved['composition']['raw']),
        'application_rendering': result.diagnostics['application_rendered_memberships'],
        'requests': requests, 'full_context': context, 'reconstructed_judge_prompt': prompt,
        'actual_fact_verdicts': safety['raw_fact_verdicts'],
        'harness_note': 'Internal Windows event-loop socket pairs allowed; all other connects blocked. Initial blanket blocking rejected an internal pipe.',
        'assessment': 'Supporting evidence is available. The actual NO verdict has no retained rationale. No application clipping defect established.'}
    with (ROOT / 'actual-safety-input-trace.json').open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(record, indent=2) + '\n')
    print(json.dumps({key: record[key] for key in ('context_hash_matches_actual_safety_record',
        'supporting_quote_present_in_reconstructed_judge_prompt', 'reconstructed_prompt_tokens',
        'actual_fact_verdicts', 'actual_model_calls_in_diagnosis')}))


if __name__ == '__main__':
    original_pair, original_connect = socket.socketpair, socket.socket.connect
    internal = threading.local()
    def socket_pair(*args, **kwargs):
        internal.creating_pair = True
        try:
            return original_pair(*args, **kwargs)
        finally:
            internal.creating_pair = False
    def connect(sock, address):
        if getattr(internal, 'creating_pair', False) and address[0] in {'127.0.0.1', '::1'}:
            return original_connect(sock, address)
        raise AssertionError('Offline diagnosis forbids model-network connections')
    previous = asyncio.get_event_loop_policy()
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        with patch.object(socket, 'socketpair', socket_pair), patch.object(socket.socket, 'connect', connect):
            main()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        asyncio.set_event_loop_policy(previous)
