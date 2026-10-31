"""Literal binary project-count coverage; not general entity resolution/entailment."""
import re
from decimal import Decimal

from src.pilot._requests import requested_components
from src.pilot._scope import same_pinned_document, measurement_periods
from src.utils._periods import _COMMAND


_NAME = r"[^\W\d_]+(?:[- ][^\W\d_]+){0,4}"
_REQUEST = re.compile(r'^(?:did|does|do)\s+(?P<left>' + _NAME + r')\s+or\s+'
    r'(?P<right>' + _NAME + r')\s+have\s+(?P<direction>more|fewer|less)\s+projects?\b'
    r'(?:\s+(?:in|for|during)\s+(?:19|20|21)\d{2})?(?=\s*(?:[?.]|$))', re.I)
_COUNT = re.compile(r'(?<![\w.,+-])(?P<value>\d{1,3}(?:,\d{3})+|\d+)\s+projects?\b', re.I)
_LINK = re.compile(r"(?:|:|'s|(?:had|has|filed|recorded|reported|submitted)(?:\s+(?:a total of|totaling|totalling))?"
    r"|(?:had|has)\s+(?:more|fewer|less)\s+projects?:"
    r"|(?:led|leads)\s+the\s+(?:FDI\s+)?source\s+rankings\s+with"
    r"|(?:was|is)\s+the\s+(?:(?:second|third|fourth|fifth)\s+largest|largest|leading)"
    r"\s+source\s+of\s+(?:FDI\s+)?applications\s+with)", re.I)
_ELLIPTICAL_RELATION = re.compile(r'(?:had|has|have)\s+(?:more|fewer|less|same)(?:\s+than)?', re.I)


def request_spec(anchor):
    match = _REQUEST.match(anchor)
    if not match:
        return None
    entities = [match['left'], match['right']]
    if (entities[0].casefold() == entities[1].casefold()
            or any(re.search(r'\bor\b', name, re.I) for name in entities)):
        return None
    return {'entities': entities, 'direction': 'more' if match['direction'].lower() == 'more' else 'fewer',
            'measure': 'project_count'}


def decorate_requests(requests):
    result = []
    for request in requests:
        spec = request_spec(request['question_anchor'])
        result.append({**request, 'entity_comparison': spec,
            'instruction': 'Compare these two entities using their own project counts. Select evidence for both; '
                'a nationality or regional-base statement is not count evidence. State the answer, or classify '
                'the unresolved comparison explicitly.'} if spec else request)
    return result


def _literal(entity):
    return re.compile(r'(?<!\w)' + re.escape(entity) + r'(?!\w)', re.I)


def linked_counts(text, entities):
    """Bind only literal entity-before-count clauses with declared predicates.

    No nationality aliases, application/project synonyms, tables, implicit units,
    arbitrary subject inference or cross-sentence association are introduced.
    """
    result = {name: set() for name in entities}
    if _COMMAND.search(text):
        return result
    for entity in entities:
        other = next(name for name in entities if name != entity)
        for occurrence in _literal(entity).finditer(text):
            tail = text[occurrence.end():occurrence.end() + 220]
            tail = re.split(r'[;!?\n]|\.(?:\s|$)', tail, maxsplit=1)[0]
            next_entity = _literal(other).search(tail)
            if next_entity:
                tail = tail[:next_entity.start()]
            for count in _COUNT.finditer(tail):
                if _LINK.fullmatch(tail[:count.start()].strip()):
                    result[entity].add(Decimal(count['value'].replace(',', '')))
    return result


def _selected_counts(component, spec):
    values = {name: set() for name in spec['entities']}
    roles, unused = {name: [] for name in spec['entities']}, []
    periods = []
    for evidence in component.evidence:
        linked = linked_counts(evidence.quote, spec['entities'])
        if not any(linked.values()):
            unused.append(evidence.source_id)
        for name, counts in linked.items():
            values[name].update(counts)
            if counts:
                roles[name].append(evidence.source_id)
        dates = set(measurement_periods(evidence.quote))
        if not re.search(r'\b(?:published|publication|released|release|issued|dated)\b', evidence.quote, re.I):
            dates.update(m.group(1) for m in re.finditer(r'\b(?:in|for|during)\s+((?:19|20|21)\d{2})\b', evidence.quote, re.I))
        if dates:
            periods.append(dates)
    return values, roles, unused, periods


def evidence_views(catalog, requests):
    result = {}
    for request in requests:
        spec = request_spec(request['question_anchor'])
        if not spec:
            continue
        roles = {name: [sid for sid, span in catalog.items() if linked_counts(span['text'], spec['entities'])[name]]
                 for name in spec['entities']}
        groups = [ids for ids in roles.values() if ids]
        # A shared span may prove both roles once. Do not force repeated IDs to
        # satisfy positional views; post-selection validation checks both roles.
        if len(groups) == 2 and set(groups[0]) & set(groups[1]):
            continue
        if groups:
            competing = any(len(set().union(*(linked_counts(catalog[sid]['text'], spec['entities'])[name]
                for sid in ids))) > 1 for name, ids in roles.items() if ids)
            extras = list(dict.fromkeys(sid for ids in roles.values() for sid in ids))
            result[request['component_id']] = [{'role': 'project_count_for_' + name,
                'span_ids': ids, 'allow_extra': competing,
                **({'extra_span_ids': extras} if competing else {})}
                for name, ids in roles.items() if ids]
    return result


