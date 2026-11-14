"""Canonical verbatim request slots, without inferring entities or evidence."""
import re
from src.utils._periods import explicit_periods


_COMPARE = re.compile(r'^How (?:did|does|do) (?P<subject>.+?) (?:compare|differ) '
    r'(?P<monthly>month-on-month\b.*?)\s+and\s+(?P<quarterly>quarter-on-quarter\b.*)$', re.I)
_ANAPHOR = re.compile(r'^(?:which|what) categories\b.*\b(?:those|these|their) (?:directions|changes|movements)\b', re.I)
_VALUE_COUNT = re.compile(r'\bwhat\s+(?:(?:was|were|is|are)\s+(?:the\s+)?)?'
    r'(?P<value>value)\s+and\s+(?P<count>project\s+count|number\s+of\s+projects)\b', re.I)
_EACH_CHANGE = re.compile(r'^how\s+(?:did|does|do)\s+(?:each|both)\s+change\b', re.I)


def _quantity_requests(requests):
    """Separate explicit value/count tasks, without guessing other noun pairs.

    The original clauses remain the retrieval queries. Private mapping slots
    each classify one measure/task, including an explicit each-change clause;
    this establishes structural coverage, not correct factual extraction.
    """
    if len(requests) not in {1, 2}:
        return None
    first = requests[0]['question_anchor']
    pair = _VALUE_COUNT.search(first)
    if pair is None or (len(requests) == 2 and not _EACH_CHANGE.search(requests[1]['question_anchor'])):
        return None
    protected = [m.span() for m in re.finditer(r'"[^"\n]*"|(?<!\w)\'[^\'\n]*\'(?!\w)|\([^()]*\)', first)]
    if any(left <= pair.start() < right for left, right in protected):
        return None
    result = []
    for task in (['level', 'change'] if len(requests) == 2 else ['level']):
        for measure in ('value', 'count'):
            anchor = pair[measure] if task == 'level' else requests[1]['question_anchor']
            label = pair[measure]
            result.append({'component_id': f'r{len(result) + 1}', 'question_anchor': anchor,
                'quantity_measure': measure, 'quantity_label': label, 'quantity_task': task,
                'instruction': f"Answer only the {'reported ' + label if task == 'level' else 'change in ' + label}; "
                    "use the original question's subject, scope and comparison period. "
                    "Give its own supporting spans or classify its specific gap explicitly. "
                    "Another measure's answer or evidence cannot fill this slot."})
    return result


def _ordinary_requests(question):
    text = question.strip()
    if not text:
        raise ValueError("A nonempty question is required")
    compound = re.search(r"^How did\s+(?P<subjects>.+?)\s+change\b.+?\bwhich activities supported them\??$", text, re.I)
    if compound and not any(c in compound["subjects"] for c in "\"'()"):
        subjects = re.split(r"\s+and\s+", compound["subjects"], flags=re.I)
        if len(subjects) == 2:
            return [{"component_id": f"r{i}", "question_anchor": subject,
                "instruction": "Answer both the change and all requested supporting activities for this subject, using the original question's scope."}
                for i, subject in enumerate(subjects, 1)]
    # Split only explicit new question clauses. A comma before the first question
    # belongs to its introductory scope, not an independent answer component.
    interrogative = r"(?:what|which|how|why|when|where|who|did|does|do|is|are|was|were|has|have|can|could)\b"
    separator = re.compile(r",?\s+\b(?:and|but)\s+(?=" + interrogative + r")"
        r"|(?<=\?)\s+(?=" + interrogative + r")|,\s+(?=" + interrogative + r")", re.I)
    protected = [m.span() for m in re.finditer(r'"[^"\n]*"|(?<!\w)\'[^\'\n]*\'(?!\w)|\([^()]*\)', text)]
    parts, start = [], 0
    for match in separator.finditer(text):
        if any(left <= match.start() < right for left, right in protected):
            continue
        left = text[start:match.start()].strip(" ,")
        if not re.search(r"\b" + interrogative, left, re.I):
            continue
        parts.append(left)
        start = match.end()
    parts.append(text[start:].strip(" ,"))
    if len(parts) > 5:
        parts = [text]  # Keep the whole request rather than silently dropping clauses.
    return [{"component_id": f"r{index}", "question_anchor": part} for index, part in enumerate(parts, 1)]


def requested_components(question):
    requests = _ordinary_requests(question)
    quantities = _quantity_requests(requests)
    if quantities is not None:
        return quantities
    match = _COMPARE.fullmatch(requests[0]['question_anchor'])
    if (match and len(requests) <= 2 and (len(requests)==1 or _ANAPHOR.search(requests[1]['question_anchor']))):
        detail = ' and all requested categories' if len(requests)==2 else ''
        return [{'component_id':f'r{i}', 'question_anchor':match[role].rstrip('?').strip(),
            'comparison_role':role, 'comparison_subject':match['subject'],
            'instruction':f"Answer the direction{detail} for {match['subject']} in this comparison period."}
            for i,role in enumerate(('monthly','quarterly'),1)]
    return requests


def requested_periods(anchor, question):
    """An explicit quarterly slot does not inherit another slot's monthly date."""
    own = explicit_periods(anchor)
    quarterly = bool(re.search(r'\bquarter\b|\bquarterly\b',anchor,re.I))
    return own or ([] if quarterly else explicit_periods(question))


def retrieval_facets(question):
    ordinary = _ordinary_requests(question)
    quantities = _quantity_requests(ordinary)
    if quantities is not None:
        # Keep the pre-existing query text, facet count/order and ranking. Only
        # the trace of which mapping slots each original clause covers changes.
        return [{'component_id': request['component_id'],
                 'covers_components': [q['component_id'] for q in quantities
                    if q['quantity_task'] == ('level' if i == 0 else 'change')],
                 'query': request['question_anchor'], 'role': 'request'}
                for i, request in enumerate(ordinary)]
    facets=[]
    for request in requested_components(question):
        role=request.get('comparison_role','request')
        query=(request['comparison_subject']+' '+request['question_anchor']
               if role!='request' else request['question_anchor'])
        facets.append({'component_id':request['component_id'],'covers_components':[request['component_id']],
                       'query':query,'role':role})
    return facets
