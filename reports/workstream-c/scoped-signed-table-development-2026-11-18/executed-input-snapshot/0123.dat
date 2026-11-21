"""Necessary direction checks for explicit comparison subjects, not entailment."""
import re

from src.pilot._topics import _mentions
from src.utils._periods import _COMMAND


_MOVE = (r'(?P<flat>remained stable|remained unchanged|stayed stable|stayed unchanged|'
         r'was stable|were stable|was unchanged|were unchanged|did not change|stable|unchanged)'
         r'|(?P<up>increased|rose|grew|expanded)|(?P<down>declined|decreased|fell|contracted)')
_DIRECT = re.compile(r'^\s*(?:indicators?|index|indices)?\s*'
    r'(?:,\s*(?:after seasonal adjustment|however)\s*,\s*)?'
    r'(?:(?:slightly|strongly|notably)\s+)?(?:' + _MOVE + r')\b', re.I)
_BARE = re.compile(r'^(?:' + _MOVE + r')[.!]?$', re.I)
_QUALIFIER = re.compile(r'\b(?:net|gross|real|nominal|growth|rate|share|per capita)\b', re.I)


def _move(match):
    return next(name for name in ('flat', 'up', 'down') if match.group(name))


def _directions(text, subject):
    if (_COMMAND.search(text) or re.search(
            r'\b(?:forecast|projected|projection|expected|scenario|would|could)\b|\?', text, re.I)):
        return set()
    directions = set()
    for topic, start, end in _mentions(text):
        if topic == subject:
            clause_prefix = re.split(r'[.!?;:\n,]', text[:start])[-1]
            if _QUALIFIER.search(clause_prefix):
                continue
            match = _DIRECT.match(text[end:])
            if match:
                directions.add(_move(match))
    return directions


def assess_direction(facet, component, evidence_checks):
    query_subject = re.split(r'\s+(?:month-on-month|quarter-on-quarter)\b', facet['query'], flags=re.I)[0]
    mentions = list(_mentions(query_subject))
    result = {'status': 'unknown', 'semantic_support_proven': False,
              'source_directions': [], 'answer_directions': []}
    if len(mentions) != 1 or '_' not in mentions[0][0]:
        return {**result, 'reason': 'subject_outside_declared_literal_vocabulary'}
    subject, start, end = mentions[0]
    # Category/measure modifiers cannot silently become the aggregate. Prefix
    # place names are not used to establish geographical applicability here.
    suffix = query_subject[end:].strip().casefold()
    if (suffix not in {'', 'indicators', 'indicator', 'index', 'indices'}
            or _QUALIFIER.search(query_subject[:start])):
        return {**result, 'reason': 'requested_subject_has_unresolved_qualifier'}
    source = set()
    for evidence, check in zip(component.evidence, evidence_checks):
        if check['status'] == 'compatible':
            source.update(_directions(evidence.quote, subject))
    answer = getattr(component, 'short_answer', '').strip()
    found = _directions(answer, subject)
    bare = _BARE.fullmatch(answer)
    if bare:
        found.add(_move(bare))
    result.update(subject=subject, source_directions=sorted(source), answer_directions=sorted(found))
    if not source or not found:
        return {**result, 'reason': 'literal_direction_not_established'}
    if len(source) != 1 or len(found) != 1 or source != found:
        return {**result, 'status': 'incompatible', 'reason': 'aggregate_direction_mismatch_or_conflict'}
    return {**result, 'status': 'compatible', 'reason': 'matching_literal_aggregate_direction'}