def validate_mapping_comparisons(mapping, question, sources):
    specs = {r['component_id']: request_spec(r['question_anchor']) for r in requested_components(question)}
    checks = {}
    for component in mapping.components:
        spec = specs.get(component.component_id)
        if not spec or component.status not in {'supported', 'partial', 'conflicting'}:
            continue
        values, roles, unused, periods = _selected_counts(component, spec)
        if component.status == 'conflicting':
            # Different counts for different entities answer a comparison; they
            # do not by themselves demonstrate conflicting evidence. Reject the
            # unsupported state, never fill an answer or relabel it supported.
            # Extra non-count context, competing counts, differing explicit
            # periods or document identities stay unresolved for source review.
            ids = list(dict.fromkeys(s for matches in roles.values() for s in matches))
            consistent = (all(len(v) == 1 for v in values.values()) and not unused and bool(ids)
                and all(sid == ids[0] or same_pinned_document(sources[ids[0]], sources[sid]) for sid in ids)
                and not any(len(p) > 1 for p in periods)
                and not any(p != periods[0] for p in periods[1:]))
            if consistent:
                raise ValueError('Project comparison marks consistent entity counts as conflicting without conflict evidence')
            continue
        if unused:
            raise ValueError('Project comparison selects background without requested entity/count evidence')
        if any(len(v) > 1 for v in values.values()):
            raise ValueError('Project comparison has ambiguous selected entity counts')
        if periods and (any(len(p) > 1 for p in periods) or any(p != periods[0] for p in periods[1:])):
            raise ValueError('Project comparison selects explicitly different reporting periods')
        ids = list(dict.fromkeys(s for matches in roles.values() for s in matches))
        if ids and any(sid != ids[0] and not same_pinned_document(sources[ids[0]], sources[sid]) for sid in ids):
            raise ValueError('Project comparison lacks shared pinned document identity')
        complete = all(len(v) == 1 for v in values.values())
        if component.status == 'supported' and not complete:
            raise ValueError('Supported project comparison requires one selected count for each entity')
        if not complete and (component.short_answer.strip(' .').casefold() in {n.casefold() for n in spec['entities']}
                             or re.search(r'\b(?:more|fewer|less)\s+projects?\b', component.short_answer, re.I)):
            raise ValueError('Partial project evidence cannot establish a comparison winner')
        if complete:
            _validate_winner(component.short_answer, spec, values)
        checks[component.component_id] = {'status': 'complete_literal_roles' if complete else 'partial_literal_roles',
            'counts': {name: [str(v) for v in sorted(counts)] for name, counts in values.items()},
            'source_ids_by_entity': roles, 'semantic_support_proven': False,
            'scope_note': 'Literal count/document checks; unknown date/scope and source truth still require review.'}
    return checks


def _validate_winner(text, spec, values):
    left, right = spec['entities']
    numbers = {name: next(iter(values[name])) for name in (left, right)}
    expected = None if numbers[left] == numbers[right] else (
        max(numbers, key=numbers.get) if spec['direction'] == 'more' else min(numbers, key=numbers.get))
    exact = text.strip(' .').casefold()
    if exact in {left.casefold(), right.casefold()} and (expected is None or exact != expected.casefold()):
        raise ValueError('Project comparison names a winner inconsistent with selected counts')
    for entity, relation in _literal_relations(text, spec):
        other = right if entity == left else left
        delta = numbers[entity] - numbers[other]
        valid = delta == 0 if relation == 'same' else (
            delta > 0 if relation == 'more' else delta < 0)
        if not valid:
            raise ValueError('Project comparison relation contradicts selected counts')


def _literal_relations(text, spec):
    left, right = spec['entities']
    for entity in (left, right):
        other = right if entity == left else left
        for occurrence in _literal(entity).finditer(text):
            tail = re.split(r'[;!?\n]|\.(?:\s|$)', text[occurrence.end():], maxsplit=1)[0]
            match = _literal(other).search(tail)
            if match:
                tail = tail[:match.start()]
            if (not re.search(r'\bprojects?\b', tail, re.I)
                    and not _ELLIPTICAL_RELATION.fullmatch(tail.strip())):
                continue
            relation = re.search(r'\b(more|fewer|less|same)\b', tail, re.I)
            if relation:
                yield entity, relation[1].lower()


def validate_composed_comparison(text, component):
    spec = request_spec(component.question_anchor)
    if not spec or component.status not in {'supported', 'partial'}:
        return
    values, _, _, _ = _selected_counts(component, spec)
    complete = all(len(v) == 1 for v in values.values())
    if component.status == 'supported':
        actual = linked_counts(text, spec['entities'])
        if not complete or actual != values:
            raise ValueError('Draft project comparison omits or swaps requested entity/count facts')
    if complete:
        _validate_winner(text, spec, values)
    elif re.search(r'\b(?:more|fewer|less)\s+projects?\b', text, re.I):
        raise ValueError('Draft partial project evidence cannot establish a winner')


