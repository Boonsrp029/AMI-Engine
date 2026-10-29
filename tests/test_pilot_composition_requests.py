"""Task context and factual authority stay separate; fixed responses only."""
import copy
import json
from types import SimpleNamespace

from langchain_core.messages import AIMessage
import pytest

from src.pilot._composition import payload,canonical_units
from src.pilot._evidence import EvidenceMap,EvidenceSelection,COMPOSITION_INSTRUCTION
from src.pilot.engine import Corpus,PilotEngine


def mapping():
    return EvidenceMap.model_validate({'components':[
        {'component_id':'r1','question_anchor':'What share of value was foreign?',
         'status':'supported','short_answer':'BAD LOSSY SUMMARY','evidence':[{'source_id':'a',
            'quote':'Foreign applications grew 25%. Foreign applications represented 61% of total application value.'}]},
        {'component_id':'r2','question_anchor':'Did Cedar or Maple have more projects?',
         'status':'supported','short_answer':'UNTRUSTED DERIVED ANSWER','evidence':[{'source_id':'b',
            'quote':'Cedar had 17 projects. Maple had 29 projects.'}]}]})


def test_requests_identify_measures_without_becoming_evidence_or_mapper_summaries():
    m=mapping();before=m.model_dump();result=payload(m,'2026-10-29')
    assert result['requests']==[{'component_id':c.component_id,'question_anchor':c.question_anchor,'status':c.status} for c in m.components]
    assert 'BAD LOSSY SUMMARY' not in json.dumps(result) and 'UNTRUSTED DERIVED ANSWER' not in json.dumps(result)
    assert all('question_anchor' not in u and 'short_answer' not in u for u in result['units'])
    assert result['units'][0]['evidence']==[e.model_dump() for e in m.components[0].evidence]
    assert m.model_dump()==before and 'not factual authority' in COMPOSITION_INSTRUCTION


def test_canonical_evidence_retains_both_request_origins():
    m=mapping();m.components[1].evidence=copy.deepcopy(m.components[0].evidence)
    result=payload(m,'2026-10-29')
    assert len(result['units'])==1 and len(result['units'][0]['origins'])==2
    assert [r['component_id'] for r in result['requests']]==['r1','r2']
    assert result['units'][0]['evidence']==canonical_units(m)[0]['evidence']


def test_missing_requests_and_unrestricted_gaps_are_not_composition_material():
    m=mapping();m.components[1].status='missing';m.components[1].short_answer='';m.components[1].evidence=[]
    m.components[1].gap_anchor='GAP MUST NOT ENTER COMPOSITION'
    result=payload(m,'2026-10-29')
    assert len(result['requests'])==1 and 'GAP MUST NOT ENTER COMPOSITION' not in json.dumps(result)


def test_dates_and_geography_in_request_do_not_become_established_scope():
    m=mapping();m.components[0].question_anchor='What happened in Atlantis in 2070?'
    result=payload(m,'2026-10-29')
    assert result['requests'][0]['question_anchor'].endswith('2070?')
    assert all(u['established_scope']=={} for u in result['units'])
    assert all('Atlantis' not in str(u['evidence']) for u in result['units'])


@pytest.mark.parametrize('guard_passes',[True,False])
def test_actual_engine_delivers_request_to_composer_and_retains_guard_and_call_bounds(tmp_path,guard_passes):
    path=tmp_path/'corpus.json';path.write_text(json.dumps([{'feed_id':'fact','clean_content':'Foreign applications represented 61% of total application value.'}]))
    tools=iter([AIMessage(content='',tool_calls=[{'name':'search_sources','args':{'query':'foreign application value','limit':3},'id':'one'}]),AIMessage(content='done')])
    guards=[];events=[]
    def structured(schema,**_):
        def invoke(messages):
            value=json.loads(messages[1].content)
            if issubclass(schema,EvidenceSelection):
                sid=value['evidence'][0]['spans'][0]['span_id']
                raw={'components':[{'component_id':'r1','status':'supported','short_answer':'61%','evidence':[sid]}],
                     'geography':{'status':'unresolved','value':'','evidence':[],'reason':'No supported place.'}}
            else:
                assert value['requests']==[{'component_id':'r1','question_anchor':'What share of total application value was foreign?','status':'supported'}]
                assert '61%' in value['units'][0]['evidence'][0]['quote']
                raw={'title':'Analyst research brief','claims':[{'component_id':'r1','unit_id':'u1','text':'Foreign applications represented 61% of total application value.'}]}
            return {'parsed':schema.model_validate(raw),'raw':AIMessage(content='fixed response')}
        return SimpleNamespace(invoke=invoke)
    model=SimpleNamespace(bind_tools=lambda _:SimpleNamespace(invoke=lambda _:next(tools)),with_structured_output=structured)
    def guard(**kwargs):guards.append(kwargs);return {'passed_guardrails':guard_passes}
    run=lambda:PilotEngine(Corpus(path),model,SimpleNamespace(validate_output=guard)).run('What share of total application value was foreign?',lambda k,v:events.append(k))
    if guard_passes:assert run()['metrics']['model_calls']==4
    else:
        with pytest.raises(ValueError,match='guardrails'):run()
    assert len(guards)==1 and events.count('model_request_started')==4
