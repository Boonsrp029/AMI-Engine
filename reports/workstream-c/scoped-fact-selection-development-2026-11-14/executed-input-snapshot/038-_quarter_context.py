"""Explicit quarterly headings and bounded source sections, never publication dates.

This supports the pinned unit-based preparation layout only. It establishes
reporting scope, not entailment, and shares the existing context/citation budget.
"""
import hashlib
import re

from src.pilot._scope import same_pinned_document
from src.utils._periods import _COMMAND, explicit_periods, reporting_period_headings


_QUARTER = re.compile(r'\b(first|second|third|fourth)[ -]quarter(?:\s+(?:of\s+)?(\d{4}))?\b', re.I)
_SECTION = re.compile(r'^(?:In|During) the (first|second|third|fourth) quarter\b', re.I)


def _proofs(text):
    # The existing heading parser checks month/quarter consistency and rejects
    # publication-only and command-shaped text before shared years are used.
    return [{**h, 'period': q.group(), 'quarter': q[1].casefold()}
            for h in reporting_period_headings(text)
            for q in _QUARTER.finditer(h['quote']) if q[2]]


def _requested(component, period):
    expected = _QUARTER.fullmatch(period)
    actual = list(_QUARTER.finditer(component.question_anchor))
    return (component.status in {'supported', 'partial'} and component.kind != 'projection'
            and expected is not None and len(actual) == 1
            and actual[0][1].casefold() == expected[1].casefold()
            and (not actual[0][2] or actual[0][2] == expected[2])
            and all(not explicit_periods(e.quote)
                    and not re.search(r'\b(?:forecast|projected|projection)\b', e.quote, re.I)
                    and all(q[1].casefold() == expected[1].casefold()
                            and (not q[2] or q[2] == expected[2]) for q in _QUARTER.finditer(e.quote))
                    for e in component.evidence))


def _hash(record):
    return hashlib.sha256(record['content'].encode()).hexdigest()


