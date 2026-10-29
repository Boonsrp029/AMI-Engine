"""Frozen synthetic subject checks, not model-quality or general entailment tests."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.pilot._topics import topic_evidence, topic_views, reject_topic_mismatches, validate_claim_topic
from src.pilot._evidence import build_span_catalog


CASES = {c['id']: c for c in json.loads((Path(__file__).parent/'fixtures/evidence_coverage_v1.json').read_text(encoding='utf-8'))['fixtures']}


def component(question, quotes, status='supported'):
    return SimpleNamespace(component_id='r1', question_anchor=question, status=status,
        evidence=[SimpleNamespace(source_id=sid, quote=q) for sid, q in quotes])


@pytest.mark.parametrize('case', ['wrong_subject', 'public_private_distinction'])
def test_known_wrong_selected_subject_is_rejected(case):
    c = CASES[case]
    check = topic_evidence(component(c['question'], [('s', c['selected_quote'])]), {'s': {'content': c['source']}})
    assert check['status'] == 'incompatible'
    with pytest.raises(ValueError, match='requested subject'):
        reject_topic_mismatches({'r1': check})


def test_bounded_same_record_antecedent_retains_category_detail():
    c = CASES['bounded_antecedent']
    check = topic_evidence(component(c['question'], [('s', c['selected_quote'])]), {'s': {'content': c['source']}})
    assert check['status'] == 'compatible'
    proof = check['evidence'][0]['antecedent']
    assert c['source'][proof['start']:proof['end']] == proof['text'] == 'Private investment'


@pytest.mark.parametrize('separator', ['\n\n', 'x' * 801, ' Public investment increased. '])
def test_antecedent_cannot_cross_a_paragraph_distance_or_subject_change(separator):
    quote = 'Investment in machinery increased.'
    text = 'Private investment was stable.' + separator + quote
    check = topic_evidence(component('How did private investment change?', [('s', quote)]), {'s': {'content': text}})
    assert check['status'] != 'compatible'


def test_identical_quote_in_two_positions_has_no_inferred_antecedent():
    quote = 'Investment in machinery increased.'
    text = 'Private investment increased. ' + quote + ' Public investment increased. ' + quote
    check = topic_evidence(component('How did private investment change?', [('s', quote)]), {'s': {'content': text}})
    assert check['status'] == 'unknown'


def test_antecedent_never_crosses_source_identifiers():
    check = topic_evidence(component('How did private investment change?', [('b', 'Investment in machinery increased.')]),
        {'a': {'content': 'Private investment increased.'}, 'b': {'content': 'Investment in machinery increased.'}})
    assert check['status'] == 'unknown'


@pytest.mark.parametrize('quote', ['Investment in machinery increased.', 'Vehicle investment increased.', 'Construction investment decreased.'])
def test_same_record_generic_category_sequence_retains_original_subject(quote):
    text = CASES['bounded_antecedent']['source'].removeprefix('SYNTHETIC: ')
    check = topic_evidence(component('Which categories explain private investment movements?', [('s', quote)]),
                           {'s': {'content': text}})
    assert check['status'] == 'compatible'
    proof = check['evidence'][0]['antecedent']
    assert proof['start'] == 0 and text[proof['start']:proof['end']] == 'Private investment'


def test_different_intervening_family_blocks_category_inheritance():
    text = 'Private investment increased. Consumption increased. Investment in machinery increased.'
    check = topic_evidence(component('How did private investment change?', [('s', 'Investment in machinery increased.')]),
                           {'s': {'content': text}})
    assert check['status'] == 'unknown'


def test_definition_is_not_a_causal_explanation():
    c = CASES['definition_not_cause']
    check = topic_evidence(component(c['question'], [('s', c['selected_quote'])]), {'s': {'content': c['sources'][0]}})
    assert check['status'] == 'incompatible'
    assert check['reason'] == 'definition_only_for_causal_request'


def test_causal_views_choose_explanation_instead_of_definition():
    c = CASES['definition_not_cause']
    sources = {str(i): {'content': text} for i, text in enumerate(c['sources'])}
    catalog = build_span_catalog(sources)
    views = topic_views(catalog, sources, [{'component_id': 'r1', 'question_anchor': c['question']}])
    assert all(catalog[s]['source_id'] == '1' for s in views['r1'][0]['span_ids'])


def test_definition_can_answer_a_definition_question():
    c = CASES['definition_not_cause']
    check = topic_evidence(component('What does the consumption index include?', [('s', c['selected_quote'])]),
                           {'s': {'content': c['sources'][0]}})
    assert check['status'] != 'incompatible'


def test_compound_request_needs_each_known_subject_or_an_explicit_partial_state():
    question = 'How did private investment and private consumption change?'
    quotes = [('s', 'Private consumption increased.')]
    supported = topic_evidence(component(question, quotes), {'s': {'content': quotes[0][1]}})
    assert supported['status'] == 'incompatible'
    partial = topic_evidence(component(question, quotes, 'partial'), {'s': {'content': quotes[0][1]}})
    assert partial['status'] == 'compatible'
    assert partial['unresolved_subjects'] == ['private_investment']


def test_unrecognized_aliases_do_not_create_false_missing_evidence():
    check = topic_evidence(component('How did private investment change?', [('s', 'Capital formation accelerated.')]),
                           {'s': {'content': 'Capital formation accelerated.'}})
    assert check['status'] == 'unknown'
    reject_topic_mismatches({'r1': check})


def test_qualitative_supported_information_does_not_require_figures():
    c = CASES['qualitative_supported_answer']
    check = topic_evidence(component(c['question'], [('s', c['source'])]), {'s': {'content': c['source']}})
    assert check['status'] == 'compatible'


def test_final_composed_claim_cannot_switch_known_measure():
    c = component('How did private investment change?', [('s', 'Private investment increased.')])
    with pytest.raises(ValueError, match='requested subject'):
        validate_claim_topic('Private consumption increased.', c)
    validate_claim_topic('Private investment increased.', c)


def test_final_claim_can_cover_a_subset_of_compound_component_units():
    c = component('How did private investment and private consumption change?', [('s', 'Private investment increased.')])
    validate_claim_topic('Private investment increased.', c)


def test_global_question_is_used_only_when_anchor_has_no_topic_and_question_is_unambiguous():
    c = component('What supported it?', [('s', 'Private consumption increased.')])
    assert topic_evidence(c, {}, 'How did private investment change and what supported it?')['status'] == 'incompatible'
    assert topic_evidence(c, {}, 'How did private investment and private consumption change?')['status'] == 'unknown'


def test_topic_views_do_not_force_an_unrecognized_synonym_into_a_missing_state():
    sources = {'s': {'content': 'Capital formation accelerated.'}}
    assert topic_views(build_span_catalog(sources), sources,
        [{'component_id': 'r1', 'question_anchor': 'How did private investment change?'}]) == {}


def test_subject_checks_stop_before_composition_or_guardrails_without_retry(tmp_path, monkeypatch):
    from langchain_core.messages import AIMessage
    from src.pilot import engine
    from src.pilot._evidence import EvidenceSelection

    c = CASES['wrong_subject']
    path = tmp_path/'corpus.json'
    path.write_text(json.dumps([{'feed_id': 's', 'clean_content': c['source'],
        'title': 'Synthetic development', 'source': 'https://example.invalid/report'}]), encoding='utf-8')
    corpus = engine.Corpus(path)
    # Isolate post-selection validation; decoder view restrictions have their
    # own contract below and would reject this choice even earlier.
    monkeypatch.setattr(engine, 'topic_views', lambda *_: {})
    responses = iter([AIMessage(content='', tool_calls=[{'name': 'search_sources',
        'args': {'query': 'private investment', 'limit': 3}, 'id': 'one'}]), AIMessage(content='done')])
    def structured(schema, **_):
        assert issubclass(schema, EvidenceSelection), 'Composition must never run'
        def invoke(messages):
            spans = [s for record in json.loads(messages[1].content)['evidence'] for s in record['spans']]
            selected = next(s['span_id'] for s in spans if s['text'] == c['selected_quote'])
            return {'parsed': schema.model_validate({'components': [{'component_id': 'r1',
                'status': 'supported', 'short_answer': c['selected_quote'], 'evidence': [selected]}],
                'geography': {'status': 'unresolved', 'value': '', 'evidence': [], 'reason': 'No location.'}}),
                'raw': AIMessage(content='fixed synthetic response')}
        return SimpleNamespace(invoke=invoke)
    model = SimpleNamespace(bind_tools=lambda _: SimpleNamespace(invoke=lambda _: next(responses)),
                             with_structured_output=structured)
    def safety(**_):
        pytest.fail('Rejected mapping must not reach guardrails')
    events = []
    with pytest.raises(ValueError, match='requested subject'):
        engine.PilotEngine(corpus, model, SimpleNamespace(validate_output=safety)).run(c['question'],
            event=lambda name, value: events.append((name, value)))
    assert [e['stage'] for name, e in events if name == 'model_request_started'] == [
        'tool_round_1', 'tool_round_2', 'evidence_mapping']
    check = next(e for name, e in events if name == 'mapped_requested_subjects')
    assert check['r1']['status'] == 'incompatible'
    assert sum(name == 'evidence_mapping_failure' for name, _ in events) == 1


def test_decoder_views_keep_known_wrong_subject_out_but_allow_explicit_missing():
    from pydantic import ValidationError
    from src.pilot._choices import constrained_selection
    from src.pilot._evidence import EvidenceSelection, GeographySelection
    c = CASES['wrong_subject']
    sources = {'s': {'content': c['source']}}
    catalog = build_span_catalog(sources)
    requests = [{'component_id': 'r1', 'question_anchor': c['question']}]
    views = topic_views(catalog, sources, requests)
    schema = constrained_selection(EvidenceSelection, GeographySelection, {'labels': []}, requests, [], views)
    wrong = next(s for s, span in catalog.items() if span['text'] == c['selected_quote'])
    value = {'geography': {'status': 'unresolved', 'value': '', 'evidence': [], 'reason': 'Not established.'},
        'components': [{'component_id': 'r1', 'status': 'supported', 'short_answer': c['selected_quote'], 'evidence': [wrong]}]}
    with pytest.raises(ValidationError):
        schema.model_validate(value)
    value['components'][0].update(status='missing', short_answer='', evidence=[], gap_anchor=c['question'])
    assert schema.model_validate(value).components[0].status == 'missing'
