"""Source-literal decoder choices, not an automatic geographic classifier."""
import re
from typing import Literal, Union

from pydantic import Field, create_model
from src.pilot._scope import _MONTHS, _PERIOD, explicit_periods, measurement_periods


_WORDS = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*", re.UNICODE)
_GENERIC = {"A", "An", "The", "In", "On", "At", "For", "Source", "Note", "Measured", "Output",
    "Capacity", "Expansion", "Spending", "Meanwhile", "However", "MWh", "GWh", "TWh", "GDP", "PCI", "PII"}

_PLACE_CUE = re.compile(
    r"\b(?:(?:region|district|province|city|country|county|state|town)\s+of|in|across|throughout|within)\s+$", re.I)
_PLACE_SUFFIX = re.compile(r"^\s+(?:region|district|province|city|country|county|state|town)\b", re.I)


def _explicit_place_occurrence(text, start, end, value):
    """Lexical location cues narrow choices; they are not a semantic location classifier."""
    if value.split()[0] in {"The", "A", "An", "Bank", "Source", "Note"}:
        return False
    if value in _MONTHS.split() and not re.search(
            r"\b(?:region|district|province|city|country|county|state|town)\s+of\s+$", text[:start], re.I):
        return bool(_PLACE_SUFFIX.search(text[end:]))
    return bool(_PLACE_CUE.search(text[:start]) or _PLACE_SUFFIX.search(text[end:])
                or re.fullmatch(r"(?:Region|District|Province|City|Country|County|State|Town)\s+\S+(?:\s+\S+)*", value))


def geography_choices(catalog, question, limit=16, explicit_only=False, allowed_names=None, requested_only=False):
    """Offer literal label candidates; capitalization alone never sets known geography."""
    labels = {}
    temporal = []
    for sid, span in catalog.items():
        text = span["text"]
        words = list(_WORDS.finditer(text))
        dates = [(m.start(), m.end()) for m in _PERIOD.finditer(text) if explicit_periods(m.group())]
        for i, word in enumerate(words):
            token = word.group()
            if not (token[0].isupper() or any(ord(c) > 127 for c in token)):
                continue
            for end in range(i + 1, min(i + 4, len(words)) + 1):
                group = words[i:end]
                if any(not (w.group()[0].isupper() or w.group() in {"of", "the", "and"}) for w in group):
                    break
                if not group[-1].group()[0].isupper() and len(group) > 1:
                    continue
                if any(not text[a.end():b.start()].isspace() for a, b in zip(group, group[1:])):
                    break
                value = " ".join(text[group[0].start():group[-1].end()].split())
                if any(start <= group[0].start() and group[-1].end() <= end for start, end in dates):
                    temporal.append({"value": value, "span_id": sid, "start": group[0].start(), "end": group[-1].end()})
                    continue
                if len(value) > 60 or value in _GENERIC:
                    continue
                if requested_only and not re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", question, re.I):
                    continue
                if (requested_only and end < len(words) and words[end].group()[0].isupper()
                        and text[group[-1].end():words[end].start()].isspace()):
                    continue  # Do not shorten a source name to match another requested name.
                if allowed_names is not None and value not in allowed_names:
                    continue
                if allowed_names is None and explicit_only and not _explicit_place_occurrence(text, group[0].start(), group[-1].end(), value):
                    continue
                labels.setdefault(value, [])
                if sid not in labels[value]:
                    labels[value].append(sid)
    query_words = set(re.findall(r"\w+", question.casefold()))
    ordered = sorted(labels, key=lambda value: -len(set(re.findall(r"\w+", value.casefold())) & query_words))
    chosen = ordered[:limit]
    return {"labels": [{"value": value, "span_ids": labels[value]} for value in chosen],
        "total_labels": len(ordered), "truncated": len(ordered) > limit,
        "excluded_temporal_mentions": temporal,
        "explicit_location_cues_only": explicit_only,
        "requested_labels_only": requested_only,
        "classification": "untyped source-literal choices; model and owner must establish geographic meaning"}


def period_choices(catalog, question=None):
    """Only literal periods in non-publication spans may enter the decoder."""
    periods = {}
    requested = {p.casefold() for p in explicit_periods(question or "")}
    years = set(re.findall(r"(?<!\d)\d{4}(?!\d)", question or ""))
    for sid, span in catalog.items():
        for period in measurement_periods(span["text"]):
            if requested and period.casefold() not in requested:
                continue
            if not requested and years and not (set(re.findall(r"\d{4}", period)) & years):
                continue
            periods.setdefault(period, []).append(sid)
    return [{"value": value, "span_ids": ids} for value, ids in periods.items()]


def constrained_selection(base, geography_base, choices, requests=None, periods=None, request_views=None):
    variants = []
    for i, label in enumerate(choices["labels"]):
        variant = create_model(f"KnownGeography{i}", __base__=geography_base,
            status=(Literal["known"], ...), value=(Literal[label["value"]], ...),
            evidence=(list[Literal[tuple(label["span_ids"])]], Field(min_length=1, max_length=1)),
            reason=(Literal[""], ...))
        variants.append(variant)
    unresolved = create_model("UnresolvedGeography", __base__=geography_base,
        status=(Literal["unresolved"], ...), value=(Literal[""], ...),
        evidence=(list[str], Field(max_length=0)), reason=(str, Field(min_length=1, max_length=200)))
    variants.append(unresolved)
    geo_type = Union[tuple(variants)] if len(variants) > 1 else unresolved
    fields = {"geography": (geo_type, ...)}
    if periods is not None:
        fields["period"] = (Literal[tuple(["", *[p["value"] for p in periods]])], "")
    if requests is not None:
        # Positional schemas prevent invented or repeated request IDs at decoding time.
        # Semantic validation still checks every selected quotation after parsing.
        from src.pilot._evidence import EvidenceSelectionComponent
        slots = []
        for i, request in enumerate(requests):
            component_fields = {"component_id": (Literal[request["component_id"]], ...),
                "measure": (Literal[""], ""), "scenario": (Literal[""], ""), "kind": (Literal["unknown"], "unknown")}
            views = (request_views or {}).get(request["component_id"])
            if views:
                required = [Literal[tuple(view["span_ids"])] for view in views]
                extra = Literal[tuple(dict.fromkeys(sid for view in views for sid in view["span_ids"]))]
                extra_counts = range(6 - len(required)) if all(v.get("allow_extra", True) for v in views) else [0]
                variants = [tuple[()]] + [tuple[tuple(required + [extra] * count)] for count in extra_counts]
                component_fields["evidence"] = (Union[tuple(variants)], ...)
            slots.append(create_model(f"RequestSlot{i}", __base__=EvidenceSelectionComponent, **component_fields))
        slots = tuple(slots)
        if not 1 <= len(slots) <= 5:
            raise ValueError("Expected one to five canonical request slots")
        fields["components"] = (tuple[slots], ...)
    return create_model("EvidenceSelection", __base__=base, **fields)


def constrained_composition(mapping, scope_context=None):
    from src.pilot._composition import response_schema
    return response_schema(mapping, scope_context)
