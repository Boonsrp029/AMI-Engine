"""Frozen numeric-role regressions; exact source identity is not entailment."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.pilot._quantities import UnsupportedQuantityRole, validate_quantity_roles, percentage_evidence, percentage_views
from src.pilot._evidence import EvidenceMap, project_draft


CASES = {c['id']: c for c in json.loads((Path(__file__).parent/'fixtures/evidence_coverage_v1.json').read_text(encoding='utf-8'))['fixtures']}


def component(quote, anchor='What was reported?'):
    return SimpleNamespace(question_anchor=anchor, evidence=[SimpleNamespace(quote=quote)])


@pytest.mark.parametrize('case', ['percentage_role_not_numeric_set', 'different_denominator', 'wrong_quantity_unit'])
def test_frozen_incorrect_numeric_assignments_fail(case):
    c = CASES[case]
    with pytest.raises(UnsupportedQuantityRole):
        validate_quantity_roles(c['candidate'], component(c['source'], c['question']), c['question'])


def test_source_currency_equivalent_is_valid_without_a_new_exchange_rate():
    c = CASES['source_currency_equivalent']
    validate_quantity_roles(c['candidate'], component(c['source'], c['question']), c['question'])


def test_share_and_growth_can_both_be_retained_with_correct_roles():
    c = CASES['percentage_role_not_numeric_set']
    validate_quantity_roles('FDI represented 68% of total application value in 2021, after increasing 19%.',
                            component(c['source'], c['question']), c['question'])
    validate_quantity_roles('FDI grew 19% from the previous year.', component(c['source']))


def test_qualitative_answers_do_not_require_unrequested_numbers():
    c = CASES['qualitative_supported_answer']
    validate_quantity_roles(c['candidate'], component(c['source'], c['question']), c['question'])


@pytest.mark.parametrize('text', ['There were 210 projects.', 'Investment was 41.6 billion baht.'])
def test_correct_project_and_money_pairs_remain_valid(text):
    validate_quantity_roles(text, component('There were 210 projects worth 41.6 billion baht.'))


@pytest.mark.parametrize('text', ['There were 41.6 projects.', 'Investment was 210 billion baht.', 'Output was 210 TWh.'])
def test_cross_unit_numeric_token_reuse_is_not_support(text):
    with pytest.raises(UnsupportedQuantityRole):
        validate_quantity_roles(text, component('There were 210 projects worth 41.6 billion baht.'))


def test_source_ratio_denominator_cannot_be_replaced_with_another_total():
    evidence = component('Renewables provided 83% of the increase in electricity generation.')
    with pytest.raises(UnsupportedQuantityRole):
        validate_quantity_roles('Renewables provided 83% of total electricity generation.', evidence)


def test_plain_years_and_unknown_units_are_outside_the_narrow_unit_pair_parser():
    validate_quantity_roles('In 2021 orders increased.', component('In 2021 orders increased.'))
    validate_quantity_roles('There were 7 widgets.', component('There were 7 widgets.'))


def test_signed_quantities_and_thousands_separators_are_preserved():
    validate_quantity_roles('Output changed by -0.2 TWh.', component('Output changed by -0.2 TWh.'))
    with pytest.raises(UnsupportedQuantityRole):
        validate_quantity_roles('Output changed by 0.2 TWh.', component('Output changed by -0.2 TWh.'))
    validate_quantity_roles('There were 3,137 projects.', component('There were 3 137 projects.'))


@pytest.mark.parametrize('case', ['percentage_role_not_numeric_set', 'different_denominator', 'wrong_quantity_unit'])
def test_public_projection_rejects_known_role_mismatch_without_retry_or_abstention(case):
    c = CASES[case]
    mapping = EvidenceMap.model_validate({'components': [{'component_id': 'r1', 'question_anchor': c['question'],
        'status': 'supported', 'short_answer': c['candidate'], 'evidence': [{'source_id': 's', 'quote': c['source']}]}]})
    with pytest.raises(UnsupportedQuantityRole):
        project_draft({'title': 'Brief', 'claims': [{'component_id': 'r1', 'text': c['candidate']}]}, mapping, c['question'])


def test_public_projection_retains_currency_equivalent_and_existing_schema():
    c = CASES['source_currency_equivalent']
    mapping = EvidenceMap.model_validate({'components': [{'component_id': 'r1', 'question_anchor': c['question'],
        'status': 'supported', 'short_answer': c['candidate'], 'evidence': [{'source_id': 's', 'quote': c['source']}]}]})
    result, _ = project_draft({'title': 'Brief', 'claims': [{'component_id': 'r1', 'text': c['candidate']}]}, mapping, c['question'])
    assert result == {'title': 'Brief', 'claims': [{'text': c['candidate'], 'source_ids': ['s']}], 'warnings': []}


def test_bare_percentage_cannot_hide_a_known_denominator_mismatch():
    c = CASES['different_denominator']
    evidence = component(c['source'], c['question'])
    assert percentage_evidence(evidence)['status'] == 'incompatible'
    with pytest.raises(UnsupportedQuantityRole):
        validate_quantity_roles('35%.', evidence, c['question'])


def test_missing_literal_ratio_information_stays_unknown_not_fabricated_absence():
    evidence = component('The foreign share was described as substantial.', 'What share of application value was FDI?')
    assert percentage_evidence(evidence)['status'] == 'unknown'


def test_percentage_views_prefer_the_available_explicit_requested_role():
    from src.pilot._evidence import build_span_catalog
    question = 'What share of application value was FDI in 2021?'
    sources = {'correct': {'content': CASES['percentage_role_not_numeric_set']['source']},
               'other': {'content': CASES['different_denominator']['source']}}
    catalog = build_span_catalog(sources)
    requests = [{'component_id': 'r1', 'question_anchor': question}]
    views = percentage_views(catalog, requests)
    assert set(views) == {'r1'}
    selected = views['r1'][0]['span_ids']
    assert selected and all(catalog[s]['source_id'] == 'correct' for s in selected)


def test_valid_growth_suffix_without_comma_is_not_part_of_the_denominator():
    evidence = component('FDI represented 68% of total application value in 2021 after increasing 19% from 2020.',
                         'What share of application value was FDI in 2021?')
    assert percentage_evidence(evidence)['status'] == 'compatible'
    validate_quantity_roles('FDI represented 68% of total application value.', evidence)


def test_unrecognized_denominator_wording_is_unknown_not_a_false_mismatch():
    evidence = component('FDI represented 68% of all investment application value.',
                         'What share of application value was FDI?')
    assert percentage_evidence(evidence)['status'] == 'unknown'
    validate_quantity_roles('FDI represented 68% of all application value.', evidence)


def test_explicit_fdi_expansion_and_numerator_alias_limits():
    evidence = component('Foreign direct investment represented 68% of total application value.',
                         'What share of application value was FDI?')
    assert percentage_evidence(evidence)['status'] == 'compatible'
    validate_quantity_roles('FDI represented 68% of total application value.', evidence)
    evidence = component('Example Group represented 68% of total application value.',
                         'What share of application value was FDI?')
    assert percentage_evidence(evidence)['status'] == 'unknown'


def test_percent_headline_tail_does_not_become_part_of_following_numerator():
    evidence = component('Foreign Applications Up 22% Year-on-Year FDI represented 66% of total application value.',
                         'What share of application value was FDI?')
    assert percentage_evidence(evidence)['status'] == 'compatible'
    with pytest.raises(UnsupportedQuantityRole):
        validate_quantity_roles('FDI represented 22% of total application value.', evidence)
