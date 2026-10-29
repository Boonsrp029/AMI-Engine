"""Synthetic comparison coverage, frozen before implementation; no inference."""
from types import SimpleNamespace

import pytest

from src.pilot._comparison_evidence import comparison_views, assess_comparisons, reject_incomplete_comparisons
from src.pilot._evidence import build_span_catalog
from src.pilot._requests import requested_components


QUESTION = ('How did private investment compare month-on-month in May 2020 and quarter-on-quarter '
            'in the second quarter, and which categories explain those directions?')


def fixture():
    sources = {'m': {'content': 'Private investment increased because machinery purchases rose.'},
               'q': {'content': 'Private investment declined because construction fell.'},
               'd': {'content': 'Public investment declined.'}}
    contexts = {sid: {'source_id': sid, 'report_period': 'May 2020',
        'section_kind': 'monthly' if sid == 'm' else 'quarterly', 'section_period': 'May 2020' if sid == 'm' else '',
        'quarter': '' if sid == 'm' else 'second', 'proof': [], 'relative_month': sid == 'm'} for sid in sources}
    return sources, contexts


def mapping(sources, ids, status='supported'):
    return SimpleNamespace(components=[SimpleNamespace(component_id=r['component_id'],question_anchor=r['question_anchor'],
        status=status, evidence=[SimpleNamespace(source_id=sid,quote=sources[sid]['content'])
            for sid in (ids.get(r['component_id'],[]) if isinstance(ids,dict) else ids)]) for r in requested_components(QUESTION)])


def test_predeclared_two_period_views_require_both_relevant_sides():
    sources, contexts = fixture()
    catalog = build_span_catalog(sources)
    views = comparison_views(QUESTION, catalog, sources, contexts)
    assert [views[cid][0]['role'] for cid in ['r1','r2']] == ['monthly_requested_comparison','quarterly_requested_comparison']
    assert [[catalog[s]['source_id'] for s in views[cid][0]['span_ids']] for cid in ['r1','r2']] == [['m'],['q']]


@pytest.mark.parametrize('ids', [['m'], ['q']])
def test_fully_supported_comparison_cannot_select_only_one_established_side(ids):
    sources, contexts = fixture()
    checks = assess_comparisons(mapping(sources, ids), QUESTION, sources, contexts)
    assert any(c['status']=='incompatible' for c in checks.values())
    with pytest.raises(ValueError, match='comparison'):
        reject_incomplete_comparisons(checks)


def test_complete_selection_and_explicit_partial_answers_remain_valid():
    sources, contexts = fixture()
    value=mapping(sources,{'r1':['m'],'r2':['q']})
    assert all(c['status']=='compatible' for c in assess_comparisons(value,QUESTION,sources,contexts).values())
    value=mapping(sources,{'r1':['m'],'r2':[]});value.components[1].status='missing'
    assert set(assess_comparisons(value,QUESTION,sources,contexts))=={'r1'}


def test_unknown_provenance_does_not_create_a_false_comparison_failure():
    sources, contexts = fixture()
    contexts['m'].update(section_kind='unknown', section_period='', report_period='', relative_month=False)
    check = assess_comparisons(mapping(sources, ['m']), QUESTION, sources, contexts)['r1']
    assert check['status'] == 'unknown'
    reject_incomplete_comparisons({'r1': check})
    assert set(comparison_views(QUESTION, build_span_catalog(sources), sources, contexts)) == {'r2'}


def test_unknown_comparison_grammar_has_no_new_contract_or_forced_views():
    sources, contexts = fixture()
    assert comparison_views('Compare investment across periods.', build_span_catalog(sources), sources, contexts) == {}
    assert assess_comparisons(mapping(sources, ['m']), 'Compare investment across periods.', sources, contexts) == {}


def test_a_known_wrong_subject_cannot_satisfy_period_coverage():
    sources, contexts = fixture()
    sources['q']['content'] = 'Private consumption declined.'
    checks = assess_comparisons(mapping(sources, {'r1':['m'],'r2':['q']}), QUESTION, sources, contexts)
    assert checks['r2']['status'] == 'incompatible'
    assert set(comparison_views(QUESTION, build_span_catalog(sources), sources, contexts)) == {'r1'}
