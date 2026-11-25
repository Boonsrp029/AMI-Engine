"""Literal application-quantity coverage, not entity, date or causal entailment.

Only the existing explicit value/count plus each-change grammar is recognized.
Roles classify candidate spans, not individual quantities within a sentence.
Unknown vocabulary or ambiguous documents do not establish missing information.
"""
import re
from decimal import Decimal
from itertools import permutations

from src.pilot._quantities import quantity_pairs, UnsupportedQuantityRole
from src.utils._periods import _COMMAND, _MONTHS


POLICY = 'literal-application-comparison-v1'
DECODER_SEQUENCE_LIMIT = 32
_FORECAST = re.compile(r'\b(?:forecast\w*|projected|expected|scenario|target\w*|would|could)\b', re.I)
_PUBLICATION = re.compile(r'\b(?:published|publication|released|issued|dated)\b', re.I)
_SUBSET = re.compile(r'\b(?:FDI|foreign(?:\s+direct)?|domestic)\s+'
    r'(?:(?:investment(?:[-\s]+promotion)?|project)\s+)?applications?\b|'
    r'\bapplications?\s+(?:from|by)\s+(?!\d{4}\b)', re.I)
_YEAR = re.compile(r'\b(?:in|for|of|during)\s+(?:all\s+of\s+)?(\d{4})\b|'
    r'\b(?:' + '|'.join(_MONTHS.split()) + r')\s+(\d{4})\b', re.I)
_CHANGE = re.compile(r'\b(?:increased?|decreased?|rose|fell|grew|soared|up|down|higher|lower)\b', re.I)
_PERCENT = re.compile(r'(?<![\w.])(\d+(?:\.\d+)?)\s*%')
_COUNT_NUMBER = r'(?:0|[1-9]\d{0,2}(?:,\d{3}){1,5}|[1-9]\d{0,17})'
_COUNT_CHANGE = (r'\s+(?:in|for|during)\s+(?:January\s+to\s+December\s+)?(?P<year>\d{4})'
    r'\s+(?P<direction>increased|decreased|rose|fell|grew)\s+(?P<growth>\d{1,6}(?:\.\d{1,6})?)%'
    r'\s+to\s+(?P<current>' + _COUNT_NUMBER + r')(?:\s+projects)?\s*,\s*from\s+'
    r'(?P<baseline>' + _COUNT_NUMBER + r')(?:\s+projects)?\s+in\s+'
    r'(?:the\s+same\s+period\s+of\s+)?(?P<baseyear>\d{4})\.?')
_PREFIX_COUNT = re.compile(r'(?:The\s+)?(?:total\s+)?number\s+of\s+projects' + _COUNT_CHANGE, re.I)
_SOURCE_COUNT = re.compile(r'(?:The\s+)?(?:total\s+)?number\s+of\s+'
    r'(?:projects|applications(?:\s+for\s+investment\s+promotion)?)'
    r'(?:\s+in\s+all\s+sectors)?(?:\s+filed)?' + _COUNT_CHANGE, re.I)


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


def decoder_coverage(view):
    """Bound decoder size while preserving all valid unordered selections.

    Small catalogs enumerate complete distinct sequences, including optional
    evidence and every order. Large catalogs retain a necessary minimum only;
    runtime role validation remains mandatory in either case. This does not
    choose evidence, infer missing roles or prove semantic support.
    """
    ids = list(dict.fromkeys(view['span_ids']))
    roles = [set(r['span_ids']) & set(ids) for r in view['coverage_requirements']]
    if not roles or any(not role for role in roles) or len(roles) > 3:
        raise ValueError('Financial decoder requires one to three offered coverage roles')
    masks = {sid: sum(1 << i for i, role in enumerate(roles) if sid in role) for sid in ids}
    full = (1 << len(roles)) - 1
    costs = {0: 0}
    for mask in masks.values():
        for seen, count in list(costs.items()):
            combined = seen | mask
            costs[combined] = min(costs.get(combined, 6), count + 1)
    minimum = costs[full]
    # At most325 sequences for five IDs. Never start an unbounded search over
    # a large corpus merely to discover that the decoder budget is exceeded.
    if len(ids) > 5:
        return minimum, None
    sequences = []
    for size in range(minimum, len(ids) + 1):
        for sequence in permutations(ids, size):
            if all(set(sequence) & role for role in roles):
                sequences.append(sequence)
                if len(sequences) > DECODER_SEQUENCE_LIMIT:
                    return minimum, None
    return minimum, sequences


def _count_binding(match):
    if match is None:
        return None
    current = Decimal(match['current'].replace(',', ''))
    baseline = Decimal(match['baseline'].replace(',', ''))
    direction = 'up' if match['direction'].casefold() in {'increased', 'rose', 'grew'} else 'down'
    return (match['year'], current, match['baseyear'], baseline, direction, Decimal(match['growth']))


def _bound_prefix_counts(text, evidence, spec):
    """Recognize only an explicit source/candidate year-count comparison.

    Unknown wording or ambiguous selected source bindings keeps the existing
    fallback. Matching numeric sets alone cannot establish this relationship.
    No entity/geography entailment, implied dates or calculated growth is added.
    """
    candidate = _count_binding(_PREFIX_COUNT.fullmatch(' '.join(text.split())))
    if candidate is None:
        return set()
    bindings = set()
    for e in evidence:
        project_pairs = {p for p in quantity_pairs(e.quote) if p[0] == 'project'}
        if not project_pairs:
            continue
        binding = _count_binding(_SOURCE_COUNT.fullmatch(' '.join(e.quote.split())))
        if (binding is None or {('project', binding[1]), ('project', binding[3])} != project_pairs
                or binding[0] != spec['current'] or binding[2] != spec['baseline']
                or not (binding[1] > binding[3] if binding[4] == 'up' else binding[1] < binding[3])):
            return set()
        bindings.add(binding)
    if len(bindings) != 1:
        return set()
    if candidate != next(iter(bindings)):
        raise UnsupportedQuantityRole('Draft project comparison differs from selected source year/count/growth bindings')
    return {('project', candidate[1]), ('project', candidate[3])}


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
    present = quantity_pairs(text)
    if request['quantity_measure'] == 'count':
        present |= _bound_prefix_counts(text, evidence, spec)
    percentages = lambda value: {format(Decimal(m[1]).normalize(), 'f') for m in _PERCENT.finditer(value)}
    missing = {'quantity_pairs': [(u, str(n)) for u, n in sorted(expected - present)],
        'percentages': sorted(percentages(quoted) - percentages(text)),
        'years': sorted({y for y in spec.values() if re.search(r'\b' + y + r'\b', quoted)
            and not re.search(r'\b' + y + r'\b', text)})}
    return missing if any(missing.values()) else {}
