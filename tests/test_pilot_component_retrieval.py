"""Synthetic retrieval coverage, not generated answer or entailment evidence."""
import copy
import json

from src.pilot._component_retrieval import retrieval_facets, rank_components
from src.pilot.engine import Corpus


def corpus(tmp_path):
    rows = []
    for name, month in [('CURRENT', 'May'), ('OTHER', 'June')]:
        texts = [f'Economic Conditions for {month} 2020',
            f'Details of the economic conditions for {month} relative to the previous month are as follows:',
            'Private credit increased from the previous month because machinery lending expanded.',
            'In the second quarter, private credit decreased from the previous quarter because construction loans fell.']
        rows += [{'feed_id': f'{name}:unit:{i}:0', 'doc_name': name, 'source': 'https://example.invalid/'+name,
                  'published': '2020-07-31', 'clean_content': text} for i, text in enumerate(texts)]
    rows.append({'feed_id': 'calendar', 'clean_content': 'May 2020 June 2020'})
    path = tmp_path/'corpus.json'
    path.write_text(json.dumps(rows), encoding='utf-8')
    return Corpus(path)


def test_literal_monthly_quarterly_comparison_gets_two_search_facets():
    question = ('How did private credit compare month-on-month in May 2020 and quarter-on-quarter '
                'in the second quarter, and which categories explain those directions?')
    facets = retrieval_facets(question)
    assert facets[0]['query'] == 'private credit month-on-month in May 2020'
    assert facets[1]['query'] == 'private credit quarter-on-quarter in the second quarter'
    assert [f['component_id'] for f in facets] == ['r1','r2']
    assert all('which categories' not in f['query'] for f in facets)


def test_other_grammars_keep_canonical_request_queries_without_inventing_subjects():
    facets = retrieval_facets('What changed in credit, and why did consumption increase?')
    assert [f['query'] for f in facets] == ['What changed in credit', 'why did consumption increase?']


def test_search_returns_monthly_and_quarterly_evidence_within_original_limit(tmp_path):
    c = corpus(tmp_path)
    question = ('How did private credit compare month-on-month in May 2020 and quarter-on-quarter '
                'in the second quarter, and which categories explain those directions?')
    before = copy.deepcopy(c.sources)
    selected, trace = rank_components('private credit', c.sources, 2, question)
    assert [s['source_id'] for s in selected] == ['CURRENT:unit:2:0', 'CURRENT:unit:3:0']
    assert len(selected) == 2 and c.sources == before
    assert trace['known_incompatible_candidates_omitted']
    assert trace['model_calls'] == 0


def test_overlapping_component_hits_are_deduplicated_then_backfilled(tmp_path):
    c = corpus(tmp_path)
    selected, trace = rank_components('private credit', c.sources, 3,
        'What changed in private credit in May 2020, and why did private credit change?')
    assert selected[0]['source_id'] == 'CURRENT:unit:2:0'
    assert len({s['source_id'] for s in selected}) == len(selected)
    assert not any(s['source_id'] == 'OTHER:unit:2:0' for s in selected)
    assert 'calendar' not in trace['source_ids']


def test_generic_unknown_scope_ties_and_empty_requests_remain_deterministic():
    records = {'a': {'source_id': 'a', 'content': 'Investment rose.'},
               'b': {'source_id': 'b', 'content': 'Investment rose.'}}
    assert rank_components('investment', records, 2, 'What changed in investment?')[0] == list(records.values())
    assert rank_components('unknown term', records, 2, 'Unknown term')[0] == []
    assert rank_components('May 2020', records, 2, 'May 2020')[0] == []
    assert rank_components('', records, 2)[0] == []


def test_matching_explicit_historical_dates_are_not_removed_due_to_later_heading(tmp_path):
    c = corpus(tmp_path)
    source = c.sources['OTHER:unit:2:0']
    source['content'] = 'In May 2020 private credit rose by 6% from April 2020.'
    selected, _ = rank_components('private credit', c.sources, 3, 'What happened to private credit in May 2020?')
    assert source in selected


def test_corpus_runtime_uses_component_policy_without_changing_raw_search(tmp_path):
    c = corpus(tmp_path)
    question = ('How did private credit compare month-on-month in May 2020 and quarter-on-quarter '
                'in the second quarter, and which categories explain those directions?')
    raw = c.search('private credit', 3)
    selected, trace = c.search_evidence('private credit', 2, requested_query=question)
    assert [s['source_id'] for s in selected] == ['CURRENT:unit:2:0', 'CURRENT:unit:3:0']
    assert c.search('private credit', 3) == raw
    assert all(s is c.sources[s['source_id']] for s in selected)
    assert trace['policy'] == 'pilot-component-lexical-v3'
    assert len(c.search_policy_sha) == 64
