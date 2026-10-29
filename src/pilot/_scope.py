"""Conservative scope propagation; phrase occurrence is not semantic entailment."""

import re
from decimal import Decimal
from src.utils._periods import _MONTHS, _PERIOD, explicit_periods
from src.pilot._quantities import validate_quantity_roles
from src.pilot._topics import validate_claim_topic
from src.pilot._requests import requested_periods


_PUBLICATION_CUE = re.compile(r"\b(?:published|publication|released|release|issued|dated)\b", re.I)
_SCENARIO = re.compile(r"\b(?:STEPS|APS|NZE)\b")
_RELEASE_DATELINE = re.compile(
    r"^(?:No\.?\s*)?\d+/\d{4}\s*(?:\([^)]{1,20}\)\s*)?"
    r"\d{1,2}\s+(?:" + '|'.join(_MONTHS.split()) + r")\s+\d{4}\b", re.I)


def _numeric_values(value):
    # The declared currency codes also occur directly beside amounts in source
    # headings (USD33). A general letter/digit split would admit identifier
    # suffixes such as record33, so normalize only these existing currency units.
    value = re.sub(r"(?<!\w)(?:USD|THB)(?=\d)", " ", value, flags=re.I)
    value = re.sub(r"(?<=\d)[ ,](?=\d{3}(?:\D|$))", "", value)
    # Do not salvage the integer prefix or fractional suffix of a malformed
    # identifier-like decimal. Ordinary sentence-final punctuation stays legal.
    return {Decimal(n) for n in re.findall(r"(?<![\w.])\d+(?:\.\d+)?(?!\w|\.\d)", value)}


def _without_established_period(text, period):
    return re.sub(r"(?<!\w)" + re.escape(period) + r"(?!\w)", "", text, flags=re.I) if period else text


def measurement_periods(text):
    """Exclude explicit publication cues and a narrow release-number dateline.

    This does not classify arbitrary datelines or establish which measurement a
    remaining date describes. Preserve factual periods after the masked prefix.
    """
    if _PUBLICATION_CUE.search(text):
        return []
    text = " ".join(text.split())
    dateline = _RELEASE_DATELINE.match(text)
    return explicit_periods(text[dateline.end():] if dateline else text)


def same_pinned_document(left, right):
    """Verify corpus membership and document identity, not geographic entailment."""
    digest = left.get("corpus_sha256", "")
    return (isinstance(digest, str) and bool(re.fullmatch(r"[0-9a-f]{64}", digest)) and digest == right.get("corpus_sha256")
            and isinstance(left.get("doc_name"), str) and bool(left["doc_name"])
            and isinstance(left.get("url"), str) and bool(left["url"])
            and all(left.get(k) == right.get(k) for k in ("doc_name", "url", "published")))


def _contains(text, phrase):
    text, phrase = " ".join(text.split()), " ".join(phrase.split())
    return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, re.I))


def _period_evidence(component, evidence, period, automatic=False):
    if period.casefold() not in {p.casefold() for p in measurement_periods(evidence.quote)}:
        return False
    return not automatic or _contains(evidence.quote, component.short_answer)


def _requests_period(component, question, period):
    return period.casefold() in {p.casefold() for p in requested_periods(component.question_anchor,question)}


