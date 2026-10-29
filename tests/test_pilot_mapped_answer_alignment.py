"""Necessary evidence alignment gates; no semantic-support or model-quality claim."""
import json

import pytest

from src.pilot._evidence import EvidenceMap, build_span_catalog
from src.pilot._scope import validate_mapped_answers, resolve_scope
from src.pilot._report_context import collect_context
from src.pilot._topics import topic_views, focused_choices
from src.pilot.engine import Corpus


def mapping(answer, quote, status='supported'):
    return EvidenceMap.model_validate({'components': [{'component_id': 'r1',
        'question_anchor': 'What value was reported?', 'status': status, 'short_answer': answer,
        'evidence': [{'source_id': 's', 'quote': quote}] if quote else []}]})


@pytest.mark.parametrize('subject', ['investment', 'consumption', 'inflation'])
def test_bare_financial_word_does_not_force_institutional_header(subject):
    sources = {'header': {'content': subject.upper() + ' SERVICES OFFICE. 12 Example Road.'},
               'facts': {'content': subject.title() + ' totaled 2.5 billion credits.'}}
    assert topic_views(build_span_catalog(sources), sources,
        [{'component_id': 'r1', 'question_anchor': f'What was the reported value of {subject}?'}]) == {}


def test_shared_focus_helper_keeps_generic_body_available_to_other_view_paths():
    sources = {'s': {'content': 'INVESTMENT SERVICES OFFICE. Investment applications totaled 2.5 billion credits.'}}
    catalog = build_span_catalog(sources)
    ids = list(catalog)
    groups, extras, trace = focused_choices(catalog, sources, 'investment applications', ids, ids)
    assert groups == [ids] and extras == ids
    assert not trace['applied'] and not trace['primary_source_ids'] and not trace['absence_established']


@pytest.mark.parametrize('subject', ['private investment', 'public investment', 'headline inflation', 'core inflation'])
def test_explicit_financial_subject_views_remain_available(subject):
    sources = {'s': {'content': subject.title() + ' increased because demand recovered.'}}
    views = topic_views(build_span_catalog(sources), sources,
        [{'component_id': 'r1', 'question_anchor': f'Why did {subject} increase?'}])
    assert views['r1'][0]['span_ids']


@pytest.mark.parametrize('answer,quote', [
    ('2.5 billion credits', 'INVESTMENT SERVICES OFFICE, 12 Example Road.'),
    ('35% growth', 'Applications grew 40%; FDI grew 25% and represented 73%.'),
    ('220 projects', 'The agency lists 200 contact offices.'),
])
def test_numeric_mapped_answer_requires_its_selected_evidence(answer, quote):
    with pytest.raises(ValueError, match='Mapped answer'):
        validate_mapped_answers(mapping(answer, quote), {})


def test_selected_value_count_and_growth_pass_without_using_other_sources():
    quote = 'Applications reached 2.5 billion credits, up 15%; project count rose 10% to 220.'
    checks = validate_mapped_answers(mapping('2.5 billion credits and 220 projects, up 15% and 10%.', quote), {})
    assert checks['r1']['status'] == 'passed_necessary_checks'
    assert checks['r1']['semantic_support_proven'] is False


def test_number_in_another_component_does_not_justify_an_unlinked_answer():
    first = mapping('35%', 'Applications grew 40%.')
    second = mapping('35%', 'A different measure grew 35%.').components[0].model_copy(update={'component_id': 'r2'})
    first.components.append(second)
    with pytest.raises(ValueError, match='Mapped answer'):
        validate_mapped_answers(first, {})


def test_qualitative_partial_information_needs_no_invented_numeric_requirement():
    checks = validate_mapped_answers(mapping('Private investment increased.', 'Private investment increased.', 'partial'), {})
    assert checks['r1']['status'] == 'passed_necessary_checks'


@pytest.mark.parametrize('status,quote', [('missing', ''), ('conflicting', 'Some sources disagree.')])
def test_unresolved_states_do_not_gain_a_factual_answer(status, quote):
    checks = validate_mapped_answers(mapping('', quote, status), {})
    assert checks['r1']['status'] == 'not_applicable'


