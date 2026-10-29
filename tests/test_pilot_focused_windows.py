"""Source-derived focus contracts; no model-quality or absence claims."""
import json
from pathlib import Path

import pytest

from src.pilot._continuations import complete_causal_spans
from src.pilot._evidence import build_span_catalog
from src.pilot._topics import topic_views


F=json.loads((Path(__file__).parent/'fixtures/focused_context_v1.json').read_text(encoding='utf-8'))


def prepare(sources,question=None):
    catalog=build_span_catalog(sources)
    result,trace=complete_causal_spans(question or F['question'],catalog,sources)
    return catalog,result,trace


def test_requested_categories_are_one_exact_cohesive_window():
    sources={'s':{'content':F['focused_source']}}
    before,catalog,trace=prepare(sources)
    assert len(catalog)==1
    span=next(iter(catalog.values()))
    assert span['text']==F['focused_source'] and span['text']==sources['s']['content'][span['start']:span['end']]
    assert len(trace['joined'][0]['member_ids'])==len(before)


def test_focused_record_prevents_mixed_overview_consuming_answer_units():
    sources={'focus':{'content':F['focused_source']},'overview':{'content':F['overview_source']}}
    _,catalog,_=prepare(sources)
    diagnostics={}
    views=topic_views(catalog,sources,[{'component_id':'r1','question_anchor':'How did private investment change?'}],diagnostics)
    assert all(catalog[s]['source_id']=='focus' for s in views['r1'][0]['span_ids'])
    assert all(catalog[s]['source_id']=='focus' for s in views['r1'][0]['extra_span_ids'])
    assert diagnostics['r1']['excluded_ids'] and not diagnostics['r1']['absence_established']


def test_unfocused_unknown_material_is_not_reclassified_as_absent():
    sources={'s':{'content':'Capital formation changed with local conditions.'}}
    _,catalog,_=prepare(sources)
    assert topic_views(catalog,sources,[{'component_id':'r1','question_anchor':'How did private investment change?'}])=={}


def test_unknown_causal_detail_within_a_primary_topic_record_remains_selectable():
    sources={'s':{'content':'Private consumption increased because hotels reopened. Receipts also reflected longer stays.'}}
    _,catalog,_=prepare(sources,'Why did private consumption increase?')
    views=topic_views(catalog,sources,[{'component_id':'r1','question_anchor':'Why did private consumption increase?'}])
    assert any('Receipts' in catalog[s]['text'] for s in views['r1'][0]['extra_span_ids'])


@pytest.mark.parametrize('separator',['\n\n','\r\n\r\n',' Public investment declined. '])
def test_cohesion_never_bridges_a_paragraph_or_different_subject(separator):
    text='Private investment declined.'+separator+'Investment in machinery increased.'
    _,catalog,_=prepare({'s':{'content':text}})
    assert not any('Private investment declined.' in s['text'] and 'machinery' in s['text'] for s in catalog.values())


def test_focus_does_not_keep_unknown_text_after_an_explicit_subject_change():
    sources={'s':{'content':'Private investment declined. Public investment increased. Other receipts rose.'}}
    _,catalog,_=prepare(sources)
    views=topic_views(catalog,sources,[{'component_id':'r1','question_anchor':'What supported private investment?'}])
    assert all('Other receipts' not in catalog[s]['text'] for s in views['r1'][0]['extra_span_ids'])


def test_long_windows_preserve_text_and_quote_limits():
    text='Private investment changed. '+'Investment in machinery changed with local conditions. '*30
    sources={'s':{'content':text}};original,catalog,_=prepare(sources)
    assert all(len(s['text'])<=600 for s in catalog.values())
    covered={i for s in catalog.values() for i in range(s['start'],s['end'])}
    assert {i for i,c in enumerate(text) if not c.isspace()} <= covered


def test_excessive_required_focus_fails_explicitly_instead_of_forcing_missing():
    sentence='Private investment changed because '+('local conditions ' *20)+'. '
    sources={'s':{'content':''.join(sentence.replace('changed because',f'changed in category {i} because') for i in range(7))}};_,catalog,_=prepare(sources)
    with pytest.raises(ValueError,match='five'):
        topic_views(catalog,sources,[{'component_id':'r1','question_anchor':'Which categories explain private investment changes?'}])


def test_different_source_records_are_never_coalesced():
    sources={'a':{'content':'Private investment declined.'},'b':{'content':'Investment in machinery increased.'}}
    original,catalog,_=prepare(sources)
    assert original==catalog


@pytest.mark.parametrize('guard_passes', [True, False])
def test_engine_retains_category_window_scope_and_guardrail_contract(tmp_path, guard_passes):
    from types import SimpleNamespace
    from langchain_core.messages import AIMessage
    from src.pilot.engine import Corpus, PilotEngine
    from src.pilot._evidence import EvidenceSelection
    texts = [F['quarter_header'],
        'Details of the economic conditions for May relative to the previous month are as follows:',
        F['focused_source'], F['quarter_source'], F['overview_source']]
    path = tmp_path / 'corpus.json'
    path.write_text(json.dumps([{'feed_id': f'FOCUS:unit:{i}:0', 'doc_name': 'FOCUS',
        'source': 'https://example.invalid/focus', 'published': '2019-07-01', 'clean_content': text}
        for i, text in enumerate(texts)]), encoding='utf-8')
    tools = iter([AIMessage(content='', tool_calls=[{'name': 'search_sources',
        'args': {'query': 'private investment', 'limit': 5}, 'id': 'one'}]), AIMessage(content='done')])
    captured = {}
    def structured(schema, **_):
        def invoke(messages):
            payload = json.loads(messages[1].content)
            if issubclass(schema, EvidenceSelection):
                captured['mapping_input'] = payload
                value = {'geography': {'status': 'unresolved', 'value': '', 'evidence': [], 'reason': 'No place.'},
                    'components': [{'component_id': cid, 'status': 'supported', 'short_answer': 'Selected directions and categories.',
                        'evidence': list(dict.fromkeys(v['span_ids'][0] for v in views))}
                        for cid, views in payload['request_evidence_views'].items()]}
            else:
                captured['composition_input'] = payload
                value = {'title': 'Analyst research brief', 'claims': []}  # Existing exact-excerpt fallback.
            return {'parsed': schema.model_validate(value), 'raw': AIMessage(content='fixed synthetic response')}
        return SimpleNamespace(invoke=invoke)
    model = SimpleNamespace(bind_tools=lambda _: SimpleNamespace(invoke=lambda _: next(tools)),
                            with_structured_output=structured)
    guards, events = [], []
    def guard(**kwargs):
        guards.append(kwargs)
        return {'passed_guardrails': guard_passes}
    run = lambda: PilotEngine(Corpus(path), model, SimpleNamespace(validate_output=guard)).run(
        F['question'], lambda k, v: events.append((k, v)))
    if guard_passes:
        result = run()
        assert result['metrics']['model_calls'] == 4 and len(result['draft']['claims']) == 2
        assert F['focused_source'] in result['draft']['claims'][0]['text']
        assert result['draft']['claims'][1]['text'].startswith('Second Quarter of 2019: ')
        assert 'tourism' not in ' '.join(c['text'] for c in result['draft']['claims'])
    else:
        with pytest.raises(ValueError, match='guardrails'):
            run()
    assert len(guards) == 1 and 'Construction investment was unchanged.' in guards[0]['raw_report']
    assert sum(k == 'model_request_started' for k, _ in events) == 4
    assert any(k == 'evidence_subject_focus' and v['r1']['excluded_ids'] for k, v in events)
    assert len(captured['composition_input']['units']) == 2