def missing_comparison_conclusion(text, component):
    """Derive a missing literal count conclusion; never repair incorrect facts."""
    spec = request_spec(component.question_anchor)
    if not spec or component.status != 'supported':
        return None
    validate_composed_comparison(text, component)
    values, roles, unused, periods = _selected_counts(component, spec)
    if (unused or any(len(p) > 1 for p in periods)
            or any(p != periods[0] for p in periods[1:])):
        raise ValueError('Project conclusion requires compatible literal count evidence')
    numbers = {name: next(iter(counts)) for name, counts in values.items()}
    relations = list(_literal_relations(text, spec))
    if len(set(numbers.values())) == 1:
        if any(relation == 'same' for _, relation in relations) or re.search(
                r'\bboth\s+had\s+the\s+same\s+number\s+of\s+projects\b', text, re.I):
            return None
        clause = 'Both had the same number of projects.'
    else:
        winner = (max if spec['direction'] == 'more' else min)(numbers, key=numbers.get)
        if any(entity == winner and ('fewer' if relation == 'less' else relation) == spec['direction']
               for entity, relation in relations):
            return None
        clause = f"{winner} had {spec['direction']} projects."
    return {'clause': clause, 'counts': {name: str(count) for name, count in numbers.items()},
        'source_ids_by_entity': roles, 'operation': 'compare_literal_project_counts',
        'semantic_support_proven': False}


def render_literal_comparison(component, sources):
    """Render a narrow source operation, never repair a model-written claim.

    Unknown period/geography stays unknown. Shared document identity and literal
    counts are necessary checks, not proof of semantic or temporal applicability.
    """
    spec = request_spec(component.question_anchor)
    if not spec or component.status != 'supported':
        return None
    tail = component.question_anchor[_REQUEST.match(component.question_anchor).end():]
    if not re.fullmatch(r'[?.\s]*(?:Keep (?:the )?percentage denominators clear[.!]?)?\s*', tail, re.I):
        return None  # A further cause/measure request must not be discarded.
    quoted = ' '.join(e.quote for e in component.evidence)
    if re.search(r'\b(?:forecast|projected|expected|scenario|STEPS|APS|NZE|would|could|might|target)\b', quoted, re.I):
        return None
    values, roles, unused, periods = _selected_counts(component, spec)
    if unused or any(len(counts) != 1 for counts in values.values()):
        raise ValueError('Literal project rendering requires one unambiguous count per entity')
    if any(len(period) > 1 for period in periods) or any(p != periods[0] for p in periods[1:]):
        raise ValueError('Literal project rendering requires compatible explicit periods')
    if periods:
        for evidence in component.evidence:
            counts, _, _, own_periods = _selected_counts(
                component.model_copy(update={'evidence': [evidence]}), spec)
            if any(counts.values()) and not own_periods:
                return None  # Do not extend one quotation's year to another.
    requested_year = re.search(r'\b(?:in|for|during)\s+((?:19|20|21)\d{2})\b',
        component.question_anchor[:_REQUEST.match(component.question_anchor).end()], re.I)
    if requested_year and (not periods or not all(any(re.search(
            r'(?<!\d)' + requested_year[1] + r'(?!\d)', date) for date in period) for period in periods)):
        return None
    ids = list(dict.fromkeys(e.source_id for e in component.evidence))
    if not ids or any(sid not in sources for sid in ids):
        raise ValueError('Literal project rendering references an unknown source')
    if any(not same_pinned_document(sources[ids[0]], sources[sid]) for sid in ids):
        raise ValueError('Literal project rendering requires shared pinned document identity')
    for evidence in component.evidence:
        quote = ' '.join(evidence.quote.split())
        if not quote or quote not in ' '.join(sources[evidence.source_id].get('content', '').split()):
            raise ValueError('Literal project rendering quotation does not match its source')
    # A wrong mapper summary also remains a failure; it is not silently fixed.
    actual = linked_counts(component.short_answer, spec['entities'])
    if any(counts and counts != values[name] for name, counts in actual.items()):
        raise ValueError('Mapped project counts contradict selected source operands')
    _validate_winner(component.short_answer, spec, values)
    numbers = {name: next(iter(counts)) for name, counts in values.items()}
    text = '; '.join(f'{name} had {count:f} projects' for name, count in numbers.items()) + '.'
    conclusion = missing_comparison_conclusion(text, component)
    if conclusion:
        text += ' ' + conclusion['clause']
    if len(text) > 800:
        raise ValueError('Literal project rendering exceeds the claim limit')
    validate_composed_comparison(text, component)
    return {'text': text, 'counts': {name: str(count) for name, count in numbers.items()},
        'source_ids_by_entity': roles, 'operation': 'render_literal_project_comparison',
        'model_generated': False, 'semantic_support_proven': False,
        'scope_note': 'No date/geography inferred; unresolved scope still requires review.'}
