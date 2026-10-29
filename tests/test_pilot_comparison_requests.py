"""Integration of request identity, source scope and comparison evidence."""
import json
from pathlib import Path
from types import SimpleNamespace

from langchain_core.messages import AIMessage
import pytest

from src.pilot._requests import requested_components
from src.pilot._source_context import assess_mapping
from src.pilot._evidence import EvidenceSelection
from src.pilot.engine import Corpus,PilotEngine


CONTRACT=json.loads((Path(__file__).parent/'fixtures/comparison_requests_v1.json').read_text(encoding='utf-8'))
Q=CONTRACT['question']


def test_comparison_anchors_are_literal_and_each_requires_direction_and_categories():
    requests=requested_components(Q)
    assert [r['question_anchor'].rstrip('?') for r in requests]==CONTRACT['expected_anchors']
    assert [r['comparison_role'] for r in requests]==['monthly','quarterly']
    assert all(r['question_anchor'] in Q and 'private investment' in r['instruction'] and 'categories' in r['instruction'] for r in requests)


def test_canonical_quarter_component_is_not_reinterpreted_as_monthly():
    requests=requested_components(Q)
    component=SimpleNamespace(component_id='r2',question_anchor=requests[1]['question_anchor'],status='supported',
        evidence=[SimpleNamespace(source_id='q',quote='Private investment declined because construction fell.')])
    contexts={'q':{'section_kind':'quarterly','quarter':'second','section_period':'','report_period':'May 2020','relative_month':False}}
    assert assess_mapping(SimpleNamespace(components=[component]),Q,contexts)['r2']['status']=='compatible'


def corpus(tmp_path,missing_quarter=False):
    texts=['Economic Conditions for May 2020','Details of the economic conditions for May relative to the previous month are as follows:',
        'Private investment increased from the previous month because machinery purchases rose.',
        'In the second quarter, private investment declined from the previous quarter because construction fell.']
    if missing_quarter:texts.pop()
    rows=[{'feed_id':f'SYNTHETIC_COMPARE:unit:{i}:0','doc_name':'SYNTHETIC_COMPARE',
        'source':'https://example.invalid/comparison','published':'2020-07-01','clean_content':text} for i,text in enumerate(texts)]
    path=tmp_path/'corpus.json';path.write_text(json.dumps(rows),encoding='utf-8')
    return Corpus(path)


@pytest.mark.parametrize('wrong_composed_date,missing_quarter', [(False,False),(True,False),(False,True)])
def test_comparison_uses_four_calls_and_keeps_periods_separate(tmp_path,wrong_composed_date,missing_quarter):
    c=corpus(tmp_path,missing_quarter);tools=iter([AIMessage(content='',tool_calls=[{'name':'search_sources',
        'args':{'query':'private investment','limit':3},'id':'one'}]),AIMessage(content='done')]);guards=[];events=[]
    def structured(schema,**_):
        def invoke(messages):
            if issubclass(schema,EvidenceSelection):
                payload=json.loads(messages[1].content);spans=[s for record in payload['evidence'] for s in record['spans']]
                monthly=next(s['span_id'] for s in spans if s['text'].startswith('Private investment increased'))
                quarterly=None if missing_quarter else next(s['span_id'] for s in spans if s['text'].startswith('In the second quarter'))
                raw={'components':[{'component_id':cid,'status':'supported','short_answer':'Selected direction and activities.',
                    'evidence':[sid]} for cid,sid in [('r1',monthly),('r2',quarterly)]],
                    'geography':{'status':'unresolved','value':'','evidence':[],'reason':'No location.'}}
                if missing_quarter:raw['components'][1].update(status='missing',short_answer='',evidence=[],gap_anchor='quarter-on-quarter in the second quarter')
            else:
                units=json.loads(messages[1].content)['units']
                raw={'title':'Analyst research brief','claims':[{'component_id':u['component_id'],'unit_id':u['unit_id'],
                    'text':('May 2020: ' if wrong_composed_date and u['component_id']=='r2' else '')+u['evidence'][0]['quote']} for u in units]}
            return {'parsed':schema.model_validate(raw),'raw':AIMessage(content='Fixed synthetic response')}
        return SimpleNamespace(invoke=invoke)
    model=SimpleNamespace(bind_tools=lambda _:SimpleNamespace(invoke=lambda _:next(tools)),with_structured_output=structured)
    guard=SimpleNamespace(validate_output=lambda **kwargs:guards.append(kwargs) or {'passed_guardrails':True})
    result=PilotEngine(c,model,guard).run(Q,lambda k,v:events.append((k,v)))
    assert result['metrics']['model_calls']==4 and len(guards)==1
    assert len(result['draft']['claims'])==(1 if missing_quarter else 2)
    assert result['draft']['claims'][0]['text'].startswith('May 2020: ')
    if not missing_quarter:assert result['draft']['claims'][1]['text'].startswith('In the second quarter')
    else:assert any('quarter-on-quarter in the second quarter' in w for w in result['draft']['warnings'])
    assert not any('requested period is not established' in w for w in result['draft']['warnings'])
    assert any(k=='mapped_source_context' and v['r2']['status']==('not_applicable' if missing_quarter else 'compatible') for k,v in events)


def test_unrecognized_comparison_does_not_guess_subjects_or_periods():
    q='Could you compare figures across some periods?'
    assert requested_components(q)==[{'component_id':'r1','question_anchor':q}]


def test_comparison_without_category_request_does_not_invent_that_requirement():
    q=Q.split(', and which')[0]+'?'
    assert all('categories' not in r['instruction'] for r in requested_components(q))


def test_quarterly_component_does_not_receive_a_monthly_scope_from_another_component():
    from src.pilot._evidence import EvidenceMap
    from src.pilot._scope import resolve_scope
    requests=requested_components(Q)
    text=['Private investment increased in May 2020.','In the second quarter, investment declined after May 2020 movements.']
    mapping=EvidenceMap.model_validate({'components':[{'component_id':r['component_id'],'question_anchor':r['question_anchor'],
        'status':'supported','short_answer':quote,'evidence':[{'source_id':str(i),'quote':quote}]} for i,(r,quote) in enumerate(zip(requests,text))]})
    _,context=resolve_scope(mapping,Q)
    assert context['components']['r1']['period']=='May 2020'
    assert 'period' not in context['components'].get('r2',{})
    assert not context['unresolved_requested_periods']
