"""Bounded, source-backed monthly report context; never infer from publication."""
import hashlib
import re

from src.pilot._scope import same_pinned_document
from src.utils._periods import _MONTHS, _COMMAND, explicit_periods, reporting_period_headings


_POSITION = re.compile(r"(?P<document>.+):unit:(?P<unit>\d+):(?P<chunk>\d+)")
_SECTION = re.compile(r"Details of the economic conditions for (?P<month>" + '|'.join(_MONTHS.split())
    + r")(?: (?P<year>\d{4}))? relative to the previous month are as follows:\s*", re.I)
_BOUNDARY = re.compile(r"^(?:(?:In|During) the (?:first|second|third|fourth) quarter\b|Details of the economic conditions for\b|Press Release on\b)", re.I)


def _position(record):
    match = _POSITION.fullmatch(record['source_id'])
    if match and match['document'] == record.get('doc_name') and record.get('page_num') is None:
        return int(match['unit']), int(match['chunk'])
    return None


def _eligible(component, period):
    return (component.status in {'supported', 'partial'} and component.kind != 'projection'
        and not any(re.search(r'\b(?:project(?:ed|ion|s)|forecast)\b', e.quote, re.I)
                    or _BOUNDARY.search(e.quote)
                    or any(p.casefold() != period.casefold() for p in explicit_periods(e.quote))
                    for e in component.evidence))


def collect_context(mapping, question, retrieved, corpus):
    """Read at most two <=600-character original context records after mapping.

    Only the preparation format's explicit unit locators are supported. Monthly
    section order and the next explicit section/quarter boundary limit binding.
    Other formats or ambiguous records retain unresolved scope.
    """
    periods = explicit_periods(question)
    added, bindings, skipped = {}, [], []
    if len(periods) != 1:
        return added, bindings, {'skipped': skipped, 'reason': 'one explicit requested period required'}
    period = periods[0]
    for component in mapping.components:
        if not _eligible(component, period):
            continue
        facts = [retrieved[e.source_id] for e in component.evidence]
        if not facts or any(_position(s) is None or not same_pinned_document(facts[0], s) for s in facts):
            continue
        records = [s for s in corpus.values() if same_pinned_document(facts[0], s) and _position(s) is not None]
        positions = [_position(s) for s in records]
        if len(positions) != len(set(positions)):
            continue
        records.sort(key=_position)
        heads = [(s, h) for s in records if _position(s) == (0, 0) and len(s['content']) <= 600
                 for h in reporting_period_headings(s['content']) if h['period'].casefold() == period.casefold()]
        if len(heads) != 1:
            continue
        heading, proof = heads[0]
        month, year = period.split()
        sections = [s for s in records if len(s['content']) <= 600 and not _COMMAND.search(s['content'])
            and (match := _SECTION.fullmatch(s['content'])) and match['month'].casefold() == month.casefold()
            and (not match['year'] or match['year'] == year) and _position(s) > _position(heading)]
        if len(sections) != 1:
            continue
        section = sections[0]
        boundary = next((s for s in records if _position(s) > _position(section) and _BOUNDARY.search(s['content'])), None)
        end = _position(boundary) if boundary is not None else None
        if not all(_position(s) > _position(section) and (end is None or _position(s) < end) for s in facts):
            continue
        context_ids = [heading['source_id'], section['source_id']]
        geographic_ids = {e.source_id for e in getattr(getattr(mapping, 'geography_resolution', None), 'evidence', [])}
        if len(set(added) | set(context_ids)) > 2 or len({s['source_id'] for s in facts} | set(context_ids) | geographic_ids) > 5:
            skipped.append({'component_id': component.component_id, 'reason': 'context or citation budget'})
            continue
        added.update({s['source_id']: s for s in (heading, section)})
        bindings.append({'component_id': component.component_id, 'period': proof['period'],
            'heading_source_id': heading['source_id'], 'section_source_id': section['source_id'],
            'factual_source_ids': list(dict.fromkeys(s['source_id'] for s in facts)),
            'section_start': list(_position(section)), 'section_end': list(end) if end is not None else None,
            'section_end_source_id': boundary['source_id'] if boundary else None,
            'section_end_content_sha256': hashlib.sha256(boundary['content'].encode()).hexdigest() if boundary else None,
            'heading_content_sha256': hashlib.sha256(heading['content'].encode()).hexdigest(),
            'section_content_sha256': hashlib.sha256(section['content'].encode()).hexdigest(), **{k: proof[k] for k in ('quote', 'start', 'end', 'normalization')}})
    return added, bindings, {'skipped': skipped, 'source_ids': list(added), 'maximum_context_records': 2}


def binding_matches(binding, component, sources):
    """Validate exact context identity again before assigning component scope."""
    heading, section = (sources[binding[key]] for key in ('heading_source_id', 'section_source_id'))
    facts = [sources[e.source_id] for e in component.evidence]
    proof = [h for h in reporting_period_headings(heading['content']) if h['period'] == binding['period']]
    section_match = _SECTION.fullmatch(section['content'])
    if (not _eligible(component, binding['period']) or not section_match or len(proof) != 1
            or any(proof[0][k] != binding[k] for k in ('quote', 'start', 'end', 'normalization'))
            or _position(heading) != (0, 0) or list(_position(section) or ()) != binding['section_start']
            or section_match['month'].casefold() != binding['period'].split()[0].casefold()
            or (section_match['year'] and section_match['year'] != binding['period'].split()[1])
            or _COMMAND.search(section['content'])
            or {s['source_id'] for s in facts} != set(binding['factual_source_ids'])
            or any(not same_pinned_document(heading, s) for s in [section, *facts])
            or any(_position(s) is None or _position(s) <= tuple(binding['section_start'])
                   or (binding['section_end'] is not None and _position(s) >= tuple(binding['section_end'])) for s in facts)
            or any(hashlib.sha256(record['content'].encode()).hexdigest() != binding[key]
                   for record, key in ((heading, 'heading_content_sha256'), (section, 'section_content_sha256')))):
        raise ValueError('Reporting context identity or section binding is invalid')
    return {'component_id': component.component_id, 'source_id': heading['source_id'],
        'quote': binding['quote'], 'context_start': binding['start'], 'context_end': binding['end'],
        'content_sha256': binding['heading_content_sha256'], 'context_source_ids': [heading['source_id'], section['source_id']],
        'role': 'explicit report heading and bounded monthly section', 'normalization': binding['normalization']}
