"""Literal quantity/percentage role checks, not unit conversion or entailment."""
from decimal import Decimal
import re
from types import SimpleNamespace


_NUMBER = r'[+-]?(?:\d{1,3}(?:[ ,]\d{3})+|\d+)(?:\.\d+)?'
_SCALE = r'trillion|billion|million|thousand'
_SUFFIX = re.compile(r'(?<![\w.,+-])(?P<number>' + _NUMBER + r')\s*'
    r'(?:(?P<scale>' + _SCALE + r')\s*)?(?P<unit>projects?|[kmgt]wh|tonnes?|baht|USD|THB)\b', re.I)
_CURRENCY = re.compile(r'(?<!\w)(?P<unit>USD|THB)\s*(?P<number>' + _NUMBER + r')'
    r'\s*(?P<scale>' + _SCALE + r')?\b', re.I)
_DENOMINATOR = re.compile(r'(?P<number>' + _NUMBER + r')\s*%\s+of\s+(?P<denominator>[^,.;:\n]+)', re.I)
_RATIO = re.compile(r'(?P<subject>[A-Za-z]+(?:\s+[A-Za-z]+){0,3})\s+'
    r'(?:represented|represents|accounted for|accounts for|constituted|constitutes|was|is)\s+'
    r'(?:(?:about|roughly|approximately)\s+)?(?P<number>' + _NUMBER + r')\s*%', re.I)
_REQUEST = re.compile(r'\b(?:what|which)\s+(?:share|percentage|proportion)\s+of\s+'
    r'(?P<denominator>.+?)\s+(?:was|were|is|are|came from)\s+(?P<subject>.+?)'
    r'(?:\s+(?:in|during|for)\s+\d{4}|\?|$)', re.I)
_SCALES = {'': Decimal(1), 'thousand': Decimal(1000), 'million': Decimal(1000000),
           'billion': Decimal(1000000000), 'trillion': Decimal(1000000000000)}
_STOP = {'the', 'of', 'in', 'on', 'for', 'all', 'total', 'overall', 'a', 'an'}


class UnsupportedQuantityRole(ValueError):
    """A parsed numeric role is absent or incompatible in selected evidence."""


def _number(text):
    return Decimal(text.replace(' ', '').replace(',', ''))


def _tokens(text):
    text = re.split(r'\s+after\s+(?:increasing|rising|growing|falling|decreasing|declining)\b', text, maxsplit=1, flags=re.I)[0]
    text = re.sub(r'\bforeign\s+direct\s+investments?\b', 'FDI', text, flags=re.I)
    values = []
    for token in re.findall(r'[A-Za-z]+', text.casefold()):
        if token in _STOP:
            continue
        token = token[:-1] if len(token) > 4 and token.endswith('s') else token
        values.append({'increase': 'growth', 'increment': 'growth', 'additional': 'growth'}.get(token, token))
    return frozenset(values)


def _subject(text):
    text = re.split(r'\b(?:as|when|where|that|while|because)\b', text, flags=re.I)[-1]
    return _tokens(text) - {'share', 'percentage', 'proportion'}


def _ratios(text):
    for match in _RATIO.finditer(text):
        subject = match['subject']
        if (re.match(r'^Year\s+', subject, re.I)
                and re.search(r'%\s*Year-on-$', text[:match.start()], re.I)):
            subject = re.sub(r'^Year\s+', '', subject, count=1, flags=re.I)
        yield _subject(subject), _number(match['number'])


def _denominator_relation(left, right):
    if left == right:
        return 'compatible'
    # Only declared distinctions establish incompatibility. Other wording stays
    # unknown rather than being equated or rejected as a different denominator.
    if left & right and any((term in left) != (term in right) for term in ('fdi', 'growth')):
        return 'incompatible'
    if (('value' in left and right & {'count', 'number'}) or
            ('value' in right and left & {'count', 'number'})):
        return 'incompatible'
    return 'unknown'


