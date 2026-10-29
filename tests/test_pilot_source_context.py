"""Frozen synthetic provenance contracts; no model-quality claims."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.messages import AIMessage

from src.pilot._evidence import EvidenceMap, EvidenceSelection
from src.pilot._report_context import collect_context
from src.pilot._scope import resolve_scope
from src.pilot._source_context import context_sources, assess_mapping, reject_incompatible, EvidenceContextMismatch
from src.pilot.engine import Corpus, PilotEngine


FIXTURES = {c['id']: c for c in json.loads(
    (Path(__file__).parent/'fixtures/source_context_v1.json').read_text(encoding='utf-8'))['fixtures']}


def prepare(tmp_path, case, *, text=None, question=None):
    case = copy.deepcopy(FIXTURES[case])
    if text is not None:
        case['selected'] = text
    query = question or case['question']
    rows = [{'feed_id': f'SYNTHETIC_SCOPE:unit:{i}:0', 'doc_name': 'SYNTHETIC_SCOPE',
             'source': 'https://example.invalid/scope', 'published': '2020-07-31', 'clean_content': t}
            for i, t in enumerate([case['header'], case.get('section', 'Summary'), case.get('selected', case.get('monthly_selected'))])]
    path = tmp_path/'corpus.json'
    path.write_text(json.dumps(rows), encoding='utf-8')
    corpus = Corpus(path)
    source = corpus.sources['SYNTHETIC_SCOPE:unit:2:0']
    mapping = EvidenceMap.model_validate({'components': [{'component_id': 'r1', 'question_anchor': query,
        'status': 'supported', 'short_answer': source['content'],
        'evidence': [{'source_id': source['source_id'], 'quote': source['content']}]}]})
    retrieved = {source['source_id']: source}
    contexts = context_sources(retrieved, corpus.sources)
    return query, corpus, mapping, retrieved, contexts


@pytest.mark.parametrize('case,reason', [
    ('wrong_report_month', 'incompatible_reporting_month'),
    ('quarter_for_month', 'quarterly_evidence_for_monthly_request'),
    ('forecast_not_outcome', 'forecast_for_observed_request'),
])
def test_frozen_incompatible_cases_fail_explicitly(tmp_path, case, reason):
    query, _, mapping, _, contexts = prepare(tmp_path, case)
    checks = assess_mapping(mapping, query, contexts)
    assert checks['r1']['status'] == 'incompatible'
    assert reason in checks['r1']['reason_codes']
    with pytest.raises(EvidenceContextMismatch):
        reject_incompatible(checks)


def test_matching_month_retains_bounded_evidence_and_scope(tmp_path):
    query, corpus, mapping, retrieved, contexts = prepare(tmp_path, 'matching_month')
    checks = assess_mapping(mapping, query, contexts)
    assert checks['r1']['status'] == 'compatible'
    reject_incompatible(checks)
    added, bindings, _ = collect_context(mapping, query, retrieved, corpus.sources)
    _, scope = resolve_scope(mapping, query, {**retrieved, **added}, reporting_bindings=bindings)
    assert scope['components']['r1']['period'] == 'May 2020'


def test_explicit_historical_comparison_survives_newer_report(tmp_path):
    query, _, mapping, _, contexts = prepare(tmp_path, 'explicit_historical_observation')
    checks = assess_mapping(mapping, query, contexts)
    assert checks['r1']['status'] == 'compatible'
    assert 'explicit_requested_period' in checks['r1']['reason_codes']
    reject_incompatible(checks)


def test_publication_only_is_unknown_not_incompatible_or_measurement_proof(tmp_path):
    query, corpus, mapping, retrieved, contexts = prepare(tmp_path, 'publication_only')
    checks = assess_mapping(mapping, query, contexts)
    assert checks['r1']['status'] == 'unknown'
    reject_incompatible(checks)
    _, scope = resolve_scope(mapping, query, retrieved)
    assert not scope['fields']
    assert contexts[next(iter(retrieved))]['report_period'] == ''


def test_monthly_and_quarterly_components_keep_distinct_scope(tmp_path):
    query, corpus, mapping, retrieved, _ = prepare(tmp_path, 'mixed_period_question')
    row = next(iter(retrieved.values()))
    extra = {**row, 'source_id': 'SYNTHETIC_SCOPE:unit:3:0', 'content': FIXTURES['mixed_period_question']['quarterly_selected']}
    corpus.sources[extra['source_id']] = extra
    retrieved[extra['source_id']] = extra
    first = mapping.components[0].model_copy(update={'question_anchor': 'May 2020 monthly factory orders'})
    second = first.model_copy(update={'component_id': 'r2', 'question_anchor': 'second-quarter orders',
        'short_answer': extra['content'], 'evidence': [first.evidence[0].model_copy(update={
            'source_id': extra['source_id'], 'quote': extra['content']})]})
    mapping = mapping.model_copy(update={'components': [first, second]})
    checks = assess_mapping(mapping, query, context_sources(retrieved, corpus.sources))
    assert checks['r1']['status'] == checks['r2']['status'] == 'compatible'
    assert checks['r1']['requested_periods'] == ['May 2020']
    assert checks['r2']['requested_periods'] == []


def test_report_heading_alone_cannot_assign_scope_without_section_binding(tmp_path):
    query, corpus, mapping, retrieved, _ = prepare(tmp_path, 'matching_month')
    retrieved['SYNTHETIC_SCOPE:unit:0:0'] = corpus.sources['SYNTHETIC_SCOPE:unit:0:0']
    _, scope = resolve_scope(mapping, query, retrieved)
    assert not scope['fields'] and not scope['components']
    assert scope['unresolved_requested_periods'] == ['May 2020']


def test_relative_monthly_summary_has_conflicting_report_provenance(tmp_path):
    query, corpus, mapping, retrieved, _ = prepare(tmp_path, 'wrong_report_month')
    corpus.sources['SYNTHETIC_SCOPE:unit:1:0']['content'] = 'Summary'
    checks = assess_mapping(mapping, query, context_sources(retrieved, corpus.sources))
    assert checks['r1']['status'] == 'incompatible'


def test_tampered_retrieved_source_does_not_become_unknown_scope(tmp_path):
    _, corpus, _, retrieved, _ = prepare(tmp_path, 'matching_month')
    changed = copy.deepcopy(retrieved)
    next(iter(changed.values()))['content'] = 'Changed source content.'
    with pytest.raises(ValueError, match='pinned source'):
        context_sources(changed, corpus.sources)


def test_unknown_record_formats_remain_unknown_and_do_not_infer_from_names():
    source = {'source_id': 'REPORT_MAY2020:pdf:0', 'doc_name': 'REPORT_MAY2020',
              'page_num': 0, 'published': '2020-06-01', 'content': 'Factory orders increased.'}
    contexts = context_sources({source['source_id']: source}, {source['source_id']: source})
    assert contexts[source['source_id']]['report_period'] == ''


def test_monthly_report_cannot_establish_a_specific_day(tmp_path):
    query, _, mapping, _, contexts = prepare(tmp_path, 'matching_month',
                                            question='What happened on 2020-05-14?')
    checks = assess_mapping(mapping, query, contexts)
    assert checks['r1']['status'] == 'unknown'
    assert checks['r1']['reason_codes'] == ['report_month_does_not_establish_requested_day']


def test_forecast_component_is_not_rejected_due_to_a_separate_observation_request(tmp_path):
    query = 'What was forecast for May 2020, and what was observed in May 2020?'
    _, _, mapping, _, contexts = prepare(tmp_path, 'forecast_not_outcome', question=query)
    component = mapping.components[0].model_copy(update={'question_anchor': 'What was forecast for May 2020'})
    mapping = mapping.model_copy(update={'components': [component]})
    assert assess_mapping(mapping, query, contexts)['r1']['status'] == 'compatible'


def test_invalid_heading_or_foreign_document_does_not_supply_period_proof(tmp_path):
    query, corpus, mapping, retrieved, _ = prepare(tmp_path, 'wrong_report_month')
    corpus.sources['SYNTHETIC_SCOPE:unit:0:0']['url'] = 'https://example.invalid/foreign'
    contexts = context_sources(retrieved, corpus.sources)
    assert contexts[next(iter(retrieved))]['report_period'] == ''
    assert assess_mapping(mapping, query, contexts)['r1']['status'] == 'unknown'


@pytest.mark.parametrize('case,success', [('matching_month', True), ('wrong_report_month', False)])
def test_runtime_offers_context_and_checks_mapping_before_composition(tmp_path, monkeypatch, case, success):
    query, corpus, _, _, _ = prepare(tmp_path, case)
    # Isolate the post-retrieval boundary: later ranking may omit this record,
    # but a supplied incompatible pinned source must still fail before drafting.
    source = corpus.sources['SYNTHETIC_SCOPE:unit:2:0']
    monkeypatch.setattr(corpus, 'search_evidence', lambda *args, **kwargs: ([source], {'policy': 'fixed test source'}))
    calls, guards, events = [], [], []
    class Model:
        def bind_tools(self, tools):
            def invoke(messages):
                calls.append('tool')
                return (AIMessage(content='', tool_calls=[{'name': 'search_sources', 'args': {
                    'query': 'factory orders', 'limit': 1}, 'id': 't1'}]) if calls.count('tool') == 1
                        else AIMessage(content='Ready'))
            return SimpleNamespace(invoke=invoke)
        def with_structured_output(self, schema, **kwargs):
            def invoke(messages):
                if issubclass(schema, EvidenceSelection):
                    calls.append('mapping')
                    record = json.loads(messages[1].content)['evidence'][0]
                    assert record['reporting_context']['report_period'] == ('May 2020' if success else 'June 2020')
                    assert record['reporting_context']['section_kind'] == 'monthly'
                    value = {'components': [{'component_id': 'r1', 'status': 'supported',
                        'short_answer': 'Factory orders increased.', 'evidence': [record['spans'][0]['span_id']]}],
                        'geography': {'status': 'unresolved', 'value': '', 'evidence': [], 'reason': 'No location.'}}
                else:
                    calls.append('composition')
                    value = {'title': 'Analyst research brief', 'claims': []}
                return {'parsed': schema.model_validate(value), 'raw': AIMessage(content='Fixed test response')}
            return SimpleNamespace(invoke=invoke)
    guard = SimpleNamespace(validate_output=lambda **kwargs: guards.append(kwargs) or {'passed_guardrails': True})
    run = lambda: PilotEngine(corpus, Model(), guard).run(query, lambda k, v: events.append((k, v)))
    if success:
        result = run()
        assert len(calls) == result['metrics']['model_calls'] == 4 and len(guards) == 1
        assert result['draft']['claims'][0]['text'].startswith('May 2020: ')
    else:
        with pytest.raises(EvidenceContextMismatch):
            run()
        assert calls == ['tool', 'tool', 'mapping'] and not guards
    checks = next(v for k, v in events if k == 'mapped_source_context')
    assert checks['r1']['status'] == ('compatible' if success else 'incompatible')