def resolve_scope(mapping, question, sources=None, reporting_bindings=()):
    """Copy only source-backed scope, and retain its supporting component/quotation."""
    supported = [c for c in mapping.components if c.status in {"supported", "partial"}]
    resolution = getattr(mapping, "geography_resolution", None)
    geographic_context = {}
    if resolution is not None:
        if resolution.value != mapping.geography:
            raise ValueError("Geography resolution does not match mapped scope")
        geographic_context["geography_resolution"] = resolution.model_dump()
    if not supported:
        return mapping, {"fields": {}, "components": {}, "unresolved_requested_periods": [], **geographic_context}
    requested = explicit_periods(question)
    period = mapping.period
    origin = "mapper"
    if not period and len(requested) == 1 and any(
            _requests_period(c,question,requested[0]) and _period_evidence(c, e, requested[0], automatic=True)
            for c in supported for e in c.evidence):
        period = requested[0]
        origin = "requested period also present in selected quotation"
    fields, components = {}, {}
    heading_matches = []
    if sources and reporting_bindings and len(requested) == 1 and (not period or period.casefold() == requested[0].casefold()):
        from src.pilot._report_context import binding_matches
        by_id = {c.component_id: c for c in supported}
        for binding in reporting_bindings:
            if binding.get('proof_format') == 'bounded-quarterly-v1':
                continue
            if binding['component_id'] not in by_id or binding['period'].casefold() != requested[0].casefold():
                raise ValueError('Reporting context does not match a supported requested component')
            heading_matches.append(binding_matches(binding, by_id[binding['component_id']], sources))
        if heading_matches:
            period, origin = requested[0], 'explicit heading and bounded monthly section; verify document context'
    for name, value in [("geography", mapping.geography), ("period", period)]:
        if not value:
            continue
        if name == "geography" and resolution is not None:
            matches = [{"component_id": c.component_id, "source_id": g.source_id, "quote": g.quote}
                       for c in supported for g in resolution.evidence
                       if any(e.source_id == g.source_id or (sources and same_pinned_document(
                           sources[g.source_id], sources[e.source_id])) for e in c.evidence)]
        elif name == "period" and heading_matches:
            matches = heading_matches + [{"component_id": c.component_id, "source_id": e.source_id, "quote": e.quote}
                for c in supported for e in c.evidence if _requests_period(c,question,value)
                and _period_evidence(c, e, value, automatic=origin != 'mapper')]
        else:
            matches = [{"component_id": c.component_id, "source_id": e.source_id, "quote": e.quote}
                       for c in supported for e in c.evidence if (
                           _requests_period(c,question,value) and _period_evidence(c, e, value, automatic=origin != "mapper") if name == "period"
                           else _contains(e.quote, value))]
        if not matches:
            raise ValueError("Mapped " + name + " is not present in selected supporting quotations")
        fields[name] = {"value": value, "origin": origin if name == "period" else "mapper",
                        "evidence": matches}
        for match in matches:
            components.setdefault(match["component_id"], {})[name] = value
    quarter_matches = []
    if sources:
        from src.pilot._quarter_context import quarter_binding_matches
        by_id = {c.component_id: c for c in supported}
        for binding in reporting_bindings:
            if binding.get('proof_format') != 'bounded-quarterly-v1':
                continue
            if binding['component_id'] not in by_id:
                raise ValueError('Reporting context does not match a supported requested component')
            match = quarter_binding_matches(binding, by_id[binding['component_id']], sources, question)
            quarter_matches.append(match)
            components.setdefault(binding['component_id'], {})['period'] = binding['period']
            field = fields.setdefault('period', {'value': '', 'origin': 'bounded per-component report headings', 'evidence': []})
            field['evidence'].append(match)
            field.setdefault('values_by_component', {})[binding['component_id']] = binding['period']
    requested_scenarios = set(_SCENARIO.findall(question))
    unresolved_scenarios = []
    if len(requested_scenarios) == 1:
        scenario = next(iter(requested_scenarios))
        matches = []
        for component in supported:
            if all(set(_SCENARIO.findall(e.quote)) == {scenario} for e in component.evidence):
                components.setdefault(component.component_id, {})["scenario"] = scenario
                matches += [{"component_id": component.component_id, "source_id": e.source_id, "quote": e.quote}
                            for e in component.evidence]
            else:
                unresolved_scenarios.append(scenario)
        if matches:
            fields["scenario"] = {"value": scenario, "origin": "requested scenario explicit and unambiguous in every selected quotation", "evidence": matches}
    updated = mapping.model_copy(update={"period": period})
    return updated, {"fields": fields, "components": components,
        "unresolved_requested_periods": [value for value in requested if not all(
            any(_period_evidence(c, e, value, automatic=True) for e in c.evidence)
            or components.get(c.component_id, {}).get("period") == value for c in supported
            if value.casefold() in {p.casefold() for p in requested_periods(c.question_anchor,question)})],
        "reporting_period_context": bool(heading_matches or quarter_matches),
        "title_periods": list(dict.fromkeys(components.get(c.component_id, {}).get('period', '')
                                             for c in supported if components.get(c.component_id, {}).get('period'))),
        "unresolved_requested_scenarios": sorted(set(unresolved_scenarios)), **geographic_context}


