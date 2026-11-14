"""Literal financial-subject checks with bounded, same-record antecedents.

This declared vocabulary is not an ontology or an entailment judge. Unknown
subjects remain unknown; a valid source identity never proves semantic support.
"""
import re
from types import SimpleNamespace
from src.utils._periods import _COMMAND


_JOIN = r'[\s\u2010-\u2014-]+'
_TOPIC = re.compile(r'\b(?:(private|public|government)' + _JOIN + r'(investment|consumption)|'
                    r'(headline|core)' + _JOIN + r'(inflation)|(investment|consumption|inflation))\b', re.I)
_CAUSAL_REQUEST = re.compile(r'\bwhy\b|\bwhat (?:supported|drove)\b|\bcauses?\b|\bdrivers?\b|'
                             r'\b(?:which|what) factors?\b|\bactivities supported\b', re.I)
_CAUSE = re.compile(r'\bbecause\b|\bdue to\b|\bdriven (?:primarily )?by\b|\bsupported by\b|'
                    r'\breflect(?:s|ed|ing)\b|\b(?:as )?a result of\b', re.I)
_DEFINITION = re.compile(r'\b(?:index|indicator|measure|definition)\b.{0,100}'
                         r'\b(?:includes?|measures?|covers?|defined|comprises?)\b', re.I | re.S)
_DETAIL_REQUEST = re.compile(r'\b(?:categories|activities)\b',re.I)
_CAUSAL_ANAPHOR = re.compile(r'^(?:This|That|These|Those|It)\b.{0,60}?'
    r'(?:\bbecause\b|\bdue to\b|\ba result of\b|\bdriven by\b|\bsupported by\b|\breflect(?:s|ed|ing)\b)',re.I)


def _mentions(text):
    for match in _TOPIC.finditer(text):
        qualifier, family = (match[1], match[2]) if match[2] else (match[3], match[4]) if match[4] else ('', match[5])
        qualifier = 'public' if (qualifier or '').casefold() == 'government' else (qualifier or '').casefold()
        yield (qualifier + '_' if qualifier else '') + family.casefold(), match.start(), match.end()


def _topics(text):
    return {topic for topic, _, _ in _mentions(text)}


def _family(topic):
    return topic.rsplit('_', 1)[-1]


def _primary_subject(text):
    subjects=_topics(text)
    specific={s for s in subjects if '_' in s}
    if len(specific)==1 and all(_family(s)==_family(next(iter(specific))) for s in subjects):
        subjects=specific
    return next(iter(subjects)) if len(subjects)==1 else None


def _matches(found, wanted):
    return found == wanted or ('_' not in wanted and _family(found) == wanted)


def _different(found, wanted):
    return _family(found) != _family(wanted) or ('_' in found and '_' in wanted and found != wanted)


def _requested(component, question):
    topics = _topics(component.question_anchor)
    if not topics and question:
        whole = _topics(question)
        if len(whole) == 1:
            topics = whole
    return topics


def _quote_topics(evidence, sources):
    direct = _topics(evidence.quote)
    result = {'source_id': evidence.source_id, 'topics': sorted(direct), 'antecedent': None}
    # Inheritance is only for a literal generic measure in a unique source
    # substring. Arbitrary category text or synonyms are not silently resolved.
    generic = {t for t in direct if '_' not in t}
    if not generic or any('_' in t for t in direct):
        return result
    text = sources.get(evidence.source_id, {}).get('content', '')
    if not isinstance(text, str) or text.count(evidence.quote) != 1:
        return result
    start = text.index(evidence.quote)
    paragraph = text.rfind('\n\n', 0, start)
    lower = max(0, start - 800, paragraph + 2 if paragraph >= 0 else 0)
    mentions = list(_mentions(text[lower:start]))
    if not mentions:
        return result
    for topic, left, right in reversed(mentions):
        if _family(topic) not in generic:
            break
        if '_' in topic:
            result['topics'] = sorted((direct - {_family(topic)}) | {topic})
            result['antecedent'] = {'start': lower + left, 'end': lower + right,
                                    'text': text[lower + left:lower + right]}
            break
    return result


def topic_evidence(component, sources, question=None):
    """Assess known subjects; no missing state, repair, or new evidence is made."""
    requested = _requested(component, question)
    evidence = [_quote_topics(e, sources) for e in component.evidence]
    found = set().union(*(set(e['topics']) for e in evidence))
    matched = {wanted for wanted in requested if any(_matches(t, wanted) for t in found)}
    unresolved = sorted(requested - matched)
    check = {'status': 'unknown', 'reason': 'subject_not_established', 'requested_subjects': sorted(requested),
             'unresolved_subjects': unresolved, 'evidence': evidence}
    if (_CAUSAL_REQUEST.search(component.question_anchor)
            and component.evidence and all(_DEFINITION.search(e.quote) and not _CAUSE.search(e.quote)
                                            for e in component.evidence)):
        return {**check, 'status': 'incompatible', 'reason': 'definition_only_for_causal_request'}
    if requested and found and not matched and all(_different(t, w) for t in found for w in requested):
        return {**check, 'status': 'incompatible', 'reason': 'known_different_requested_subject'}
    # A compound supported answer cannot be complete with only one known
    # requested subject. Unknown evidence prevents this narrow conclusion.
    if (len(requested) > 1 and matched and unresolved and component.status == 'supported'
            and all(e['topics'] for e in evidence)
            and all(any(_different(t, w) for t in found) and
                    not any(_family(t) == _family(w) and '_' not in t for t in found) for w in unresolved)):
        return {**check, 'status': 'incompatible', 'reason': 'supported_component_omits_known_requested_subject'}
    if matched:
        return {**check, 'status': 'compatible', 'reason': 'literal_or_bounded_requested_subject'}
    return check


