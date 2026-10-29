"""Bounded summary proof, not the removed unbounded same-document fallback."""
import copy
import json
from pathlib import Path

import pytest

from src.pilot._evidence import EvidenceMap
from src.pilot._report_context import collect_context
from src.pilot._scope import resolve_scope
from src.pilot.engine import Corpus


F=json.loads((Path(__file__).parent/'fixtures/monthly_summary_v1.json').read_text(encoding='utf-8'))['fixture']
Q='How did factory orders change in May 2019?'


def fixture(tmp_path, quotes=None, change=None):
    texts=[F['header'],F['summary'],F['section'],F['detail'],F['quarter']]
    rows=[{'feed_id':f"{F['doc_name']}:unit:{i}:0",'doc_name':F['doc_name'],
        'source':'https://example.invalid/summary','published':'2019-06-28','clean_content':text} for i,text in enumerate(texts)]
    if change:change(rows)
    path=tmp_path/'corpus.json';path.write_text(json.dumps(rows),encoding='utf-8');corpus=Corpus(path)
    retrieved={sid:s for sid,s in corpus.sources.items() if ':unit:1:' in sid or ':unit:3:' in sid}
    selected=quotes or [(f"{F['doc_name']}:unit:1:0",corpus.sources[f"{F['doc_name']}:unit:1:0"]['content'])]
    mapping=EvidenceMap.model_validate({'components':[{'component_id':'r1','question_anchor':Q,'status':'supported',
        'short_answer':'Orders increased.','evidence':[{'source_id':s,'quote':q} for s,q in selected]}]})
    return corpus,retrieved,mapping


def test_summary_with_its_own_monthly_cue_binds_to_bounded_context(tmp_path):
    corpus,retrieved,mapping=fixture(tmp_path)
    added,bindings,_=collect_context(mapping,Q,retrieved,corpus.sources)
    assert len(added)==2 and len(bindings)==1
    assert bindings[0]['summary_factual_source_ids']==[f"{F['doc_name']}:unit:1:0"]
    _,scope=resolve_scope(mapping,Q,{**retrieved,**added},bindings)
    assert scope['components']['r1']['period']=='May 2019' and not scope['unresolved_requested_periods']


def test_summary_and_monthly_detail_can_share_the_verified_period(tmp_path):
    selected=[(f"{F['doc_name']}:unit:1:0",F['summary']),(f"{F['doc_name']}:unit:3:0",F['detail'])]
    corpus,retrieved,mapping=fixture(tmp_path,selected)
    added,bindings,_=collect_context(mapping,Q,retrieved,corpus.sources)
    assert len(bindings)==1
    _,scope=resolve_scope(mapping,Q,{**retrieved,**added},bindings)
    assert not scope['unresolved_requested_periods']


@pytest.mark.parametrize('quote', ['Factory orders increased.', 'Orders grew because machines were purchased.'])
def test_another_sentence_monthly_cue_cannot_date_the_selected_quote(tmp_path,quote):
    corpus,retrieved,mapping=fixture(tmp_path,[(f"{F['doc_name']}:unit:1:0",quote)],
        lambda rows:rows[1].update(clean_content=quote+' Sales increased from the previous month.'))
    assert not collect_context(mapping,Q,retrieved,corpus.sources)[1]


@pytest.mark.parametrize('change', [
    lambda rows:rows[0].update(clean_content=F['header'].replace('May','April')),
    lambda rows:rows[2].update(clean_content=F['section'].replace('May','April')),
    lambda rows:rows[0].update(clean_content='Published in May 2019.'),
    lambda rows:rows[1].update(clean_content='Factory orders are projected to increase from the previous month.'),
    lambda rows:rows[1].update(clean_content='In the first quarter, orders increased from the previous month.'),
])
def test_wrong_month_publication_forecast_and_quarter_do_not_bind(tmp_path,change):
    corpus,retrieved,mapping=fixture(tmp_path,change=change)
    assert not collect_context(mapping,Q,retrieved,corpus.sources)[1]


def test_changed_summary_content_cannot_be_bound_to_the_original_corpus(tmp_path):
    corpus,retrieved,mapping=fixture(tmp_path)
    sid=f"{F['doc_name']}:unit:1:0";retrieved=copy.deepcopy(retrieved)
    retrieved[sid]['content']='Different orders increased from the previous month.'
    mapping.components[0].evidence[0].quote=retrieved[sid]['content']
    with pytest.raises(ValueError,match='pinned'):
        collect_context(mapping,Q,retrieved,corpus.sources)


def test_quarterly_request_cannot_receive_a_monthly_binding_even_with_monthly_source(tmp_path):
    corpus,retrieved,mapping=fixture(tmp_path)
    added,bindings,_=collect_context(mapping,Q,retrieved,corpus.sources)
    mapping.components[0].question_anchor='quarter-on-quarter in the second quarter'
    assert not collect_context(mapping,Q,retrieved,corpus.sources)[1]
    with pytest.raises(ValueError,match='binding'):
        resolve_scope(mapping,Q,{**retrieved,**added},bindings)


@pytest.mark.parametrize('field', ['section_end','section_end_source_id','section_end_content_sha256','summary_factual_source_ids'])
def test_tampered_boundary_or_summary_membership_fails_before_scope_assignment(tmp_path,field):
    corpus,retrieved,mapping=fixture(tmp_path)
    added,bindings,_=collect_context(mapping,Q,retrieved,corpus.sources)
    assert bindings
    binding=copy.deepcopy(bindings)
    binding[0][field]=[100,0] if field=='section_end' else [] if field=='summary_factual_source_ids' else 'invalid'
    with pytest.raises(ValueError,match='binding'):
        resolve_scope(mapping,Q,{**retrieved,**added},binding)
