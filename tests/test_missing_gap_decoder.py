"""Question-bound missing decoding; no model-quality claim or runtime repair."""
import copy
import json

import pytest
from pydantic import ValidationError

from src.pilot._choices import constrained_selection
from src.pilot._evidence import EvidenceSelection, GeographySelection
from src.pilot._source_selection import (
    SOURCE_SELECTION_INSTRUCTION, SourceSelection, SourceSelectionComponent, resolve_source_selection,
)

QUESTION = 'What was the synthetic canal annual operating loss in 2022?'
ANCHOR = 'annual operating loss in 2022'

def schema(**kwargs):
    return constrained_selection(SourceSelection, GeographySelection, {'labels':[]},
        [{'component_id':'r1','question_anchor':ANCHOR}], component_base=SourceSelectionComponent,
        question_bound_missing=True, **kwargs)

def missing():
    return {'wire_version':'source-selection-v1','components':[{'component_id':'r1','status':'missing',
            'evidence':[],'gap_anchor':ANCHOR}],
            'geography':{'status':'unresolved','value':'','evidence':[],'reason':'No place selected.'},'period':''}

def test_missing_schema_requires_exact_anchor_empty_evidence_and_explicit_fields():
    value=missing();before=copy.deepcopy(value)
    parsed=schema().model_validate(value)
    assert value==before and parsed.components[0].gap_anchor==ANCHOR
    node=schema().model_json_schema()['$defs']['MissingRequestSlot0']
    assert node['properties']['gap_anchor']['const']==ANCHOR
    assert node['properties']['evidence']['maxItems']==0
    assert {'gap_anchor','status','evidence','component_id'}<=set(node['required'])
    result,_=resolve_source_selection(parsed.model_dump(),{},QUESTION,{},'2026-11-02')
    assert result.components[0].status=='missing' and result.components[0].gap_anchor==ANCHOR

@pytest.mark.parametrize('anchor',['requested dated observation','unrequested revenue','', '2022'])
def test_missing_generic_altered_empty_or_noncanonical_anchor_is_rejected(anchor):
    value=missing();value['components'][0]['gap_anchor']=anchor
    with pytest.raises(ValidationError):schema().model_validate(value)

@pytest.mark.parametrize('field',['gap_anchor','evidence','status','component_id'])
def test_omitted_missing_fields_are_not_filled(field):
    value=missing();del value['components'][0][field]
    with pytest.raises(ValidationError):schema().model_validate(value)

def test_missing_background_evidence_is_rejected():
    value=missing();value['components'][0]['evidence']=['background']
    with pytest.raises(ValidationError):schema().model_validate(value)

def test_partial_preserves_literal_unanswered_fragment_and_requires_evidence():
    value=missing();value['components'][0].update(status='partial',evidence=['span'],gap_anchor='2022')
    assert schema().model_validate(value).components[0].gap_anchor=='2022'
    value['components'][0]['evidence']=[]
    with pytest.raises(ValidationError):schema().model_validate(value)

def test_legacy_default_decoder_is_not_silently_changed():
    legacy=constrained_selection(SourceSelection,GeographySelection,{'labels':[]},
        [{'component_id':'r1','question_anchor':ANCHOR}],component_base=SourceSelectionComponent)
    value=missing();value['components'][0]['gap_anchor']='unasked phrase'
    assert legacy.model_validate(value).components[0].gap_anchor=='unasked phrase'
    assert legacy.model_json_schema()['$defs']['UnresolvedRequestSlot0']['properties']['status']['enum']==['partial','missing','conflicting']
    with pytest.raises(ValueError,match='gap anchor is not in the question'):
        resolve_source_selection(value,{},QUESTION,{},'2026-11-02')
    old=constrained_selection(EvidenceSelection,GeographySelection,{'labels':[]},
        [{'component_id':'r1','question_anchor':ANCHOR}])
    assert 'short_answer' in old.model_json_schema()['$defs']['SupportedRequestSlot0']['required']


def test_conflict_still_requires_two_distinct_spans_and_preserves_gap_fragment():
    value=missing();value['components'][0].update(status='conflicting',evidence=['a','b'],gap_anchor='2022')
    assert schema().model_validate(value).components[0].gap_anchor=='2022'
    value['components'][0]['evidence']=['a']
    with pytest.raises(ValidationError):schema().model_validate(value)

@pytest.mark.parametrize('anchor',['',None,' '*3])
def test_invalid_application_request_cannot_build_a_missing_const(anchor):
    with pytest.raises(ValueError,match='nonempty supplied question anchor'):
        constrained_selection(SourceSelection,GeographySelection,{'labels':[]},
            [{'component_id':'r1','question_anchor':anchor}],component_base=SourceSelectionComponent,
            question_bound_missing=True)

def test_instruction_missing_example_uses_its_supplied_question_fragment():
    assert 'requested dated observation' not in SOURCE_SELECTION_INSTRUCTION
    assert 'gap_anchor exactly from that supplied request question_anchor' in SOURCE_SELECTION_INSTRUCTION
    assert '"gap_anchor":"annual profit in 2021"' in SOURCE_SELECTION_INSTRUCTION
    assert 'What was the trial operator annual profit in 2021?' in SOURCE_SELECTION_INSTRUCTION


@pytest.mark.parametrize('bad_response',[False,True])
def test_real_sdk_transmits_the_gap_const_and_never_repairs_invalid_response(monkeypatch,bad_response):
    import httpx
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage
    monkeypatch.delenv('OLLAMA_API_KEY',raising=False)
    value=missing()
    if bad_response:value['components'][0]['gap_anchor']='requested dated observation'
    seen=[]
    def handler(request):
        seen.append(json.loads(request.content))
        frame={'model':'fixture','message':{'role':'assistant','content':json.dumps(value)},'done':True}
        return httpx.Response(200,content=json.dumps(frame)+'\n',headers={'Content-Type':'application/x-ndjson'})
    model=ChatOllama(model='fixture',client_kwargs={'transport':httpx.MockTransport(handler),'trust_env':False})
    result=model.with_structured_output(schema(),include_raw=True).invoke([HumanMessage(content=QUESTION)])
    node=seen[0]['format']['$defs']['MissingRequestSlot0']
    assert node['properties']['gap_anchor']['const']==ANCHOR and node['properties']['evidence']['maxItems']==0
    if bad_response:
        assert result['parsed'] is None and result['parsing_error'] is not None
        assert 'requested dated observation' in result['raw'].content
    else:assert result['parsed'].components[0].gap_anchor==ANCHOR