def reject_topic_mismatches(checks):
    if any(c['status'] == 'incompatible' for c in checks.values()):
        raise ValueError('Selected evidence does not establish the requested subject or explanation')


def focused_choices(catalog,sources,anchor,candidates,eligible,require_details=False):
    """Bound choices by source structure, not a claim that excluded facts are absent."""
    wanted=_topics(anchor);primary={};limits={}
    if len(wanted) != 1 or '_' not in next(iter(wanted)):
        return ([candidates] if candidates else []), list(eligible), {
            'primary_source_ids': [], 'excluded_ids': [], 'absence_established': False,
            'policy': 'qualified-subject-focus-v2', 'applied': False,
            'reason': 'unqualified or ambiguous subject; no primary-record preference'}
    for sid in candidates:
        span=catalog[sid];source_id=span['source_id'];text=sources[source_id]['content']
        spans=sorted(((s,v) for s,v in catalog.items() if v['source_id']==source_id),key=lambda p:p[1]['start'])
        first_id,first=spans[0];subject=_primary_subject(first['text'])
        if (first['start']!=len(text)-len(text.lstrip()) or subject is None
                or not any(_matches(subject,w) for w in wanted)):
            continue
        end=len(text)
        paragraph=re.search(r'\r?\n[ \t]*\r?\n',text[first['start']:])
        if paragraph:end=min(end,first['start']+paragraph.start())
        for other_id,other in spans[1:]:
            topics=_topics(other['text'])
            if topics and all(_different(t,subject) for t in topics):
                end=min(end,other['start']);break
        primary[source_id]=first_id;limits[source_id]=end
    preferred=[s for s in candidates if catalog[s]['source_id'] in primary
               and catalog[s]['end']<=limits[catalog[s]['source_id']]]
    if preferred:
        if not require_details:
            roots=[s for s in preferred if s in primary.values()]
            preferred=roots or preferred
        groups={}
        for sid in preferred:groups.setdefault(catalog[sid]['text'],[]).append(sid)
        required=list(groups.values()) if require_details else [preferred]
        extras=[s for s in eligible if s in preferred or (catalog[s]['source_id'] in primary
            and catalog[s]['end']<=limits[catalog[s]['source_id']]
            and not _topics(catalog[s]['text']))]
    else:
        required=[candidates] if candidates else []
        extras=list(candidates)
        for sid in eligible:
            span=catalog[sid]
            if sid in extras or _topics(span['text']) or not _CAUSAL_ANAPHOR.search(span['text']):continue
            for parent_id in candidates:
                parent=catalog[parent_id]
                if parent['source_id']!=span['source_id'] or parent['end']>=span['start']:continue
                gap=sources[span['source_id']]['content'][parent['end']:span['start']]
                if gap.isspace() and not re.search(r'\r?\n[ \t]*\r?\n',gap):
                    extras.append(sid);break
    if len(required)>5:
        raise ValueError('Focused evidence exceeds five mapped quotations; narrow the request')
    return required,extras,{'primary_source_ids':list(primary),'excluded_ids':[s for s in eligible if s not in extras],
                            'absence_established':False,'policy':'qualified-subject-focus-v2','applied':True}


def topic_views(catalog, sources, requests, diagnostics=None):
    """Offer matching qualified subjects; bare topic words never force evidence.

    Existing higher-priority view contracts win at the integration boundary.
    For a causal question prefer matching explicit explanations when present.
    Institutional names may contain unqualified investment/consumption/inflation
    words; these remain untyped mapper choices rather than compulsory roots.
    """
    views = {}
    for request in requests:
        requested_topics = _topics(request['question_anchor'])
        if len(requested_topics) != 1 or '_' not in next(iter(requested_topics)):
            continue
        candidates, causal, complete, eligible = [], [], [], []
        for sid, span in catalog.items():
            if _COMMAND.search(span['text']):
                continue
            component = SimpleNamespace(question_anchor=request['question_anchor'], status='partial',
                evidence=[SimpleNamespace(source_id=span['source_id'], quote=span['text'])])
            check = topic_evidence(component, sources)
            if check['status'] != 'incompatible':
                eligible.append(sid)
            if check['status'] == 'compatible':
                candidates.append(sid)
                if _CAUSE.search(span['text']) and not _DEFINITION.search(span['text']):
                    causal.append(sid)
                    if span.get('continuation_members'):
                        complete.append(sid)
        selected = (complete or causal) if causal and _CAUSAL_REQUEST.search(request['question_anchor']) else candidates
        if selected:
            groups,extras,trace=focused_choices(catalog,sources,request['question_anchor'],selected,eligible,
                bool(_DETAIL_REQUEST.search(request['question_anchor']+' '+request.get('instruction',''))))
            views[request['component_id']] = [{'role':'requested_financial_subject','span_ids':group,
                'extra_span_ids':extras,'allow_extra':True} for group in groups]
            if diagnostics is not None:diagnostics[request['component_id']]=trace
    return views


def validate_claim_topic(text, component, question=None):
    """A claim may cover a subset of a compound request, never switch known topics."""
    requested, actual = _requested(component, question), _topics(text)
    if requested and actual and all(_different(t, w) for t in actual for w in requested):
        raise ValueError('Draft substitutes a different requested subject')
