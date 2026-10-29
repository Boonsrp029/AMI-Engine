"""Offline uniqueness/date-range contracts; no decoder/model-quality evidence."""
import pytest
from pydantic import ValidationError

from src.pilot._choices import constrained_selection, period_choices
from src.pilot._evidence import EvidenceSelection, GeographySelection


def value(ids):
    return {'components': [{'component_id': 'r1', 'status': 'supported', 'short_answer': 'Six capacity units and nine sites.',
                            'evidence': ids}],
            'geography': {'status': 'unresolved', 'value': '', 'evidence': [], 'reason': 'No selected place.'}}


def constrained():
    return constrained_selection(EvidenceSelection, GeographySelection, {'labels': []},
        [{'component_id': 'r1', 'question_anchor': 'What capacity and site count were recorded?'}], [],
        {'r1': [{'span_ids': ['a'], 'extra_span_ids': ['a', 'b'], 'allow_extra': True}]})


@pytest.mark.parametrize('schema', [EvidenceSelection, constrained()])
def test_duplicate_ids_fail_parsing_without_silent_correction(schema):
    with pytest.raises(ValidationError, match='distinct'):
        schema.model_validate(value(['a', 'b', 'a']))
    parsed = schema.model_validate(value(['a', 'b']))
    assert list(parsed.components[0].evidence) == ['a', 'b']


@pytest.mark.parametrize('schema', [EvidenceSelection, constrained()])
def test_generated_schema_declares_unique_items(schema):
    spec = schema.model_json_schema()
    selections = [v['properties']['evidence'] for v in spec['$defs'].values()
                  if 'component_id' in v.get('properties', {})]
    assert selections and all(s.get('uniqueItems') is True for s in selections)


def test_same_evidence_can_support_distinct_requested_components():
    raw = value(['a'])
    raw['components'].append({**raw['components'][0], 'component_id': 'r2'})
    assert len(EvidenceSelection.model_validate(raw).components) == 2


@pytest.mark.parametrize('status,ids,answer', [('missing', [], ''), ('conflicting', ['a', 'b'], '')])
def test_explicit_unresolved_states_keep_their_selection_shape(status, ids, answer):
    raw = value(ids)
    raw['components'][0].update(status=status, short_answer=answer)
    assert EvidenceSelection.model_validate(raw).components[0].status == status


@pytest.mark.parametrize('text', [
    'Applications from January to December 2018 reached nine projects.',
    'Applications from January through December 2018 reached nine projects.',
    'Applications from January–December 2018 reached nine projects.',
    'Applications from March 2017 to December 2018 reached nine projects.',
    'Applications from March 2017 — December 2018 reached nine projects.',
    'Applications from January\n to December 2018 reached nine projects.',
])
def test_range_endpoints_do_not_become_monthly_measurement_choices(text):
    assert period_choices({'s': {'text': text}}, 'How many applications were recorded in 2018?') == []


def test_explicit_monthly_question_is_not_answered_by_annual_range():
    assert period_choices({'s': {'text': 'Applications from January to December 2018 reached nine projects.'}},
                          'What was output in December 2018?') == []


def test_independent_same_month_observation_remains_available_after_a_range():
    text = ('Applications from January to December 2018 reached nine projects. '
            'Output in December 2018 reached six units.')
    assert period_choices({'s': {'text': text}}, 'What was output in December 2018?') == [
        {'value': 'December 2018', 'span_ids': ['s']}]


def test_unrelated_standalone_monthly_observations_keep_existing_choices():
    assert [p['value'] for p in period_choices({'s': {'text': 'Output in May 2018 and April 2017 was reported.'}},
                                               'Compare 2018 with 2017.')] == ['May 2018', 'April 2017']
