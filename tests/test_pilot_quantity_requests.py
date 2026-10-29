"""Quantity-slot contracts and numeric boundaries, not actual model-quality evidence."""
import copy
import json
from decimal import Decimal
from types import SimpleNamespace

from langchain_core.messages import AIMessage
from pydantic import ValidationError
import pytest

from src.pilot._choices import constrained_selection
from src.pilot._evidence import (EvidenceMap, EvidenceSelection, GeographySelection,
    build_span_catalog, evidence_gaps, resolve_selection)
from src.pilot._requests import requested_components, retrieval_facets
from src.pilot._scope import _numeric_values, validate_mapped_answers, validate_claim_measure_and_numbers
from src.pilot.engine import Corpus, PilotEngine


QUESTION = "What value and project count did Cedar report for 2019 applications, and how did each change from 2018?"


@pytest.mark.parametrize('text,expected', [
    ('USD33 Billion', {'33'}), ('usd33 billion.', {'33'}), ('THB1.14 trillion', {'1.14'}),
    ('USD1,234.50 million', {'1234.50'}), ('THB 1 234 million', {'1234'}),
    ('USD 33 billion, 144 projects, up 12%.', {'33', '144', '12'}),
])
def test_declared_currency_prefixes_and_literal_numbers(text, expected):
    assert _numeric_values(text) == {Decimal(n) for n in expected}


@pytest.mark.parametrize('text', ['record33', 'AUSD33', 'USD33foo', 'USD33_foo',
    'USD1.14alpha', 'record1.14', 'THB2x', 'model33.2x'])
def test_identifier_fragments_cannot_justify_numeric_answers(text):
    assert _numeric_values(text) == set()


def test_currency_spelling_equivalence_keeps_absent_value_and_unit_checks():
    raw = {'components': [{'component_id': 'r1', 'question_anchor': 'What value was reported?',
        'status': 'supported', 'short_answer': '33 billion USD',
        'evidence': [{'source_id': 's', 'quote': 'Application value was USD33 Billion.'}]}]}
    mapping = EvidenceMap.model_validate(raw)
    assert validate_mapped_answers(mapping, {})['r1']['status'] == 'passed_necessary_checks'
    validate_claim_measure_and_numbers('33 billion USD', mapping.components[0])
    mapping.components[0].short_answer = '34 billion USD'
    with pytest.raises(ValueError, match='Mapped answer'):
        validate_mapped_answers(mapping, {})
    with pytest.raises(ValueError, match='quantity value/unit'):
        validate_claim_measure_and_numbers('33 billion baht', mapping.components[0])


def test_value_count_and_each_change_have_four_private_classification_slots():
    slots = requested_components(QUESTION)
    assert [s['component_id'] for s in slots] == ['r1', 'r2', 'r3', 'r4']
    assert [(s['quantity_measure'], s['quantity_task']) for s in slots] == [
        ('value', 'level'), ('count', 'level'), ('value', 'change'), ('count', 'change')]
    assert all(s['question_anchor'] in QUESTION for s in slots)
    assert all('Another measure' in s['instruction'] for s in slots)


def test_retrieval_keeps_original_clauses_and_facet_order():
    facets = retrieval_facets(QUESTION)
    assert [f['query'] for f in facets] == [QUESTION.split(', and ')[0], 'how did each change from 2018?']
    assert [f['component_id'] for f in facets] == ['r1', 'r2']
    assert [f['covers_components'] for f in facets] == [['r1', 'r2'], ['r3', 'r4']]


@pytest.mark.parametrize('question', [
    'What value and project count were reported?',
    'What were the value and number of projects in Cedar?',
])
def test_level_only_request_does_not_invent_changes(question):
    slots = requested_components(question)
    assert len(slots) == 2 and all(s['quantity_task'] == 'level' for s in slots)
    assert len(retrieval_facets(question)) == 1


@pytest.mark.parametrize('question', [
    'What changed in demand and generation?',
    'What value and project count were reported, and why were they revised?',
    'What does "what value and project count" mean?',
    'What is (what value and project count) intended to mean?',
    'What value and project count were reported, which source led, and how did each change?',
])
def test_unrecognized_or_quoted_pairs_keep_existing_clause_behavior(question):
    assert all('quantity_measure' not in s for s in requested_components(question))


def selections():
    sources = {'s': {'content': 'Applications had value USD2.7 Billion, up 12%. Project count increased 20% to 144 projects.'}}
    catalog = build_span_catalog(sources)
    ids = list(catalog)
    answers = ['2.7 billion USD', '144 projects', '12% value growth', '20% count growth']
    raw = {'components': [{'component_id': f'r{i+1}', 'status': 'supported', 'short_answer': answer,
                          'evidence': [ids[0 if i in (0, 2) else 1]]}
                         for i, answer in enumerate(answers)],
           'geography': {'status': 'unresolved', 'value': '', 'evidence': [], 'reason': 'No location.'}}
    return sources, catalog, raw


@pytest.mark.parametrize('kind', ['omitted_count', 'old_two_slots', 'duplicate', 'invented', 'other_measure_span'])
def test_quantity_classification_does_not_silently_complete_or_reassign(kind):
    sources, catalog, raw = selections()
    if kind == 'omitted_count':
        raw['components'].pop(1)
    elif kind == 'old_two_slots':
        raw['components'] = raw['components'][:2]
    elif kind == 'duplicate':
        raw['components'][1]['component_id'] = 'r1'
    elif kind == 'invented':
        raw['components'][1]['component_id'] = 'r5'
    else:
        raw['components'][2]['evidence'] = raw['components'][1]['evidence'][:]
    before = copy.deepcopy(raw)
    with pytest.raises(ValueError):
        mapping = resolve_selection(raw, catalog, QUESTION, sources, '2026-10-28')
        validate_mapped_answers(mapping, {})
    assert raw == before


