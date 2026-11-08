"""Necessary supported-state provenance coverage; no semantic answer selection."""
from functools import reduce
from itertools import combinations
from operator import or_
from typing import get_args, Literal, Union
from pydantic import create_model, Field


MAX_COVER_PATTERNS = 128


def _minimal_covers(masks, target, branch_count):
    """Enumerate bounded minimal provenance covers, in deterministic mask order."""
    if reduce(or_, masks, 0) != target:
        return []
    covers = []
    for size in range(1, min(5, branch_count, len(masks)) + 1):
        for choice in combinations(masks, size):
            if reduce(or_, choice, 0) != target:
                continue
            if any(reduce(or_, choice[:i] + choice[i+1:], 0) == target for i in range(size)):
                continue
            covers.append(choice)
            if len(covers) > MAX_COVER_PATTERNS:
                raise ValueError("Coverage decoder exceeds bounded alternative budget")
    return covers


def covered_schema(base, catalog, report, requests, requirements):
    results = {r.subtask_id:r for r in report.results}
    slots, profile = [], {}
    original = get_args(base.model_fields["components"].annotation)
    for request, slot in zip(requests, original, strict=True):
        cid = request["component_id"]
        if cid not in requirements:
            slots.append(slot)
            continue
        branches = requirements[cid]
        supports = [{s.source_id for s in results[bid].sources if s.role == "support"}
                    if bid in results and results[bid].outcome == "evidence" else set()
                    for bid in branches]
        groups = {}
        for sid, span in catalog.items():
            mask = sum(1 << i for i, sources in enumerate(supports) if span["source_id"] in sources)
            if mask:
                groups.setdefault(mask, []).append(sid)
        target = (1 << len(branches)) - 1
        masks = sorted(groups)
        covers = _minimal_covers(masks, target, len(branches))
        alternatives = []
        for cover in covers:
            prefix = [Literal[tuple(groups[mask])] for mask in cover]
            extra = Literal[tuple(catalog)]
            for count in range(6-len(prefix)):
                alternatives.append(tuple[tuple(prefix + [extra]*count)])
        variants = []
        for variant in get_args(slot):
            if get_args(variant.model_fields["status"].annotation) != ("supported",):
                variants.append(variant)
            elif alternatives:
                evidence_type = Union[tuple(alternatives)] if len(alternatives)>1 else alternatives[0]
                variants.append(create_model("Covered"+variant.__name__, __base__=variant,
                    evidence=(evidence_type, Field(description=(
                        "Choose a coverage prefix in schema order, then optional distinct extra spans. "
                        "Provenance coverage does not establish relevance or factual support."),
                        json_schema_extra={"uniqueItems": True}))))
        # With absent support, supported is unavailable; partial/missing/conflict
        # still use the existing validators. Never fabricate evidence to fill it.
        slots.append(Union[tuple(variants)] if len(variants)>1 else variants[0])
        profile[cid] = {"required_branches":list(branches), "minimal_cover_patterns":len(covers),
                        "supported_available":bool(covers), "semantic_support_proven":False}
    schema = create_model("CoveredSourceSelection", __base__=base, components=(tuple[tuple(slots)], ...))
    schema.__coverage_profile__ = profile
    return schema
