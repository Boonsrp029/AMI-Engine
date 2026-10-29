"""Coverage for the existing literal monthly/quarterly comparison grammar.

This reuses retrieval facets and pinned contexts. Two selected sides establish
structural coverage, not correct reasoning, directions or category completeness.
"""
import re
from types import SimpleNamespace

from src.pilot._component_retrieval import retrieval_facets
from src.pilot._source_context import assess_mapping
from src.pilot._topics import topic_evidence,focused_choices,_DETAIL_REQUEST
from src.utils._periods import _COMMAND


def _facets(question):
    return [f for f in retrieval_facets(question) if f['role'] in {'monthly', 'quarterly'}]


def _check(facet, evidence, sources, contexts):
    component = SimpleNamespace(component_id=facet['component_id'], question_anchor=facet['query'],
                                status='supported', evidence=[evidence])
    scope = assess_mapping(SimpleNamespace(components=[component]), facet['query'], contexts)[facet['component_id']]
    topic = topic_evidence(component, sources)
    context = contexts[evidence.source_id]
    if (facet['role'] == 'quarterly' and context['section_kind'] == 'monthly'
            and not re.search(r'\bquarter\b|\bquarterly\b', evidence.quote, re.I)):
        scope = {**scope, 'status': 'incompatible', 'reason_codes': ['monthly_section_for_quarterly_comparison']}
    status = ('incompatible' if 'incompatible' in {scope['status'], topic['status']} else
              'compatible' if scope['status'] == topic['status'] == 'compatible' else 'unknown')
    return {'source_id': evidence.source_id, 'status': status, 'scope': scope, 'subject': topic}


def comparison_views(question, catalog, sources, contexts, diagnostics=None):
    facets = _facets(question)
    if not facets:
        return {}
    views = {}
    for facet in facets:
        checks = {sid:_check(facet,SimpleNamespace(source_id=span['source_id'],quote=span['text']),sources,contexts)
                  for sid,span in catalog.items() if not _COMMAND.search(span['text'])}
        ids = [sid for sid,check in checks.items() if check['status']=='compatible']
        extras = [sid for sid,check in checks.items() if check['status']!='incompatible']
        if not ids:
            continue  # Unknown classification does not erase another supported slot.
        groups,extras,trace=focused_choices(catalog,sources,facet['query'],ids,extras,bool(_DETAIL_REQUEST.search(question)))
        for cid in facet['covers_components']:
            views.setdefault(cid,[]).extend({'role':facet['role']+'_requested_comparison','span_ids':group,
                'extra_span_ids':extras,'allow_extra':True} for group in groups)
            if diagnostics is not None:diagnostics[cid]=trace
    return views


def assess_comparisons(mapping, question, sources, contexts):
    facets, result = _facets(question), {}
    for component in mapping.components:
        needed = [f for f in facets if component.component_id in f['covers_components']]
        if not needed or component.status not in {'supported', 'partial'}:
            continue
        roles = []
        for facet in needed:
            evidence = [_check(facet, e, sources, contexts) for e in component.evidence]
            status = ('compatible' if any(e['status'] == 'compatible' for e in evidence) else
                      'incompatible' if evidence and all(e['status'] == 'incompatible' for e in evidence) else 'unknown')
            roles.append({'role': facet['role'], 'status': status, 'evidence': evidence})
        unresolved = [r['role'] for r in roles if r['status'] != 'compatible']
        status = ('compatible' if not unresolved else
                  'incompatible' if all(r['status']=='incompatible' for r in roles) else
                  'partial' if component.status=='partial' and any(r['status']=='compatible' for r in roles) else 'unknown')
        result[component.component_id] = {'status': status, 'unresolved_roles': unresolved, 'roles': roles}
    return result


def reject_incomplete_comparisons(checks):
    if any(c['status'] == 'incompatible' for c in checks.values()):
        raise ValueError('Supported comparison omits an established requested period or subject')
