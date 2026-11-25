"""Bounded component retrieval using lexical scores and source-context hints."""
from types import SimpleNamespace
from src.pilot._requests import retrieval_facets
from src.pilot._retrieval_policy import LEXICAL_VERSION, rank_evidence
from src.pilot._source_context import context_sources, assess_mapping

COMPONENT_VERSION = 'pilot-component-lexical-v3'


def rank_components(query, sources, limit, requested_query=None):
    intent = requested_query or query
    facets = retrieval_facets(intent) if intent.strip() else []
    contexts = context_sources(sources, sources)
    queues, diagnostics, omitted = [], [], []
    for facet in facets:
        ranked, _ = rank_evidence(query, sources.values(), len(sources), facet['query'])
        priorities = []
        for index, source in enumerate(ranked):
            # Whole records here are ranking candidates, never validated answer mappings.
            component = SimpleNamespace(component_id=facet['component_id'], question_anchor=facet['query'],
                status='supported', evidence=[SimpleNamespace(source_id=source['source_id'], quote=source['content'])])
            check = assess_mapping(SimpleNamespace(components=[component]), intent, contexts)[facet['component_id']]
            if check['status'] == 'incompatible':
                omitted.append({'source_id': source['source_id'], 'component_id': facet['component_id'],
                                'reasons': check['reason_codes']})
                continue
            priorities.append((0 if check['status'] == 'compatible' else 1, index, source))
        priorities.sort(key=lambda row: (row[0], row[1]))
        queues.append([row[2] for row in priorities])
        diagnostics.append({**facet, 'eligible_records': len(priorities),
                            'ranked_ids': [row[2]['source_id'] for row in priorities[:10]]})
    selected, seen = [], set()
    while len(selected) < limit and any(queues):
        for queue in queues:
            while queue and queue[0]['source_id'] in seen:
                queue.pop(0)
            if queue:
                source = queue.pop(0)
                selected.append(source)
                seen.add(source['source_id'])
                if len(selected) == limit:
                    break
    return selected, {'policy': COMPONENT_VERSION, 'base_policy': LEXICAL_VERSION, 'original_query': query,
        'requested_query': intent, 'facets': diagnostics, 'source_ids': [s['source_id'] for s in selected],
        'known_incompatible_candidates_omitted': omitted, 'model_calls': 0,
        'scope_note': 'Scope is a ranking constraint, not entailment. Unknown records remain eligible. Original text and source IDs are unchanged.'}
