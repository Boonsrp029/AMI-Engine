"""Offline input contracts only; these tests do not measure model quality."""
import copy

from src.pilot._composition import payload, project
from src.pilot._evidence import COMPOSITION_INSTRUCTION, EvidenceMap, composition_payload
from src.pilot._requests import requested_components


QUESTION = ('What value and project count did Alder report for 2022 applications, '
            'and how did each change from 2021?')
VALUE = ('Applications in 2022 increased 10% in value to 3.3 billion baht '
         '(ca. USD 99 million).')
BASELINE = 'The total adjusted investment value of applications for 2021 was 3 billion baht.'
COUNT = ('The number of applications for 2022 increased 20% to 180 projects, '
         'from 150 projects in 2021.')


def mapping():
    return EvidenceMap.model_validate({'components': [
        {'component_id': r['component_id'], 'question_anchor': r['question_anchor'],
         'status': 'supported', 'short_answer': 'Not used as synthesis evidence.',
         'evidence': [{'source_id': f's{i}', 'quote': q} for i, q in enumerate(
             [VALUE, BASELINE] if r['quantity_measure'] == 'value' else [COUNT])]}
        for r in requested_components(QUESTION)]})


def test_input_exposes_current_baseline_change_and_keeps_measures_separate():
    m = mapping()
    before = copy.deepcopy(m.model_dump())
    result = composition_payload(m, '2026-11-02', question=QUESTION)
    assert len(result['units']) == 2  # identical evidence is composed only once
    value, count = [u['required_literal_coverage'] for u in result['units']]
    assert value == {'quantity_pairs': [('baht', '3000000000'), ('baht', '3300000000.0'),
                                      ('usd', '99000000')],
                     'percentages': ['10'], 'years': ['2021', '2022']}
    assert count == {'quantity_pairs': [('project', '150'), ('project', '180')],
                     'percentages': ['20'], 'years': ['2021', '2022']}
    assert m.model_dump() == before
    assert 'growth percentage alone is not a substitute' in COMPOSITION_INSTRUCTION


def test_unrecognized_request_or_legacy_call_does_not_invent_requirements():
    m = mapping()
    for question in ('', 'What was revenue in 2022?', QUESTION.replace('2022', '2035')):
        result = payload(m, '2026-11-02', question=question)
        if question != QUESTION.replace('2022', '2035'):
            assert all('required_literal_coverage' not in u for u in result['units'])
        # A requested but unquoted year is never a required fact.
        assert all('2035' not in u.get('required_literal_coverage', {}).get('years', [])
                   for u in result['units'])


def test_absent_baseline_is_not_manufactured():
    m = mapping()
    for c in m.components:
        c.evidence = [e for e in c.evidence if e.quote != BASELINE]
    result = payload(m, '2026-11-02', question=QUESTION)
    value = result['units'][0]['required_literal_coverage']
    assert ('baht', '3000000000') not in value['quantity_pairs']
    assert value['years'] == ['2022']


def test_old_lossy_response_still_triggers_logged_fallback_not_acceptance():
    m = mapping()
    draft, fallbacks = project({'title': 'Analyst research brief', 'claims': [
        {'unit_id': 'u1', 'component_id': 'r1',
         'text': 'Applications increased 10% to USD 99 million in 2022.'},
        {'unit_id': 'u2', 'component_id': 'r2', 'text': COUNT}]},
        m, QUESTION, {})
    assert fallbacks
    assert BASELINE in draft['claims'][0]['text']
    assert '3.3 billion baht' in draft['claims'][0]['text']
