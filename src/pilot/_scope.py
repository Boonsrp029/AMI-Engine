"""Conservative scope propagation; phrase occurrence is not semantic entailment."""

import re
import hashlib
from decimal import Decimal
from src.utils._periods import _MONTHS, _PERIOD, explicit_periods


_PUBLICATION_CUE = re.compile(r"\b(?:published|publication|released|release|issued|dated)\b", re.I)
_SCENARIO = re.compile(r"\b(?:STEPS|APS|NZE)\b")
_RELEASE_DATELINE = re.compile(
    r"^(?:No\.?\s*)?\d+/\d{4}\s*(?:\([^)]{1,20}\)\s*)?"
    r"\d{1,2}\s+(?:" + '|'.join(_MONTHS.split()) + r")\s+\d{4}\b", re.I)


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
            _period_evidence(c, e, requested[0], automatic=True) for c in supported for e in c.evidence):
        period = requested[0]
        origin = "requested period also present in selected quotation"
    fields, components = {}, {}
    heading_matches = []
    if sources and reporting_bindings and len(requested) == 1 and (not period or period.casefold() == requested[0].casefold()):
        from src.pilot._report_context import binding_matches
        by_id = {c.component_id: c for c in supported}
        for binding in reporting_bindings:
            if binding['component_id'] not in by_id or binding['period'].casefold() != requested[0].casefold():
                raise ValueError('Reporting context does not match a supported requested component')
            heading_matches.append(binding_matches(binding, by_id[binding['component_id']], sources))
        if heading_matches:
            period, origin = requested[0], 'explicit heading and bounded monthly section; verify document context'
    if not period and len(requested) == 1 and sources:
        for source_id, source in sources.items():
            match = re.search(r"\b(?:Economic and Monetary|Economic) Conditions for\s+(" + re.escape(requested[0]) + r")\b", source["content"], re.I)
            if match is None or not source.get("doc_name") or not source.get("url"):
                continue
            for component in supported:
                factual = [sources[e.source_id] for e in component.evidence]
                if (component.kind == "projection" or any(re.search(r"\bproject(?:ed|ion|s)|\bforecast", e.quote, re.I) for e in component.evidence)
                        or any(explicit_periods(e.quote) and not _contains(e.quote, requested[0]) for e in component.evidence)):
                    continue
                if all(all(record.get(key) == source.get(key) for key in ("doc_name", "url", "published")) for record in factual):
                    heading_matches.append({"component_id": component.component_id, "source_id": source_id,
                        "quote": match.group(), "context_start": match.start(), "context_end": match.end(),
                        "content_sha256": hashlib.sha256(source["content"].encode()).hexdigest(),
                        "role": "reporting-period heading in the same document"})
        if heading_matches:
            period, origin = requested[0], "explicit reporting-period heading; verify document context"
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
                for c in supported for e in c.evidence if _period_evidence(c, e, value, automatic=origin != 'mapper')]
        else:
            matches = [{"component_id": c.component_id, "source_id": e.source_id, "quote": e.quote}
                       for c in supported for e in c.evidence if (
                           _period_evidence(c, e, value, automatic=origin != "mapper") if name == "period"
                           else _contains(e.quote, value))]
        if not matches:
            raise ValueError("Mapped " + name + " is not present in selected supporting quotations")
        fields[name] = {"value": value, "origin": origin if name == "period" else "mapper",
                        "evidence": matches}
        for match in matches:
            components.setdefault(match["component_id"], {})[name] = value
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
            or components.get(c.component_id, {}).get("period") == value for c in supported)],
        "reporting_period_context": bool(heading_matches), "unresolved_requested_scenarios": sorted(set(unresolved_scenarios)), **geographic_context}


class UnsupportedClaimPeriod(ValueError):
    """A composed period is absent from this component's established evidence."""


def qualify_claim(text, component, context):
    """Retain verified scope without truncating claims or assigning another component's scope."""
    for period in explicit_periods(text):
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
    def numbers(value):
        value = re.sub(r"(?<=\d)[ ,](?=\d{3}(?:\D|$))", "", value)
        return {Decimal(n) for n in re.findall(r"(?<!\w)\d+(?:\.\d+)?(?!\w)", value)}
    established = numbers(" ".join(e.quote for e in component.evidence))
    factual_text = re.sub(r"(?<!\w)" + re.escape(scope_period) + r"(?!\w)", "", text, flags=re.I) if scope_period else text
    if not numbers(factual_text).issubset(established):
        raise ValueError("Draft introduces a numeric value absent from its selected evidence")
