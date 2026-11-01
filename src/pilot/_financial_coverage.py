"""Literal application-quantity coverage, not entity, date or causal entailment.

Only the existing explicit value/count plus each-change grammar is recognized.
Roles classify candidate spans, not individual quantities within a sentence.
Unknown vocabulary or ambiguous documents do not establish missing information.
"""
import re
from decimal import Decimal

from src.pilot._quantities import quantity_pairs
from src.utils._periods import _COMMAND, _MONTHS


POLICY = 'literal-application-comparison-v1'
_FORECAST = re.compile(r'\b(?:forecast\w*|projected|expected|scenario|target\w*|would|could)\b', re.I)
_PUBLICATION = re.compile(r'\b(?:published|publication|released|issued|dated)\b', re.I)
_SUBSET = re.compile(r'\b(?:FDI|foreign(?:\s+direct)?|domestic)\s+'
    r'(?:(?:investment(?:[-\s]+promotion)?|project)\s+)?applications?\b|'
    r'\bapplications?\s+(?:from|by)\s+(?!\d{4}\b)', re.I)
_YEAR = re.compile(r'\b(?:in|for|of|during)\s+(?:all\s+of\s+)?(\d{4})\b|'
    r'\b(?:' + '|'.join(_MONTHS.split()) + r')\s+(\d{4})\b', re.I)
_CHANGE = re.compile(r'\b(?:increased?|decreased?|rose|fell|grew|soared|up|down|higher|lower)\b', re.I)
_PERCENT = re.compile(r'(?<![\w.])(\d+(?:\.\d+)?)\s*%')


def _spec(question, requests):
    if (_FORECAST.search(question) or not re.search(r'\bapplications?\b', question, re.I)
            or len(requests) != 4 or [r.get('quantity_measure') for r in requests] != ['value', 'count', 'value', 'count']):
        return None
    base = re.findall(r'\bfrom\s+(\d{4})\b', requests[2]['question_anchor'], re.I)
    years = set(re.findall(r'\b\d{4}\b', question))
    if len(base) != 1 or len(years) != 2 or base[0] not in years:
        return None
    return {'current': next(iter(years - {base[0]})), 'baseline': base[0]}


def quantity_anchor(anchor):
    """Keep a typed quantity's selected comparison together during composition."""
    return bool(re.fullmatch(r'value|project\s+count|number\s+of\s+projects|'
        r'how\s+(?:did|does|do)\s+(?:each|both)\s+change\b.*', anchor, re.I))


def financial_views(catalog, sources, requests, question):
    spec = _spec(question, requests)
    if spec is None:
        return {}
    by_measure = {'value': {}, 'count': {}}
    eligible = {'value': {}, 'count': {}}
    for sid, span in catalog.items():
        text = span['text']
        source = sources[span['source_id']]
        if (_COMMAND.search(source['content']) or _FORECAST.search(text) or _PUBLICATION.search(text)
                or _SUBSET.search(text) or not re.search(r'\bapplications?\b', text, re.I)):
            continue
        years = {next(g for g in match.groups() if g) for match in _YEAR.finditer(text)}
        roles = [role for role, year in spec.items() if year in years]
        if years and not roles:
            continue  # A recognized different year is not an unknown date.
        units = {unit for unit, _ in quantity_pairs(text)}
        document = (tuple(source.get(k, '') for k in ('doc_name', 'url', 'published'))
            if source.get('doc_name') and source.get('url') else ('source', span['source_id']))
        for measure, known in [('value', bool(units & {'usd', 'baht'})), ('count', 'project' in units)]:
            if not known:
                continue
            eligible[measure].setdefault(document, []).append(sid)
            if not roles:
                continue
            slots = by_measure[measure].setdefault(document, {})
            for role in roles:
                slots.setdefault(role, []).append(sid)
            if 'current' in roles and _PERCENT.search(text) and _CHANGE.search(text):
                slots.setdefault('change', []).append(sid)
    result = {}
    for request in requests:
        documents = by_measure[request['quantity_measure']]
        if len(documents) != 1:
            continue  # No forced choice between potentially different subjects.
        groups = next(iter(documents.values()))
        if 'current' not in groups:
            continue  # A baseline alone cannot force out unknown current facts.
        requirements = [{'role': role, 'year': spec.get(role, spec['current']), 'span_ids': groups[role]}
            for role in ('current', 'baseline', 'change') if role in groups]
        ids = list(dict.fromkeys(sid for r in requirements for sid in r['span_ids']))
        document = next(iter(documents))
        optional = [sid for sid in eligible[request['quantity_measure']][document] if sid not in ids]
        ids.extend(optional)
        result[request['component_id']] = [{'role': 'financial_measure_comparison',
            'policy': POLICY, 'unordered_coverage': True, 'span_ids': ids,
            'optional_span_ids': optional,
            'coverage_requirements': requirements, 'allow_extra': False,
            'semantic_support_proven': False, 'absence_established': False}]
    return result


def validate_financial_selection(raw_component, views):
    if not views or raw_component['status'] not in {'supported', 'partial'}:
        return {'status': 'not_checked', 'semantic_support_proven': False}
    selected = set(raw_component['evidence'])
    if not selected.issubset(views[0]['span_ids']):
        raise ValueError('Selected evidence lies outside financial comparison choices')
    roles = views[0]['coverage_requirements']
    missing = [r['role'] for r in roles if not selected.intersection(r['span_ids'])]
    if missing:
        raise ValueError('Selected evidence omits available financial comparison coverage: ' + ', '.join(missing))
    return {'status': 'available_literal_roles_selected', 'roles': [r['role'] for r in roles],
        'policy': POLICY, 'semantic_support_proven': False}


def financial_context_omissions(text, evidence, request, question):
    from src.pilot._requests import requested_components
    spec = _spec(question, requested_components(question))
    if spec is None or request.get('quantity_measure') not in {'value', 'count'}:
        return {}
    quoted = ' '.join(e.quote for e in evidence)
    units = {'baht', 'usd'} if request['quantity_measure'] == 'value' else {'project'}
    expected = {pair for pair in quantity_pairs(quoted) if pair[0] in units}
    if not expected:
        return {}
    percentages = lambda value: {format(Decimal(m[1]).normalize(), 'f') for m in _PERCENT.finditer(value)}
    missing = {'quantity_pairs': [(u, str(n)) for u, n in sorted(expected - quantity_pairs(text))],
        'percentages': sorted(percentages(quoted) - percentages(text)),
        'years': sorted({y for y in spec.values() if re.search(r'\b' + y + r'\b', quoted)
            and not re.search(r'\b' + y + r'\b', text)})}
    return missing if any(missing.values()) else {}
