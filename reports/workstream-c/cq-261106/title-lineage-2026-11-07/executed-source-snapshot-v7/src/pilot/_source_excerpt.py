"""Conservative labeled presentation; original selected quotations stay intact."""
from datetime import date
import hashlib
import re

from src.pilot._financial_coverage import _spec, financial_context_omissions
from src.pilot._requests import requested_components
from src.pilot._scope import same_pinned_document
from src.utils._periods import _COMMAND, _MONTHS

_NUMBER = re.compile(r'^\d{1,8}(?:[/.-]\d{1,8})?(?:\s+\([A-Za-z0-9. -]{1,12}\))?\s+')
_NAME = r"(?:[A-Z][A-Za-z'’\-]*|\([A-Z][A-Z0-9.]{0,15}\))"
_BODY = re.compile(r'\bThe\s+(?!The\b)[A-Z][A-Za-z\-]*'
    r'(?:\s+(?:(?!The\b)' + _NAME + r'|of|the|and|for)){0,14}'
    r'\s+(?:said|reported|announced)\s+(?:today\s+)?that\b')
_UNSAFE = re.compile(r'\b(?:not|no|never|denied|denies|false|alleged|disputed|unless|if|except|'
    r'claims?|quoted?|forecast\w*|expected|projected|scenario|would|could|correction|retract\w*)\b', re.I)
_REQUESTED_HEADER = re.compile(r'\b(?:publish\w*|publication|release\w*|dateline|headline|issuer|who|when)\b|'
    r'\breport\s+(?:number|date)\b', re.I)


def render_fallback_excerpt(evidence, sources, question):
    """Return original text unless a small, explicit release structure is proven.

    This is not semantic header classification. Source identity, uniqueness,
    publication date and exact retained character ranges must all be available.
    Labels disclose publication context without changing relative source words.
    """
    original = ' '.join(e.quote for e in evidence)
    if (_spec(question, requested_components(question)) is None or _REQUESTED_HEADER.search(question)
            or not evidence or not isinstance(sources, dict)):
        return original, None
    records = [sources.get(e.source_id) for e in evidence]
    if any(not isinstance(s, dict) for s in records):
        return original, None
    if any(not same_pinned_document(records[0], s) for s in records):
        return original, None
    published = records[0].get('published')
    if not isinstance(published, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', published):
        return original, None
    try:
        publication = date.fromisoformat(published)
    except ValueError:
        return original, None
    label = f'{publication.day} {_MONTHS.split()[publication.month-1]} {publication.year}'
    pieces, proof, trimmed = [], [], 0
    for e, record in zip(evidence, records, strict=True):
        content = record.get('content')
        if not isinstance(content, str) or content.count(e.quote) != 1 or _COMMAND.search(content):
            return original, None
        offset = content.index(e.quote)
        body, removed = e.quote, 0
        number = _NUMBER.match(e.quote)
        if number and re.search(r'PRESS RELEASE No\.\s*$', content[:offset], re.I):
            matches = list(_BODY.finditer(e.quote))
            if len(matches) != 1:
                return original, None
            removed = matches[0].start()
            prefix = e.quote[:removed]
            if (not 0 < removed <= 300 or not prefix[number.end():].startswith(label+' ')
                    or _UNSAFE.search(prefix)):
                return original, None
            body = e.quote[removed:]
            trimmed += 1
        pieces.append(body)
        proof.append({'source_id':e.source_id, 'source_start':offset+removed,
            'source_end':offset+len(e.quote), 'quote_start':offset,
            'original_quote_sha256':hashlib.sha256(e.quote.encode('utf-8')).hexdigest(),
            'source_content_sha256':hashlib.sha256(content.encode('utf-8')).hexdigest(),
            'removed_prefix_characters':removed})
    if trimmed != 1:
        return original, None
    rendered = f'Source excerpt, published {label}: ' + ' '.join(f'“{body}”' for body in pieces)
    if len(rendered) > 800 or any(financial_context_omissions(rendered,evidence,
            {'quantity_measure':measure},question) for measure in ('value','count')):
        return original, None
    return rendered, {'origin':'application-labeled-exact-source-excerpt',
        'published':published, 'publication_label':label, 'publication_context_not_measurement_date':True,
        'original_selected_quotes_unchanged':True, 'pieces':proof}


def render_fallback_prose(evidence, sources, question):
    """Reframe only a proven issuer/measurement statement as attributed prose.

    The older excerpt formatter establishes release identity and exact body
    ranges; its dated/quoted display is not returned. A measurement year must
    occur in the explicit application-value statement, never just the header.
    Unsupported syntax retains the original selected text for review. This is
    bounded presentation, not a general paraphraser or semantic support check.
    """
    original = ' '.join(e.quote for e in evidence)
    _, proof = render_fallback_excerpt(evidence, sources, question)
    if proof is None:
        return original, None
    pieces = [sources[p['source_id']]['content'][p['source_start']:p['source_end']]
              for p in proof['pieces']]
    starts = [i for i,p in enumerate(proof['pieces']) if p['removed_prefix_characters']]
    index = starts[0]
    body = pieces[index]
    attribution = _BODY.match(body)
    if attribution is None:
        return original, None
    reporting = re.search(r'\s+(?:said|reported|announced)\s+(?:today\s+)?that$', attribution[0])
    if reporting is None:
        return original, None
    issuer = attribution[0][:reporting.start()]
    statement = body[attribution.end():].strip()
    measurement = re.fullmatch(r'applications for investment promotion in (?P<year>\d{4})\s+(?P<facts>.+)',
                               statement, re.S)
    spec = _spec(question, requested_components(question))
    if (measurement is None or measurement['year'] != spec['current'] or _UNSAFE.search(statement)
            or not re.search(r'\b(?:baht|USD)\b', statement)):
        return original, None
    # Keep the measurement year inside its source clause. Moving it before
    # "issuer reported" would incorrectly date the act of reporting.
    pieces[index] = issuer + ' reported that ' + statement
    rendered = ' '.join(pieces)
    if len(rendered) > 800 or any(financial_context_omissions(rendered, evidence,
            {'quantity_measure': measure}, question) for measure in ('value', 'count')):
        return original, None
    after_attribution = body[attribution.end():]
    clause_offset = attribution.end() + len(after_attribution) - len(after_attribution.lstrip())
    return rendered, {**proof, 'origin':'application-source-attributed-prose',
        'presentation':'source-attributed prose; original measurement clause unchanged',
        'measurement_year':measurement['year'], 'reporting_attribution':issuer,
        'reporting_prefix_original':body[:clause_offset],
        'reporting_prefix_rendered':issuer + ' reported that ',
        'factual_clause':{'source_id':proof['pieces'][index]['source_id'],
            'source_start':proof['pieces'][index]['source_start'] + clause_offset,
            'source_end':proof['pieces'][index]['source_start'] + clause_offset + len(statement),
            'sha256':hashlib.sha256(statement.encode('utf-8')).hexdigest()},
        'relative_reporting_word_removed':bool(re.search(r'\btoday\b', attribution[0])),
        'dated_excerpt_display_used':False, 'semantic_support_proven':False}
