"""Source-literal decoder choices, not an automatic geographic classifier."""
import re
from typing import Literal, Union

from pydantic import Field, create_model
from src.pilot._scope import _PERIOD, explicit_periods


_WORDS = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*", re.UNICODE)
_GENERIC = {"A", "An", "The", "In", "On", "At", "For", "Source", "Note", "Measured", "Output",
    "Capacity", "Expansion", "Spending", "Meanwhile", "However", "MWh", "GWh", "TWh", "GDP", "PCI", "PII"}


def geography_choices(catalog, question, limit=16):
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
                labels.setdefault(value, [])
                if sid not in labels[value]:
                    labels[value].append(sid)
    query_words = set(re.findall(r"\w+", question.casefold()))
    ordered = sorted(labels, key=lambda value: -len(set(re.findall(r"\w+", value.casefold())) & query_words))
    chosen = ordered[:limit]
    return {"labels": [{"value": value, "span_ids": labels[value]} for value in chosen],
        "total_labels": len(ordered), "truncated": len(ordered) > limit,
        "excluded_temporal_mentions": temporal,
        "classification": "untyped source-literal choices; model and owner must establish geographic meaning"}


def constrained_selection(base, geography_base, choices, requests=None):
    variants = []
    for i, label in enumerate(choices["labels"]):
        variant = create_model(f"KnownGeography{i}", __base__=geography_base,
            status=(Literal["known"], ...), value=(Literal[label["value"]], ...),
            evidence=(list[Literal[tuple(label["span_ids"])]], Field(min_length=1, max_length=5)),
            reason=(Literal[""], ...))
        variants.append(variant)
    unresolved = create_model("UnresolvedGeography", __base__=geography_base,
        status=(Literal["unresolved"], ...), value=(Literal[""], ...),
        evidence=(list[str], Field(max_length=0)), reason=(str, Field(min_length=1, max_length=200)))
    variants.append(unresolved)
    geo_type = Union[tuple(variants)] if len(variants) > 1 else unresolved
    fields = {"geography": (geo_type, ...)}
    if requests is not None:
        # Positional schemas prevent invented or repeated request IDs at decoding time.
        # Semantic validation still checks every selected quotation after parsing.
        from src.pilot._evidence import EvidenceSelectionComponent
        slots = tuple(create_model(f"RequestSlot{i}", __base__=EvidenceSelectionComponent,
            component_id=(Literal[request["component_id"]], ...))
            for i, request in enumerate(requests))
        if not 1 <= len(slots) <= 5:
            raise ValueError("Expected one to five canonical request slots")
        fields["components"] = (tuple[slots], ...)
    return create_model("EvidenceSelection", __base__=base, **fields)