def quantity_pairs(text):
    """Parse a limited declared vocabulary; preserve scale without FX conversion."""
    result = set()
    for pattern in (_SUFFIX, _CURRENCY):
        for match in pattern.finditer(text):
            unit = match['unit'].casefold()
            unit = {'projects': 'project', 'tonnes': 'tonne', 'thb': 'baht'}.get(unit, unit)
            scale = (match['scale'] or '').casefold()
            result.add((unit, _number(match['number']) * _SCALES[scale]))
    return result


def percentage_evidence(component):
    """Check only literal requested ratio roles, never infer missing denominators."""
    request = _REQUEST.search(component.question_anchor)
    if request is None:
        return {'status': 'unknown', 'reason': 'no_literal_percentage_request'}
    denominator, subject = _tokens(request['denominator']), _subject(request['subject'])
    known_denominators, linked_subjects, matching_values = set(), set(), set()
    for evidence in component.evidence:
        percentages = list(_DENOMINATOR.finditer(evidence.quote))
        known_denominators.update(_tokens(p['denominator']) for p in percentages)
        for numerator, value in _ratios(evidence.quote):
            if any(value == _number(p['number']) and
                   _tokens(p['denominator']) == denominator for p in percentages):
                linked_subjects.add(numerator)
                if numerator == subject:
                    matching_values.add(str(value))
    if known_denominators and all(_denominator_relation(d, denominator) == 'incompatible' for d in known_denominators):
        return {'status': 'incompatible', 'reason': 'requested_percentage_denominator_absent'}
    if linked_subjects and subject not in linked_subjects:
        return {'status': 'unknown', 'reason': 'numerator_equivalence_not_established'}
    if matching_values:
        return {'status': 'compatible', 'reason': 'literal_percentage_role', 'values': sorted(matching_values)}
    return {'status': 'unknown', 'reason': 'percentage_role_not_established'}


def percentage_views(catalog, requests):
    """Constrain selection only when one explicit ratio value is unambiguous."""
    result = {}
    for request in requests:
        candidates, values = [], set()
        for sid, span in catalog.items():
            component = SimpleNamespace(question_anchor=request['question_anchor'],
                                        evidence=[SimpleNamespace(quote=span['text'])])
            check = percentage_evidence(component)
            if check['status'] == 'compatible':
                candidates.append(sid)
                values.update(check['values'])
        if candidates and len(values) == 1:
            result[request['component_id']] = [{'role': 'explicit_requested_percentage_role',
                                               'span_ids': candidates, 'allow_extra': True}]
    return result


def validate_quantity_roles(text, component, question=None):
    """Reject known literal mismatches; unparsed semantics remain unverified.

    All source material comes from this component's selected quotations. Years,
    unknown units, implicit denominators and conversions are not inferred.
    """
    check = percentage_evidence(component)
    if check['status'] == 'incompatible':
        raise UnsupportedQuantityRole('Selected evidence has an incompatible requested percentage role')
    quotes = [e.quote for e in component.evidence]
    established_pairs = set().union(*(quantity_pairs(q) for q in quotes))
    if not quantity_pairs(text).issubset(established_pairs):
        raise UnsupportedQuantityRole('Draft quantity value/unit pair is absent from selected evidence')
    denominator_by_value, ratios_by_subject = {}, {}
    for quote in quotes:
        for match in _DENOMINATOR.finditer(quote):
            denominator_by_value.setdefault(_number(match['number']), set()).add(_tokens(match['denominator']))
        for subject, value in _ratios(quote):
            ratios_by_subject.setdefault(subject, set()).add(value)
    for match in _DENOMINATOR.finditer(text):
        denominators = denominator_by_value.get(_number(match['number']))
        if denominators and all(_denominator_relation(_tokens(match['denominator']), d) == 'incompatible' for d in denominators):
            raise UnsupportedQuantityRole('Draft percentage denominator differs from selected evidence')
    for subject, value in _ratios(text):
        values = ratios_by_subject.get(subject)
        if values and value not in values:
            raise UnsupportedQuantityRole('Draft percentage subject/value role differs from selected evidence')
