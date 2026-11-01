"""Exact-source span contracts, without model generation or semantic judging."""
import hashlib

import pytest

from src.pilot._evidence import build_span_catalog
from src.pilot._source_selection import resolve_source_selection, WIRE_VERSION


def spans(text):
    return build_span_catalog({'s': {'content': text}})


@pytest.mark.parametrize('abbreviation', ['ca.', 'approx.', 'e.g.', 'i.e.', 'CA.'])
def test_financial_abbreviation_retains_its_continuation(abbreviation):
    text = f'Applications reached 2.4 billion baht ({abbreviation} USD 70 million), led by computing. Count increased.'
    values = list(spans(text).values())
    assert [v['text'] for v in values] == [text.split(' Count')[0], 'Count increased.']


@pytest.mark.parametrize('ending', ['.', ';', '!', '?'])
def test_ordinary_punctuation_still_separates_statements(ending):
    assert [s['text'] for s in spans(f'Value increased{ending} Count fell.').values()] == [
        f'Value increased{ending}', 'Count fell.']


def test_abbreviation_cannot_bridge_a_paragraph():
    assert [s['text'] for s in spans('Value was approx.\n \nCount fell.').values()] == [
        'Value was approx.', 'Count fell.']


def test_unknown_abbreviation_does_not_imply_a_continuation():
    assert [s['text'] for s in spans('Class was abc. Count fell.').values()] == ['Class was abc.', 'Count fell.']


@pytest.mark.parametrize('text', [
    ' \tมูลค่า was 2.4 billion baht (ca. USD 70 million).\nCount was 80 projects.  ',
    'Value was approx. ' + 'long financial context ' * 70 + '2.4 billion baht.',
    'λ' * 1250,
])
def test_exact_offsets_bounds_ids_and_nonwhitespace_coverage(text):
    catalog = spans(text)
    assert catalog == spans(text)
    covered = []
    for sid, span in catalog.items():
        assert 0 < len(span['text']) <= 600
        assert text[span['start']:span['end']] == span['text']
        assert span['content_sha256'] == hashlib.sha256(text.encode()).hexdigest()
        identity = f"s\0{span['content_sha256']}\0{span['start']}\0{span['end']}"
        assert sid == 's_' + hashlib.sha256(identity.encode()).hexdigest()[:16]
        covered.extend(range(span['start'], span['end']))
    assert len(covered) == len(set(covered))
    assert {i for i, c in enumerate(text) if not c.isspace()} <= set(covered)


def test_resolved_application_extract_retains_full_currency_sentence():
    text = 'Applications reached 2.4 billion baht (ca. USD 70 million), led by computing.'
    catalog = spans(text)
    raw = {'wire_version': WIRE_VERSION, 'components': [{'component_id': 'r1',
        'status': 'supported', 'evidence': list(catalog), 'gap_anchor': ''}],
        'geography': {'status': 'unresolved', 'value': '', 'evidence': [], 'reason': 'No location.'}}
    mapping, provenance = resolve_source_selection(raw, catalog, 'What was application value?',
        {'s': {'content': text}}, '2026-11-01')
    assert mapping.components[0].short_answer == text
    assert provenance[0]['text'] == text


def test_duplicate_text_in_distinct_records_keeps_distinct_identity():
    text = 'Value was approx. USD 70 million.'
    catalog = build_span_catalog({'a': {'content': text}, 'b': {'content': text}})
    assert len(catalog) == 2
    assert {s['source_id'] for s in catalog.values()} == {'a', 'b'}
