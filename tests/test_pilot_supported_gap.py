"""Synthetic supported/partial gap contract; no inference or source judgments."""
import pytest
from pydantic import ValidationError

from src.pilot._choices import constrained_selection
from src.pilot._evidence import EvidenceSelection, EvidenceSelectionComponent, GeographySelection


def schema():
    return constrained_selection(EvidenceSelection, GeographySelection, {'labels': []},
        [{'component_id': 'r1', 'question_anchor': 'output and staffing'}])


def value(status='supported', gap=''):
    return {'components': [{'component_id': 'r1', 'status': status,
        'short_answer': 'Output stayed unchanged.' if status in {'supported', 'partial'} else '',
        'evidence': ['synthetic_span'] if status in {'supported', 'partial'} else [], 'gap_anchor': gap}],
        'geography': {'status': 'unresolved', 'value': '', 'evidence': [], 'reason': 'No place stated.'}, 'period': ''}


@pytest.mark.parametrize('gap', ['output', 'declined in the period', ' '])
def test_supported_component_rejects_even_a_valid_question_fragment_as_gap(gap):
    with pytest.raises(ValidationError):
        EvidenceSelectionComponent.model_validate(value(gap=gap)['components'][0])
    with pytest.raises(ValidationError):
        schema().model_validate(value(gap=gap))


def test_supported_schema_exposes_empty_gap_constant_and_keeps_answer():
    model = schema()
    definitions = model.model_json_schema()['$defs']
    assert definitions['SupportedRequestSlot0']['properties']['gap_anchor']['const'] == ''
    parsed = model.model_validate(value())
    assert parsed.components[0].short_answer == 'Output stayed unchanged.'


@pytest.mark.parametrize('status', ['partial', 'missing', 'conflicting'])
def test_unresolved_state_preserves_granular_gap_for_later_exact_question_validation(status):
    parsed = schema().model_validate(value(status, 'staffing'))
    assert parsed.components[0].gap_anchor == 'staffing'


def test_lower_level_mapping_cannot_bypass_supported_gap_rule():
    from src.pilot._evidence import validate_mapping
    component = {**value(gap='staffing')['components'][0], 'question_anchor': 'output and staffing',
        'evidence': [{'source_id': 's1', 'quote': 'Output stayed unchanged.'}]}
    with pytest.raises(ValueError, match='Supported evidence cannot contain a gap anchor'):
        validate_mapping({'components': [component]}, 'output and staffing',
                         {'s1': {'content': 'Output stayed unchanged.'}}, '2026-10-31')