def test_decoder_schema_requires_all_four_ordered_slots():
    sources, catalog, raw = selections()
    schema = constrained_selection(EvidenceSelection, GeographySelection, {'labels': []},
                                   requested_components(QUESTION), [], {})
    schema.model_validate(raw)
    raw['components'] = raw['components'][:2]
    with pytest.raises(ValidationError):
        schema.model_validate(raw)


def test_missing_changes_remain_distinguishable_with_shared_question_anchor():
    sources, catalog, raw = selections()
    for component in raw['components'][2:]:
        component.update(status='missing', short_answer='', evidence=[])
    mapping = resolve_selection(raw, catalog, QUESTION, sources, '2026-10-28')
    gaps = evidence_gaps(mapping, QUESTION)
    assert len(gaps) == 2
    assert 'change in value' in gaps[0] and 'change in project count' in gaps[1]
    assert all('how did each change from 2018?' in gap for gap in gaps)


@pytest.mark.parametrize('state', ['missing', 'conflicting', 'partial'])
def test_unresolved_states_preserve_other_supported_quantities(state):
    sources, catalog, raw = selections()
    component = raw['components'][2]
    if state == 'missing':
        component.update(status=state, short_answer='', evidence=[])
    elif state == 'conflicting':
        sources['other'] = {'content': 'Application value increased 18%.'}
        catalog = build_span_catalog(sources)
        other = next(s for s, v in catalog.items() if v['source_id'] == 'other')
        component.update(status=state, short_answer='', evidence=component['evidence'] + [other])
    else:
        component.update(status=state, gap_anchor='how did each change from 2018?')
    mapping = resolve_selection(raw, catalog, QUESTION, sources, '2026-10-28')
    assert len(mapping.components) == 4 and mapping.components[1].short_answer == '144 projects'
    checks = validate_mapped_answers(mapping, {})
    assert checks['r3']['status'] == ('passed_necessary_checks' if state == 'partial' else 'not_applicable')
    assert any('change in value' in gap for gap in evidence_gaps(mapping, QUESTION))


@pytest.mark.parametrize('mode', ['valid', 'wrong_span', 'guard_rejected', 'partial_changes'])
def test_four_slot_engine_preserves_budget_final_guard_and_public_draft(tmp_path, mode):
    rows = [{'feed_id': 's', 'clean_content': selections()[0]['s']['content'], 'source': 'https://example.invalid/data'}]
    path = tmp_path / 'corpus.json'
    path.write_text(json.dumps(rows), encoding='utf-8')
    calls = iter([AIMessage(content='', tool_calls=[{'name': 'search_sources',
        'args': {'query': 'application value project count', 'limit': 3}, 'id': 'one'}]), AIMessage(content='done')])
    guards, compositions, events = [], [], []
    def structured(schema, **_):
        def invoke(messages):
            payload = json.loads(messages[1].content)
            if issubclass(schema, EvidenceSelection):
                assert len(payload['requests']) == 4
                sources, catalog, raw = selections()
                if mode == 'wrong_span':
                    raw['components'][2]['evidence'] = raw['components'][1]['evidence'][:]
                if mode == 'partial_changes':
                    for c in raw['components'][2:]:
                        c.update(status='partial', gap_anchor='how did each change from 2018?')
            else:
                compositions.append(payload)
                raw = {'title': 'Analyst research brief', 'claims': [{'component_id': u['component_id'],
                    'unit_id': u['unit_id'], 'text': u['evidence'][0]['quote']} for u in payload['units']]}
            return {'parsed': schema.model_validate(raw), 'raw': AIMessage(content='Fixed synthetic response')}
        return SimpleNamespace(invoke=invoke)
    model = SimpleNamespace(bind_tools=lambda _: SimpleNamespace(invoke=lambda _: next(calls)),
                            with_structured_output=structured)
    def guard(**kwargs):
        guards.append(kwargs)
        return {'passed_guardrails': mode != 'guard_rejected'}
    run = lambda: PilotEngine(Corpus(path), model, SimpleNamespace(validate_output=guard)).run(
        QUESTION, lambda k, v: events.append((k, v)))
    if mode == 'wrong_span':
        with pytest.raises(ValueError, match='Mapped answer'):
            run()
        assert not compositions and not guards
        assert sum(k == 'model_request_started' for k, _ in events) == 3
    else:
        if mode == 'guard_rejected':
            with pytest.raises(ValueError, match='guardrails'):
                run()
        else:
            result = run()
            assert result['metrics']['model_calls'] == 4
            assert len(result['draft']['claims']) == 2
            assert all(x in ' '.join(c['text'] for c in result['draft']['claims']) for x in ['USD2.7', '12%', '20%', '144'])
            if mode == 'partial_changes':
                gaps = [w for w in result['draft']['warnings'] if 'requested clause:' in w]
                assert len(gaps) == 2
                assert 'change in value' in gaps[0] and 'change in project count' in gaps[1]
        assert len(compositions) == len(guards) == 1
