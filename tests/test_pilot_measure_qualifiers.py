"""Necessary literal measure qualifiers; these are not semantic quality scores."""
import pytest

from src.pilot._composition import project
from src.pilot._evidence import EvidenceMap


def mapping(quote):
    return EvidenceMap.model_validate({'components': [{'component_id': cid, 'question_anchor': 'What changed?',
        'status': 'supported', 'short_answer': quote, 'evidence': [{'source_id': 'a', 'quote': quote}]}
        for cid in ('r1', 'r2')]})


@pytest.mark.parametrize('quote,text,label', [
    ('Revenue increased after seasonal adjustment.', 'Revenue increased.', 'seasonally_adjusted'),
    ('Revenue increased after seasonal adjustment.', 'Non-seasonally adjusted revenue increased.', 'seasonally_adjusted'),
    ('Unadjusted orders declined.', 'Seasonally adjusted orders declined.', 'unadjusted'),
    ('Unadjusted orders declined.', 'Orders were not unadjusted and declined.', 'unadjusted'),
    ('Exports excluding gold declined.', 'Exports declined.', 'gold_excluded'),
    ('Exports excluding gold declined.', 'Exports including gold declined.', 'gold_excluded'),
])
def test_qualifier_loss_uses_exact_source_for_all_origins(quote, text, label):
    trace = {}
    draft, fallback = project({'title': 'Brief', 'claims': [{'unit_id': 'u1', 'component_id': 'r1', 'text': text}]},
                              mapping(quote), 'What changed?', {}, trace)
    assert fallback == ['u1', 'u2'] and len(draft['claims']) == 1
    assert draft['claims'][0]['text'] == quote
    assert trace['omitted_measure_qualifiers'] == {'u1': [label], 'u2': [label]}
    assert set(trace['fallback_reasons'].values()) == {'source_measure_qualifier_absent'}


@pytest.mark.parametrize('quote,text', [
    ('Revenue increased after seasonal adjustment.', 'Seasonally adjusted revenue increased.'),
    ('Exports excluding gold declined.', 'Exports declined with gold excluded.'),
    ('Non-seasonally adjusted orders declined.', 'Unadjusted orders declined.'),
])
def test_explicit_equivalent_qualifier_is_retained_without_fallback(quote, text):
    draft, fallback = project({'title': 'Brief', 'claims': [{'unit_id': 'u1', 'component_id': 'r1', 'text': text}]},
                              mapping(quote), 'What changed?', {})
    assert not fallback and draft['claims'][0]['text'] == text


def test_omitted_unit_still_reports_omission_instead_of_inventing_model_qualifier_error():
    trace = {}
    _, fallback = project({'title': 'Brief', 'claims': []}, mapping('Seasonally adjusted orders declined.'), 'What changed?', {}, trace)
    assert fallback == ['u1', 'u2'] and trace['omitted_measure_qualifiers'] == {}
    assert set(trace['fallback_reasons'].values()) == {'unit_omitted'}
