"""Compose identical evidence once; validate each origin. No semantic judge."""
from pydantic import ValidationError
import pytest

from src.pilot import _composition as composition
from src.pilot._evidence import EvidenceMap


def mapping():
    return EvidenceMap.model_validate({'components': [{'component_id': cid, 'question_anchor': anchor,
        'status': 'supported', 'short_answer': 'Orders unchanged; costs fell.', 'evidence': [
            {'source_id': 'a', 'quote': 'Orders were unchanged.'},
            {'source_id': 'b', 'quote': 'Costs fell because warehouses expanded.'}]}
        for cid, anchor in [('r1', 'What changed?'), ('r2', 'Why did costs fall?')]]})


def test_shared_evidence_enters_composer_once_and_covers_both_requests():
    value = mapping()
    before = value.model_dump()
    units = composition.canonical_units(value)
    assert len(composition.composition_units(value)) == 4 and len(units) == 2
    assert [u['origins'] for u in units] == [
        [{'unit_id': 'u1', 'component_id': 'r1'}, {'unit_id': 'u3', 'component_id': 'r2'}],
        [{'unit_id': 'u2', 'component_id': 'r1'}, {'unit_id': 'u4', 'component_id': 'r2'}]]
    raw = {'title': 'Analyst research brief', 'claims': [{'unit_id': u['unit_id'], 'component_id': u['component_id'],
        'text': u['evidence'][0]['quote']} for u in units]}
    composition.response_schema(value).model_validate(raw)
    trace = {}
    draft, fallback = composition.project(raw, value, 'What changed? Why did costs fall?', {}, trace)
    assert len(draft['claims']) == 2 and not fallback
    assert trace['public_claim_coverage'][0]['unit_ids'] == ['u1', 'u3']
    payload = composition.payload(value, '2026-10-27')
    assert len(payload['units']) == 2 and 'identity_sha256' not in str(payload)
    assert value.model_dump() == before


def test_omitted_canonical_units_fall_back_for_every_origin():
    trace = {}
    draft, fallback = composition.project({'title': 'Brief', 'claims': []}, mapping(), 'What changed?', {}, trace)
    assert fallback == ['u1', 'u2', 'u3', 'u4'] and len(draft['claims']) == 2
    assert [g['component_ids'] for g in trace['public_claim_coverage']] == [['r1', 'r2'], ['r1', 'r2']]


def test_alias_replies_fail_in_schema_and_projection_without_repair():
    value = mapping()
    raw = {'title': 'Analyst research brief', 'claims': [{'component_id': 'r2', 'unit_id': 'u3', 'text': 'Orders unchanged.'}]}
    with pytest.raises(ValidationError):
        composition.response_schema(value).model_validate(raw)
    with pytest.raises(ValueError, match='unknown or mismatched'):
        composition.project(raw, value, 'What changed?', {})


def test_every_origin_is_validated_even_when_composed_body_is_shared(monkeypatch):
    value = mapping()
    seen = []
    original = composition.qualify_claim
    def reject_later(text, component, context):
        seen.append(component.component_id)
        if component.component_id == 'u3':
            raise ValueError('Synthetic later-origin validation failure')
        return original(text, component, context)
    monkeypatch.setattr(composition, 'qualify_claim', reject_later)
    raw = {'title': 'Brief', 'claims': [{'unit_id': u['unit_id'], 'component_id': u['component_id'],
        'text': u['evidence'][0]['quote']} for u in composition.canonical_units(value)]}
    with pytest.raises(ValueError, match='later-origin'):
        composition.project(raw, value, 'What changed?', {})
    assert seen == ['u1', 'u2', 'u3']


def test_different_established_scope_or_citation_proofs_do_not_share_units():
    value = mapping()
    context = {'components': {'r1': {'period': 'May 2012'}}, 'fields': {'period': {'evidence': [
        {'component_id': 'r1', 'source_id': 'scope-a'}]}}}
    assert len(composition.canonical_units(value, context)) == 4
    context['components']['r2'] = {'period': 'May 2012'}
    context['fields']['period']['evidence'].append({'component_id': 'r2', 'source_id': 'scope-b'})
    assert len(composition.canonical_units(value, context)) == 4
    context['fields']['period']['evidence'][1]['source_id'] = 'scope-a'
    assert len(composition.canonical_units(value, context)) == 2
    assert len(composition.payload(value, '2026-10-27', context)['units']) == 2
    context['fields']['period']['evidence'].clear()
    with pytest.raises(ValueError, match='lacks citation evidence'):
        composition.canonical_units(value, context)
