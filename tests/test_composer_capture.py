"""Frozen diagnostic stages are not new inference or a safety verdict."""
import json

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.graph import StateGraph
import pytest

from scripts._composer_capture import capture_composer
from scripts._mapper_transport import sha
from src.pilot._evidence import build_span_catalog
from src.pilot.engine import Corpus


Q = 'What happened to sales, and did Cedar or Maple have more projects?'


def fixture(tmp_path, count_only=False):
    corpus = tmp_path/'corpus.json'
    corpus.write_text(json.dumps([{'feed_id':'REPORT:unit:0:0','doc_name':'SYNTHETIC_REPORT',
        'source':'https://example.invalid/report','published':'2020-01-01',
        'clean_content':'Sales rose by 6%. Cedar had 17 projects. Maple had 29 projects.'}]),encoding='utf-8')
    catalog = build_span_catalog(Corpus(corpus).sources)
    ids = [sid for entity in ('Cedar','Maple') for sid,span in catalog.items() if span['text'].startswith(entity)]
    sales = [sid for sid,span in catalog.items() if span['text'].startswith('Sales')]
    components = [] if count_only else [{'component_id':'r1','status':'supported',
        'short_answer':'Sales rose by 6%.','evidence':sales}]
    components.append({'component_id':'r1' if count_only else 'r2','status':'supported','short_answer':'Maple','evidence':ids})
    mapping = {'components':components,
        'geography':{'status':'unresolved','value':'','evidence':[],'reason':'No resolved place.'},'period':''}
    attempt = tmp_path/'attempt.json'
    attempt.write_text(json.dumps({'query':'Did Cedar or Maple have more projects?' if count_only else Q,'captured_model_outputs':[
        {'stage':'tool','content':'','tool_calls':[{'id':'one','type':'tool_call','name':'search_sources',
            'args':{'query':'projects','limit':3}}]},
        {'stage':'tool','content':'Fixed tool turn.','tool_calls':[]},
        {'stage':'structured','content':json.dumps(mapping)},
        {'stage':'structured','content':'Retained composition is not used as a new response.'}]}),encoding='utf-8')
    return attempt,corpus


def replay(attempt,corpus,callback=None):
    return capture_composer(attempt,corpus,'2026-10-30',callback,expected_attempt_sha256=sha(attempt))


def test_capture_has_request_context_and_no_guard_or_model_client(tmp_path,monkeypatch):
    attempt,corpus=fixture(tmp_path)
    import socket
    monkeypatch.setattr(socket.socket,'connect',lambda *a:pytest.fail('No network is allowed'))
    original_add=StateGraph.add_node
    result=replay(attempt,corpus)
    assert StateGraph.add_node is original_add
    assert result['actual_model_calls']==result['nemo_invocations']==result['target_callback_invocations']==0
    assert result['frozen_tool_replays']==2 and result['frozen_mapper_replays']==1
    payload=json.loads(result['captured']['messages'][1]['content'])
    assert payload['requests'][0]['question_anchor']=='What happened to sales'
    assert len(payload['units'])==1 and len(payload['units'][0]['evidence'])==1
    assert payload['units'][0]['evidence'][0]['quote']=='Sales rose by 6%.'
    assert not any(e['kind']=='guard_invocation_started' for e in result['events'])
    assert 'draft' not in result


def response(text,unit='u1',component='r1'):
    return {'title':'Analyst research brief','claims':[{'unit_id':unit,'component_id':component,'text':text}]}


def fixed(value,seen):
    def callback(schema,messages):
        seen.append(messages)
        raw=AIMessage(content=json.dumps(value))
        return {'raw':raw,'parsed':PydanticOutputParser(pydantic_object=schema).invoke(raw),'parsing_error':None}
    return callback


def test_supported_composition_passes_real_projection_before_safety(tmp_path):
    attempt,corpus=fixture(tmp_path);seen=[]
    result=replay(attempt,corpus,fixed(response('Sales rose by 6%.'),seen))
    assert len(seen)==result['target_callback_invocations']==1
    assert result['status'].startswith('passed actual composition validation')
    assert result['draft']['claims'][0]['source_ids']==['REPORT:unit:0:0']
    assert '29 projects' in result['draft']['claims'][1]['text']
    assert result['sources']['REPORT:unit:0:0']['content'].endswith('29 projects.')
    assert result['nemo_invocations']==result['actual_model_calls']==0
    assert not any(e['kind'] in {'guard_invocation_started','guardrails'} for e in result['events'])


@pytest.mark.parametrize('value',[response('Sales rose by 7%.'),
    response('Cedar had 17 projects; Maple had 29 projects. Cedar had more.',unit='u2',component='r2'),
    response('Sales rose by 6% and fell by 17%.'),
    response('Sales rose by 6%.',unit='unknown'),
    response('Sales rose by 6%.',component='unknown')])
def test_invalid_composition_is_rejected_without_another_callback(tmp_path,value):
    attempt,corpus=fixture(tmp_path);seen=[];original_add=StateGraph.add_node
    with pytest.raises(ValueError):replay(attempt,corpus,fixed(value,seen))
    assert len(seen)==1 and StateGraph.add_node is original_add


def test_changed_retained_attempt_rejected_before_replay(tmp_path):
    attempt,corpus=fixture(tmp_path);digest=sha(attempt)
    attempt.write_text('{}')
    with pytest.raises(ValueError,match='identity'):
        capture_composer(attempt,corpus,'2026-10-30',expected_attempt_sha256=digest)


def test_unexpected_stage_sequence_is_not_silently_repaired(tmp_path):
    attempt,corpus=fixture(tmp_path);data=json.loads(attempt.read_text());data['captured_model_outputs'].pop()
    attempt.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='exactly two'):replay(attempt,corpus)


def test_count_only_capture_never_calls_composer_or_guard(tmp_path):
    attempt,corpus=fixture(tmp_path,count_only=True)
    result=replay(attempt,corpus,lambda *_:pytest.fail('Application-owned counts must not invoke composer'))
    assert result['captured']=={} and result['target_callback_invocations']==0
    assert result['actual_model_calls']==result['nemo_invocations']==0
    assert result['draft']['claims'][0]['text'].endswith('Maple had more projects.')
    assert not any(e['kind'] in {'guard_invocation_started','guardrails'} for e in result['events'])