class UnsupportedClaimPeriod(ValueError):
    """A composed period is absent from this component's established evidence."""


def qualify_claim(text, component, context):
    """Retain verified scope without truncating claims or assigning another component's scope."""
    from src.pilot._quarter_context import _QUARTER
    for period in [*explicit_periods(text), *(m.group() for m in _QUARTER.finditer(text))]:
        if (not any(_contains(e.quote, period) for e in component.evidence)
                and not _contains(context.get("components", {}).get(component.component_id, {}).get("period", ""), period)):
            raise UnsupportedClaimPeriod("Composed claim uses a period absent from its selected evidence")
    scope = context.get("components", {}).get(component.component_id, {})
    missing = [scope[name] for name in ("geography", "period", "scenario")
               if scope.get(name) and not _contains(text, scope[name])]
    qualified = ", ".join(missing) + ": " + text if missing else text
    if len(qualified) > 800:
        raise ValueError("Scoped claim exceeds the public text limit")
    sources = []
    for name, value in scope.items():
        matches = context["fields"][name]["evidence"]
        match = next(match for match in matches if match["component_id"] == component.component_id)
        sources.extend(match.get('context_source_ids', [match['source_id']]))
    return qualified, sources


def validate_claim_measure_and_numbers(text, component, question=None, scope_period=""):
    """Narrow regression gates, not a general entailment or unit-conversion judge."""
    if (question and re.search(r"\belectricity demand\b", question, re.I)
            and not re.search(r"\bpeak\b", question, re.I) and re.search(r"\bpeak (?:electricity )?demand\b", text, re.I)):
        raise ValueError("Peak demand cannot substitute for the requested electricity demand measure")
    if (question and re.search(r"\belectricity demand\b", question, re.I)
            and re.search(r"\b(?:total final |final |total )?energy consumption\b", text, re.I)
            and not re.search(r"\belectricity\b", text, re.I)):
        raise ValueError("Total energy consumption cannot substitute for electricity demand")
    if (question and re.search(r"\bdemand\b", question, re.I) and not re.search(r"\bgeneration\b", question, re.I)
            and re.search(r"\bgeneration\b", text, re.I) and not re.search(r"\bdemand\b", text, re.I)):
        raise ValueError("Generation cannot substitute for the requested demand measure")
    established = _numeric_values(" ".join(e.quote for e in component.evidence))
    factual_text = _without_established_period(text, scope_period)
    if not _numeric_values(factual_text).issubset(established):
        raise ValueError("Draft introduces a numeric value absent from its selected evidence")
    validate_quantity_roles(factual_text, component, question)
    validate_claim_topic(factual_text, component, question)
    from src.pilot._entity_comparison import validate_composed_comparison
    validate_composed_comparison(factual_text, component)


def validate_mapped_answers(mapping, context):
    """Check numeric compatibility of each mapper answer before composition.

    Use only that component's selected quotations and already established period.
    This shares the existing numeric parsing, not stricter unit-pair rules that
    could reject shorthand mapper answers. It is not entailment/relevance proof.
    Unresolved components keep their existing validated state without repair.
    """
    checks = {}
    for component in mapping.components:
        if component.status not in {'supported', 'partial'}:
            checks[component.component_id] = {'status': 'not_applicable', 'semantic_support_proven': False}
            continue
        period = context.get('components', {}).get(component.component_id, {}).get('period', '')
        answer = _without_established_period(component.short_answer, period)
        established = _numeric_values(' '.join(e.quote for e in component.evidence))
        if not _numeric_values(answer).issubset(established):
            raise ValueError('Mapped answer introduces a numeric value absent from its selected evidence')
        checks[component.component_id] = {'status': 'passed_necessary_checks', 'semantic_support_proven': False}
    return checks
