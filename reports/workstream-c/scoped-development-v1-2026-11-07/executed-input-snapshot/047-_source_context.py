"""Pinned report/section checks; compatible provenance is not semantic support."""
import hashlib
import re

from src.pilot._report_context import _position, _SECTION
from src.pilot._scope import same_pinned_document, measurement_periods
from src.utils._periods import _COMMAND, _key, explicit_periods, reporting_period_headings
from src.pilot._requests import requested_periods


_QUARTER = re.compile(r'\b(first|second|third|fourth)[ -]quarter\b', re.I)
_QUARTER_SECTION = re.compile(r'^(?:In|During) the (first|second|third|fourth) quarter\b', re.I)
_RELATIVE_MONTH = re.compile(r'\bprevious month\b|\bmonth-on-month\b', re.I)
_FORECAST = re.compile(r'\b(?:is|are|was|were|be)\s+(?:forecast|projected|expected)\b|'
                       r'\b(?:forecast|projected|expected)\s+to\b', re.I)
_OBSERVED_REQUEST = re.compile(r'\b(?:actual|observed|realized)\b', re.I)
_FORECAST_REQUEST = re.compile(r'\b(?:forecast|projected|projection|expected)\b', re.I)


class EvidenceContextMismatch(ValueError):
    """An established source context is incompatible with its requested use."""


def _proof(record):
    return {'source_id': record['source_id'], 'content_sha256': hashlib.sha256(record['content'].encode()).hexdigest(),
            'position': list(_position(record))}


def context_sources(retrieved, corpus):
    """Describe original records, never infer periods from names or publication.

    Only the pinned HTML preparation layout is understood. Other layouts remain
    unknown. Header and section proof do not attest source truth or entailment.
    """
    result, documents = {}, {}
    for sid, source in retrieved.items():
        description = {'source_id': sid, 'report_period': '', 'section_kind': 'unknown',
                       'section_period': '', 'quarter': '', 'proof': [], 'relative_month': False}
        result[sid] = description
        position = _position(source)
        if position is None:
            continue
        pinned = corpus.get(sid)
        if (pinned is None or source['content'] != pinned['content']
                or not same_pinned_document(source, pinned)):
            raise ValueError('Context does not match the pinned source')
        key = tuple(source.get(k) for k in ('doc_name', 'url', 'published', 'corpus_sha256'))
        if key not in documents:
            records = sorted((s for s in corpus.values() if _position(s) is not None
                              and same_pinned_document(source, s)), key=_position)
            positions = [_position(s) for s in records]
            heads = [(s, h) for s in records if _position(s) == (0, 0) and len(s['content']) <= 600
                     for h in reporting_period_headings(s['content'])]
            documents[key] = (records, heads) if len(positions) == len(set(positions)) else ([], [])
        records, heads = documents[key]
        if len(heads) != 1:
            continue
        header, heading = heads[0]
        description.update(report_period=heading['period'], proof=[_proof(header)],
                           relative_month=bool(_RELATIVE_MONTH.search(source['content'])))
        for record in records:
            if _position(record) > position:
                break
            if _position(record) <= (0, 0) or _COMMAND.search(record['content']):
                continue
            monthly = _SECTION.fullmatch(record['content']) if len(record['content']) <= 600 else None
            quarterly = _QUARTER_SECTION.match(record['content'])
            if monthly:
                year = monthly['year'] or heading['period'].split()[1]
                description.update(section_kind='monthly', section_period=monthly['month'] + ' ' + year,
                                   quarter='', proof=[_proof(header), _proof(record)])
            elif quarterly:
                description.update(section_kind='quarterly', section_period='',
                                   quarter=quarterly[1].casefold(), proof=[_proof(header), _proof(record)])
    return result


def _requested(component, question):
    anchor = component.question_anchor
    quarter = bool(re.search(r'\bquarter\b|\bquarterly\b', anchor, re.I))
    # Do not inherit a monthly request onto an explicitly quarterly component.
    periods = requested_periods(anchor,question)
    return periods, quarter


def assess_mapping(mapping, question, contexts):
    """Check known incompatibility, leaving missing provenance explicitly unknown.

    Selected explicit historical dates take precedence over a later report's
    heading. Date identity alone cannot establish measure, geography or causality.
    """
    checks = {}
    for component in mapping.components:
        periods, quarter_requested = _requested(component, question)
        check = {'status': 'not_applicable', 'requested_periods': periods, 'reason_codes': [], 'evidence': []}
        checks[component.component_id] = check
        if component.status not in {'supported', 'partial'}:
            continue
        outcomes = []
        for evidence in component.evidence:
            context = contexts[evidence.source_id]
            status, reason = 'unknown', 'measurement_context_unresolved'
            quote_periods = {p.casefold() for p in measurement_periods(evidence.quote)}
            if (_OBSERVED_REQUEST.search(component.question_anchor + ' ' + question)
                    and not _FORECAST_REQUEST.search(component.question_anchor)
                    and _FORECAST.search(evidence.quote)):
                status, reason = 'incompatible', 'forecast_for_observed_request'
            elif len(periods) == 1 and periods[0].casefold() in quote_periods:
                status, reason = 'compatible', 'explicit_requested_period'
            elif len(periods) == 1 and not quarter_requested:
                if context['section_kind'] == 'quarterly':
                    status, reason = 'incompatible', 'quarterly_evidence_for_monthly_request'
                elif context['section_kind'] == 'monthly' or context['relative_month']:
                    actual = context['section_period'] or context['report_period']
                    actual_key, requested_key = _key(actual) if actual else None, _key(periods[0])
                    if actual_key and requested_key:
                        if actual_key[:7] != requested_key[:7]:
                            status, reason = 'incompatible', 'incompatible_reporting_month'
                        elif len(requested_key) == 7:
                            status, reason = 'compatible', 'matching_reporting_month'
                        else:
                            reason = 'report_month_does_not_establish_requested_day'
            elif quarter_requested and not periods and context['section_kind'] == 'quarterly':
                requested_quarters = {m.casefold() for m in _QUARTER.findall(component.question_anchor)}
                if requested_quarters:
                    status = 'compatible' if context['quarter'] in requested_quarters else 'incompatible'
                    reason = 'matching_quarterly_section' if status == 'compatible' else 'incompatible_quarterly_section'
            elif (quarter_requested and not periods and (context['section_kind']=='monthly' or context['relative_month'])
                    and not re.search(r'\bquarter\b|\bquarterly\b',evidence.quote,re.I)):
                status,reason='incompatible','monthly_evidence_for_quarterly_request'
            outcomes.append(status)
            check['reason_codes'].append(reason)
            check['evidence'].append({'source_id': evidence.source_id, 'status': status, 'reason': reason,
                                      'context': context})
        check['status'] = ('incompatible' if 'incompatible' in outcomes else
                           'compatible' if outcomes and all(x == 'compatible' for x in outcomes) else 'unknown')
        check['reason_codes'] = list(dict.fromkeys(check['reason_codes']))
    return checks


def reject_incompatible(checks):
    if any(c['status'] == 'incompatible' for c in checks.values()):
        raise EvidenceContextMismatch('Selected evidence has incompatible requested reporting context')


def mapper_context(context):
    """Typed provenance hints only; no new factual spans or source instructions."""
    return {key: context[key] for key in ('report_period', 'section_kind', 'section_period', 'quarter')}