def test_reporting_period_must_be_established_before_answer_year_is_exempted(tmp_path):
    question = 'How did private investment change in June 2019?'
    quote = 'Private investment increased by 5%.'
    rows = [{'feed_id': f'ALIGNMENT:unit:{i}:0', 'doc_name': 'ALIGNMENT',
        'source': 'https://example.invalid/alignment', 'published': '2019-07-01', 'clean_content': text}
        for i, text in enumerate(['Economic Conditions for June 2019',
            'Details of the economic conditions for June relative to the previous month are as follows:', quote])]
    path = tmp_path / 'corpus.json'
    path.write_text(json.dumps(rows), encoding='utf-8')
    corpus = Corpus(path)
    mapped = mapping('Private investment increased by 5% in June 2019.', quote)
    mapped.components[0].question_anchor = question
    mapped.components[0].evidence[0].source_id = 'ALIGNMENT:unit:2:0'
    with pytest.raises(ValueError, match='Mapped answer'):
        validate_mapped_answers(mapped, {})
    retrieved = {'ALIGNMENT:unit:2:0': corpus.sources['ALIGNMENT:unit:2:0']}
    added, bindings, _ = collect_context(mapped, question, retrieved, corpus.sources)
    mapped, context = resolve_scope(mapped, question, {**retrieved, **added}, bindings)
    assert validate_mapped_answers(mapped, context)['r1']['status'] == 'passed_necessary_checks'


def test_numeric_compatibility_does_not_claim_to_prove_relevance():
    checks = validate_mapped_answers(mapping('12 projects', 'The contact office is at 12 Example Road.'), {})
    assert not checks['r1']['semantic_support_proven']


def test_one_requests_measure_does_not_override_another_components_question():
    first = mapping('Electricity demand was 20 GWh.', 'Electricity demand was 20 GWh.')
    first.components[0].question_anchor = 'What was electricity demand?'
    second = mapping('Total energy consumption was 30 PJ.', 'Total energy consumption was 30 PJ.').components[0]
    first.components.append(second.model_copy(update={'component_id': 'r2', 'question_anchor': 'What was total energy consumption?'}))
    checks = validate_mapped_answers(first, {})
    assert all(c['status'] == 'passed_necessary_checks' for c in checks.values())


@pytest.mark.parametrize('mode', ['invalid_mapping', 'valid', 'guard_rejected'])
def test_engine_checks_mapping_before_composition_and_keeps_final_guardrail(tmp_path, mode):
    from types import SimpleNamespace
    from langchain_core.messages import AIMessage
    from src.pilot._evidence import EvidenceSelection
    from src.pilot.engine import PilotEngine
    rows = [{'feed_id': 'header', 'source': 'https://example.invalid/header',
             'clean_content': 'INVESTMENT SERVICES OFFICE. 12 Example Road.'},
            {'feed_id': 'fact', 'source': 'https://example.invalid/fact',
             'clean_content': 'Investment applications in 2019 had a value of 2.5 billion credits.'}]
    path = tmp_path / 'corpus.json'
    path.write_text(json.dumps(rows), encoding='utf-8')
    tools = iter([AIMessage(content='', tool_calls=[{'name': 'search_sources',
        'args': {'query': 'investment applications value', 'limit': 3}, 'id': 'one'}]), AIMessage(content='done')])
    composed, guards, events = [], [], []
    def structured(schema, **_):
        def invoke(messages):
            payload = json.loads(messages[1].content)
            if issubclass(schema, EvidenceSelection):
                assert payload['request_evidence_views'] == {}
                sid = next(span['span_id'] for source in payload['evidence']
                           if source['source_id'] == ('header' if mode == 'invalid_mapping' else 'fact')
                           for span in source['spans'])
                raw = {'components': [{'component_id': 'r1', 'status': 'supported',
                    'short_answer': '2.5 billion credits', 'evidence': [sid]}],
                    'geography': {'status': 'unresolved', 'value': '', 'evidence': [], 'reason': 'No location.'}}
            else:
                composed.append(payload)
                raw = {'title': 'Analyst research brief', 'claims': [
                    {'component_id': unit['component_id'], 'unit_id': unit['unit_id'], 'text': unit['evidence'][0]['quote']}
                    for unit in payload['units']]}
            return {'parsed': schema.model_validate(raw), 'raw': AIMessage(content='fixed synthetic response')}
        return SimpleNamespace(invoke=invoke)
    model = SimpleNamespace(bind_tools=lambda _: SimpleNamespace(invoke=lambda _: next(tools)),
                            with_structured_output=structured)
    def guard(**kwargs):
        guards.append(kwargs)
        return {'passed_guardrails': mode != 'guard_rejected'}
    run = lambda: PilotEngine(Corpus(path), model, SimpleNamespace(validate_output=guard)).run(
        'What value was reported for investment applications?', lambda k, v: events.append((k, v)))
    if mode == 'invalid_mapping':
        with pytest.raises(ValueError, match='Mapped answer'):
            run()
        assert not composed and not guards
        assert sum(k == 'model_request_started' for k, _ in events) == 3
    else:
        if mode == 'guard_rejected':
            with pytest.raises(ValueError, match='guardrails'):
                run()
        else:
            result = run()
            assert result['metrics']['model_calls'] == 4 and '2.5 billion credits' in result['draft']['claims'][0]['text']
        assert len(composed) == len(guards) == 1
        assert any(k == 'mapped_answer_alignment' for k, _ in events)
