"""Offline decoder/request contracts, not evidence of real-model quality."""
import json

import httpx
import pytest
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from pydantic import ValidationError

from src.pilot._choices import constrained_selection
from src.pilot._evidence import (
    EvidenceSelection, EvidenceSelectionComponent, GeographySelection, MAPPING_INSTRUCTION,
)


def schema():
    return constrained_selection(EvidenceSelection, GeographySelection, {'labels': []},
        [{'component_id': 'r1', 'question_anchor': 'output'}], request_views={
            'r1': [{'span_ids': ['fixture-output'], 'allow_extra': False}]})


def value():
    return {'components': [{'component_id': 'r1', 'status': 'supported',
        'evidence': ['fixture-output'], 'short_answer': 'Output rose as staffing increased.'}],
        'geography': {'status': 'unresolved', 'value': '', 'evidence': [], 'reason': 'No place stated.'}}


def assert_evidence_first(definition):
    keys = list(definition['properties'])
    assert keys.index('evidence') < keys.index('short_answer')
    assert {'evidence', 'short_answer'} <= set(definition['required'])


def test_evidence_precedes_answer_in_base_and_both_dynamic_status_branches():
    assert_evidence_first(EvidenceSelectionComponent.model_json_schema())
    definitions = schema().model_json_schema()['$defs']
    for name in ('SupportedRequestSlot0', 'UnresolvedRequestSlot0'):
        assert_evidence_first(definitions[name])


@pytest.mark.parametrize('field', ['evidence', 'short_answer'])
def test_reordering_does_not_make_required_values_optional(field):
    raw = value()
    del raw['components'][0][field]
    with pytest.raises(ValidationError):
        schema().model_validate(raw)


def test_examples_parse_and_supported_examples_demonstrate_complete_answers():
    examples = [json.loads(line) for line in MAPPING_INSTRUCTION.splitlines() if line.startswith('{')]
    assert len(examples) == 3
    for example in examples:
        EvidenceSelection.model_validate(example)
        for component in example['components']:
            if component['status'] == 'supported':
                assert component['short_answer'].endswith('.')
                assert len(component['short_answer'].split()) > 5
                assert list(component).index('evidence') < list(component).index('short_answer')
    comparison = examples[-1]['components']
    assert len(comparison) == 2
    assert all('because' in component['short_answer'] for component in comparison)


def test_installed_sdk_sends_evidence_first_schema_and_keeps_selected_answer(monkeypatch):
    monkeypatch.delenv('OLLAMA_API_KEY', raising=False)
    requests = []

    def handler(request):
        assert request.url.path == '/api/chat'
        requests.append(json.loads(request.content))
        frame = {'model': 'fixture', 'message': {'role': 'assistant', 'content': json.dumps(value())},
            'done': True, 'done_reason': 'stop', 'prompt_eval_count': 5, 'eval_count': 5}
        return httpx.Response(200, content=json.dumps(frame) + '\n',
            headers={'Content-Type': 'application/x-ndjson'})

    model = ChatOllama(model='fixture', temperature=0, num_ctx=4096, num_predict=900,
        client_kwargs={'transport': httpx.MockTransport(handler), 'trust_env': False})
    result = model.with_structured_output(schema(), include_raw=True).invoke([HumanMessage(content='fixture')])
    assert len(requests) == 1
    for name in ('SupportedRequestSlot0', 'UnresolvedRequestSlot0'):
        assert_evidence_first(requests[0]['format']['$defs'][name])
    assert result['parsed'].components[0].short_answer == value()['components'][0]['short_answer']
    assert result['parsed'].components[0].evidence == ('fixture-output',)
