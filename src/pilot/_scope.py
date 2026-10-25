"""Conservative scope propagation; phrase occurrence is not semantic entailment."""

import re
from datetime import date


_MONTHS = "January February March April May June July August September October November December"
_PERIOD = re.compile(r"\b(?:" + "|".join(_MONTHS.split()) + r")\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b", re.I)
_PUBLICATION_CUE = re.compile(r"\b(?:published|publication|released|release|issued|dated)\b", re.I)


def _contains(text, phrase):
    text, phrase = " ".join(text.split()), " ".join(phrase.split())
    return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, re.I))


def explicit_periods(text):
    """Recognize full English month/year or valid ISO dates, never publication metadata."""
    values = []
    for match in _PERIOD.finditer(text):
        value = " ".join(match.group().split())
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            try:
                date.fromisoformat(value)
            except ValueError:
                continue
        else:
            _, year = value.split()
            if not 1 <= int(year) <= 9999:
                continue
        if value.casefold() not in {v.casefold() for v in values}:
            values.append(value)
    return values


def _period_evidence(component, evidence, period, automatic=False):
    if not _contains(evidence.quote, period) or _PUBLICATION_CUE.search(evidence.quote):
        return False
    return not automatic or _contains(evidence.quote, component.short_answer)


def resolve_scope(mapping, question):
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
    for name, value in [("geography", mapping.geography), ("period", period)]:
        if not value:
            continue
        if name == "geography" and resolution is not None:
            matches = [{"component_id": c.component_id, "source_id": g.source_id, "quote": g.quote}
                       for c in supported for g in resolution.evidence
                       if any(e.source_id == g.source_id for e in c.evidence)]
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
    updated = mapping.model_copy(update={"period": period})
    return updated, {"fields": fields, "components": components,
        "unresolved_requested_periods": [value for value in requested if not any(
            _period_evidence(c, e, value, automatic=True) for c in supported for e in c.evidence)], **geographic_context}


def qualify_claim(text, component, context):
    """Retain verified scope without truncating claims or assigning another component's scope."""
    for period in explicit_periods(text):
        if not any(_contains(e.quote, period) for e in component.evidence):
            raise ValueError("Composed claim uses a period absent from its selected evidence")
    scope = context.get("components", {}).get(component.component_id, {})
    missing = [scope[name] for name in ("geography", "period")
               if scope.get(name) and not _contains(text, scope[name])]
    qualified = ", ".join(missing) + ": " + text if missing else text
    if len(qualified) > 800:
        raise ValueError("Scoped claim exceeds the public text limit")
    sources = []
    for name, value in scope.items():
        matches = context["fields"][name]["evidence"]
        sources.append(next(match["source_id"] for match in matches
                            if match["component_id"] == component.component_id))
    return qualified, sources