def _requested_year(component, question):
    """Constrain source choice; a question never establishes measurement scope."""
    from src.pilot._requests import requested_components
    quarters = list(_QUARTER.finditer(component.question_anchor))
    if len(quarters) == 1 and quarters[0][2]:
        return quarters[0][2]
    requests = requested_components(question) if question else []
    if any(r['component_id'] == component.component_id and r.get('comparison_role') == 'quarterly' for r in requests):
        monthly = [p for r in requests if r.get('comparison_role') == 'monthly'
                   for p in explicit_periods(r['question_anchor']) if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', p)]
        if len(monthly) == 1:
            return monthly[0].split()[-1]
    return ''


def _section_matches(text, proof):
    section = _SECTION.match(text)
    quarter = _QUARTER.search(text)
    expected = _QUARTER.fullmatch(proof['period'])
    return (section is not None and quarter is not None and expected is not None
            and section[1].casefold() == proof['quarter']
            and (not quarter[2] or quarter[2] == expected[2])
            and not _COMMAND.search(text))


def collect_quarter_context(mapping, retrieved, corpus, added, question=''):
    from src.pilot._report_context import _position, _BOUNDARY, _binding_digest
    bindings, skipped = [], []
    for component in mapping.components:
        if not _QUARTER.search(component.question_anchor) or not component.evidence:
            continue
        facts = [retrieved[e.source_id] for e in component.evidence]
        if any(_position(s) is None or not same_pinned_document(facts[0], s) for s in facts):
            continue
        if any(s['source_id'] not in corpus or s['content'] != corpus[s['source_id']]['content']
               or not same_pinned_document(s, corpus[s['source_id']]) for s in facts):
            raise ValueError('Reporting facts do not match the pinned corpus')
        records = sorted((s for s in corpus.values() if _position(s) is not None
                          and same_pinned_document(facts[0], s)), key=_position)
        if len({_position(s) for s in records}) != len(records):
            continue
        proofs = [(s, h) for s in records if _position(s) == (0, 0) and len(s['content']) <= 600
                  for h in _proofs(s['content'])]
        if len(proofs) != 1:
            continue
        heading, proof = proofs[0]
        requested_year = _requested_year(component, question)
        report_year = _QUARTER.fullmatch(proof['period'])[2]
        # An explicit historical quote is not re-dated from a later heading.
        dated_quote = any(explicit_periods(e.quote) or any(q[2] for q in _QUARTER.finditer(e.quote))
                          for e in component.evidence)
        if (requested_year and requested_year != report_year and component.status in {'supported', 'partial'}
                and component.kind != 'projection' and not dated_quote):
            raise ValueError('Quarterly report context conflicts with the requested comparison year')
        if not _requested(component, proof['period']):
            continue
        sections = [s for s in records if _section_matches(s['content'], proof)]
        if len(sections) != 1:
            continue
        section = sections[0]
        boundary = next((s for s in records if _position(s) > _position(section)
                         and _BOUNDARY.search(s['content'])), None)
        end = _position(boundary) if boundary else None
        if (not _position(heading) < _position(section)
                or any(_position(s) < _position(section) or (end is not None and _position(s) >= end)
                       for s in facts)):
            continue
        context = {s['source_id']: s for s in (heading, section)}
        # Long sections can be reused when already retrieved, never read as new
        # oversized context. Only genuinely additional records spend the budget.
        new = set(context) - set(retrieved)
        geographic_ids = {e.source_id for e in getattr(getattr(mapping, 'geography_resolution', None), 'evidence', [])}
        if (len((set(added) | new) - set(retrieved)) > 2
                or any(len(context[sid]['content']) > 600 for sid in new)
                or len(set(context) | {s['source_id'] for s in facts} | geographic_ids) > 5):
            skipped.append({'component_id': component.component_id, 'reason': 'context or citation budget'})
            continue
        added.update(context)
        binding = {'component_id': component.component_id, 'period': proof['period'],
            'proof_format': 'bounded-quarterly-v1', 'quarter': proof['quarter'],
            'heading_source_id': heading['source_id'], 'section_source_id': section['source_id'],
            'heading_content_sha256': _hash(heading), 'section_content_sha256': _hash(section),
            'section_start': list(_position(section)), 'section_end': list(end) if end else None,
            'section_end_source_id': boundary['source_id'] if boundary else None,
            'section_end_content_sha256': _hash(boundary) if boundary else None,
            'factual_source_ids': list(dict.fromkeys(s['source_id'] for s in facts)),
            'factual_content_sha256': {s['source_id']: _hash(s) for s in facts},
            **{k: proof[k] for k in ('quote', 'start', 'end', 'normalization')}}
        binding['binding_sha256'] = _binding_digest(binding)
        bindings.append(binding)
    return bindings, skipped


def quarter_binding_matches(binding, component, sources, question=''):
    from src.pilot._report_context import _position, _binding_digest
    heading, section = (sources[binding[key]] for key in ('heading_source_id', 'section_source_id'))
    facts = [sources[e.source_id] for e in component.evidence]
    proof = [h for h in _proofs(heading['content']) if h['period'] == binding['period']]
    if (binding.get('binding_sha256') != _binding_digest(binding)
            or not _requested(component, binding['period']) or len(proof) != 1
            or (_requested_year(component, question)
                and _requested_year(component, question) != _QUARTER.fullmatch(binding['period'])[2])
            or any(proof[0][k] != binding[k] for k in ('quote', 'start', 'end', 'normalization', 'quarter'))
            or _position(heading) != (0, 0) or not _section_matches(section['content'], binding)
            or list(_position(section) or ()) != binding['section_start']
            or _COMMAND.search(section['content'])
            or set(binding['factual_source_ids']) != {s['source_id'] for s in facts}
            or any(not same_pinned_document(heading, s) for s in [section, *facts])
            or any(_position(s) is None or _position(s) < tuple(binding['section_start'])
                   or (binding['section_end'] and _position(s) >= tuple(binding['section_end']))
                   or _hash(s) != binding['factual_content_sha256'].get(s['source_id']) for s in facts)
            or any(e.quote not in sources[e.source_id]['content'] for e in component.evidence)
            or _hash(heading) != binding['heading_content_sha256']
            or _hash(section) != binding['section_content_sha256']):
        raise ValueError('Reporting context identity or quarterly section binding is invalid')
    return {'component_id': component.component_id, 'source_id': heading['source_id'],
        'quote': binding['quote'], 'context_start': binding['start'], 'context_end': binding['end'],
        'content_sha256': binding['heading_content_sha256'],
        'context_source_ids': list(dict.fromkeys([heading['source_id'], section['source_id']])),
        'role': 'explicit shared-year quarterly report heading and bounded quarterly section',
        'normalization': binding['normalization']}
