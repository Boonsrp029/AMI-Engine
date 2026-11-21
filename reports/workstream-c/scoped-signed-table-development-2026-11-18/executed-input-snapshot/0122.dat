"""Retain bounded category/causal windows as exact, contiguous source quotations.

Adjacency and literal discourse cues establish a traceable reading window, not
semantic entailment. No source records are joined and no text is synthesized.
"""
import hashlib
import re

from src.pilot._topics import _CAUSAL_REQUEST, _CAUSE, _topics, _matches, _family, _primary_subject, _DETAIL_REQUEST, _CAUSAL_ANAPHOR
from src.utils._periods import _COMMAND


CONTINUATION_VERSION = 'bounded-source-windows-v2'
_PARAGRAPH = re.compile(r'\r?\n[ \t]*\r?\n')


def _verify(span, sources):
    text = sources.get(span['source_id'], {}).get('content', '')
    if (not isinstance(text, str) or not 0 <= span['start'] < span['end'] <= len(text)
            or text[span['start']:span['end']] != span['text']
            or hashlib.sha256(text.encode()).hexdigest() != span['content_sha256']):
        raise ValueError('Causal span provenance does not match source content')
    return text


def complete_causal_spans(question, catalog, sources):
    """Replace adjacent subject/cue-linked spans with one <=600-character substring.

    Only a single literal requested subject can introduce a continuation. New
    subjects, paragraphs, source IDs, command-shaped content and unrecognized
    links are never bridged. Unjoined source spans remain in the catalog.
    """
    trace = {'policy': CONTINUATION_VERSION, 'joined': [], 'unjoined': []}
    if not (_CAUSAL_REQUEST.search(question) or _DETAIL_REQUEST.search(question)):
        return dict(catalog), trace
    requested = _topics(question)
    by_source = {}
    for sid, span in catalog.items():
        _verify(span, sources)
        by_source.setdefault(span['source_id'], []).append((sid, span))
    replacements, removed = {}, set()
    for source_id, spans in by_source.items():
        spans.sort(key=lambda pair: pair[1]['start'])
        text = sources[source_id]['content']
        if _COMMAND.search(text):
            continue  # Untrusted instructions are not promoted into reading windows.
        for i, (sid, parent) in enumerate(spans):
            if sid in removed:
                continue
            subject=_primary_subject(parent['text'])
            if subject is None or not any(_matches(subject,t) for t in requested):
                continue
            subjects={subject}
            end, members = parent['end'], [{'span_id': sid, 'start': parent['start'], 'end': parent['end']}]
            for child_id, child in spans[i+1:]:
                gap = text[end:child['start']]
                if child['start'] < end or not gap.isspace() or _PARAGRAPH.search(gap):
                    break
                child_topics = _topics(child['text'])
                category=(_family(subject) in {'investment','consumption'} and child_topics
                    and all(t in {subject,_family(subject)} for t in child_topics))
                if not category and not (_CAUSAL_ANAPHOR.search(child['text']) and _CAUSE.search(child['text'])):
                    break
                if any(not any(_matches(t, s) or _matches(s, t) for s in subjects) for t in child_topics):
                    break
                if child['end'] - parent['start'] > 600:
                    trace['unjoined'].append({'parent_id': sid, 'continuation_id': child_id, 'reason': 'quotation_limit'})
                    break
                end = child['end']
                members.append({'span_id': child_id, 'start': child['start'], 'end': child['end']})
                removed.add(child_id)
            if len(members) > 1:
                key = f"{source_id}\0{parent['content_sha256']}\0{parent['start']}\0{end}"
                new_id = 's_' + hashlib.sha256(key.encode()).hexdigest()[:16]
                if new_id in catalog or any(new_id == item[0] for item in replacements.values()):
                    raise ValueError('Causal span identity collision')
                replacements[sid] = (new_id, {**parent, 'end': end, 'text': text[parent['start']:end],
                                             'continuation_members': members})
                trace['joined'].append({'span_id': new_id, 'source_id': source_id,
                    'content_sha256': parent['content_sha256'], 'start': parent['start'], 'end': end,
                    'member_ids': [m['span_id'] for m in members]})
    result = {}
    for sid, span in catalog.items():
        if sid in replacements:
            new_id, combined = replacements[sid]
            result[new_id] = combined
        elif sid not in removed:
            result[sid] = span
    return result, trace
