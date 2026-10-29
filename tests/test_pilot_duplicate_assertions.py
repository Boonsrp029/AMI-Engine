"""Merge only identical validated assertions, never infer independent support."""
import pytest

from src.pilot import _composition as composition
from src.pilot._evidence import EvidenceMap


def mapping(quotes=None, count=2):
    quotes = quotes or ['Output was 7 GWh.'] * count
    return EvidenceMap.model_validate({'components': [{'component_id': 'r1', 'question_anchor': 'What was output?',
        'status': 'supported', 'short_answer': 'Output was 7 GWh.', 'evidence': [
            {'source_id': chr(97+i), 'quote': q} for i,q in enumerate(quotes)]}]})


def composed(value, text=None):
    return {'title': 'Brief', 'claims': [{'component_id': u['component_id'], 'unit_id': u['unit_id'],
        'text': text or u['evidence'][0]['quote']} for u in composition.canonical_units(value)]}


def test_identical_quotes_and_claims_keep_both_source_citations_once():
    value = mapping();trace = {}
    assert len(composition.canonical_units(value)) == 2  # No prevalidation aliasing.
    draft, fallback = composition.project(composed(value), value, 'What was output?', {}, trace)
    assert draft['claims'] == [{'text': 'Output was 7 GWh.', 'source_ids': ['a','b']}]
    assert not fallback
    assert trace['public_claim_coverage'][0]['unit_ids'] == ['u1','u2']
    assert trace['merged_duplicate_citations']


def test_same_summary_cannot_erase_distinct_selected_quotations():
    value = mapping(['Output was 7 GWh, with solar additions.', 'Output was 7 GWh, with wind additions.'])
    draft, _ = composition.project(composed(value,'Output was 7 GWh.'), value, 'What was output?', {})
    assert len(draft['claims']) == 2


def test_different_components_and_scope_are_not_cross_source_merged():
    value = mapping()
    other = value.components[0].model_copy(update={'component_id':'r2', 'question_anchor':'What was a different output?',
        'evidence':[value.components[0].evidence[1]]})
    first = value.components[0].model_copy(update={'evidence':[value.components[0].evidence[0]]})
    value = value.model_copy(update={'components':[first,other]})
    draft, _ = composition.project(composed(value), value, 'What was output?', {})
    assert len(draft['claims']) == 2


def test_later_origin_validation_still_fails_before_a_duplicate_can_hide_it(monkeypatch):
    value = mapping();original=composition.qualify_claim;seen=[]
    def validate(text, component, context):
        seen.append(component.component_id)
        if component.component_id=='u2':raise ValueError('Synthetic invalid second citation origin')
        return original(text,component,context)
    monkeypatch.setattr(composition,'qualify_claim',validate)
    with pytest.raises(ValueError,match='second citation origin'):
        composition.project(composed(value),value,'What was output?',{})
    assert seen==['u1','u2']


def test_citation_limit_is_never_met_by_dropping_a_source():
    value = mapping(count=5)
    context = {'components': {'r1': {'period':'May 2020'}}, 'fields': {'period': {'evidence': [
        {'component_id':'r1','source_id':'scope','quote':'May 2020'}]}}}
    draft, _ = composition.project(composed(value),value,'What was output?',context)
    assert all(len(c['source_ids'])<=5 for c in draft['claims'])
    assert {s for c in draft['claims'] for s in c['source_ids']} == {'a','b','c','d','e','scope'}
    assert len(draft['claims']) == 2


def test_fallback_deduplicates_only_after_validation_and_preserves_coverage():
    value = mapping();trace={}
    draft, fallback = composition.project({'title':'Brief','claims':[]},value,'What was output?',{},trace)
    assert fallback==['u1','u2'] and len(draft['claims'])==1
    assert draft['claims'][0]['source_ids']==['a','b']
    assert trace['public_claim_coverage'][0]['unit_ids']==['u1','u2']
