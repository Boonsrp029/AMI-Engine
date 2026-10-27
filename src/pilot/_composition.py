"""Bounded synthesis units retain selected evidence without inventing new requests."""
import hashlib
import json
import re
from itertools import combinations
from typing import Literal, Union

from pydantic import create_model

from src.pilot._evidence import ComposedBrief, ComposedClaim, EvidenceQuote, project_draft, supported_components
from src.pilot._scope import UnsupportedClaimPeriod, qualify_claim


class UnitClaim(ComposedClaim):
    unit_id: str


class UnitBrief(ComposedBrief):
    claims: list[UnitClaim]


def composition_units(mapping):
    """Split selected passages into at most five slots, preserving component/evidence order.

    Grouping is structural, not semantic: it guarantees that all selected quotations
    enter synthesis, not that a generated sentence covers or supports every fact.
    """
    groups = [{"component_id": c.component_id, "evidence": [e.model_dump() for e in c.evidence]}
              for c in supported_components(mapping)]
    for group in groups:
        for evidence in group["evidence"]:
            if re.search(r"\bignore\b.{0,60}\b(?:instructions|rules)\b|\bapprove_export\b|"
                         r"\breveal\b.{0,40}\b(?:secrets|credentials)\b", evidence["quote"], re.I | re.S):
                raise ValueError("Selected synthesis evidence contains instruction-like source content")
    while len(groups) < 5:
        candidates = [i for i, group in enumerate(groups) if len(group["evidence"]) > 1]
        if not candidates:
            break
        index = max(candidates, key=lambda i: (len(groups[i]["evidence"]),
            sum(len(e["quote"]) for e in groups[i]["evidence"]), -i))
        group = groups[index]
        midpoint = len(group["evidence"]) // 2
        groups[index:index + 1] = [{**group, "evidence": group["evidence"][:midpoint]},
                                  {**group, "evidence": group["evidence"][midpoint:]}]
    for i, group in enumerate(groups, 1):
        group["unit_id"] = f"u{i}"
        group["identity_sha256"] = hashlib.sha256(json.dumps(group, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return groups


def payload(mapping, as_of, scope_context=None):
    # Global title scope must not be offered as factual scope for every unit.
    context = scope_context or {}
    units = [{k: v for k, v in unit.items() if k not in {'identity_sha256', 'scope_citation_ids'}}
             for unit in canonical_units(mapping, context)]
    return {"as_of": as_of, "units": units}


def canonical_units(mapping, scope_context=None):
    """Compose identical evidence once only when scope and citation proofs agree.

    Origin units remain independent validation targets. This does not merge
    paraphrases, overlapping spans or evidence merely sharing a source ID.
    """
    context = scope_context or {}
    result, positions = [], {}
    for unit in composition_units(mapping):
        cid = unit['component_id']
        scope = context.get('components', {}).get(cid, {})
        citations = []
        for name in scope:
            matches = context.get('fields', {}).get(name, {}).get('evidence', [])
            match = next((m for m in matches if m['component_id'] == cid), None)
            if match is None:
                raise ValueError('Established composition scope lacks citation evidence')
            citations.extend(match.get('context_source_ids', [match['source_id']]))
        key = (tuple((e['source_id'], e['quote']) for e in unit['evidence']),
               json.dumps(scope, sort_keys=True), tuple(citations))
        if key not in positions:
            positions[key] = len(result)
            result.append({**unit, 'established_scope': scope, 'scope_citation_ids': citations, 'origins': []})
        result[positions[key]]['origins'].append({'unit_id': unit['unit_id'], 'component_id': cid})
    return result


def response_schema(mapping, scope_context=None):
    units = canonical_units(mapping, scope_context)
    if not 1 <= len(units) <= 5:
        raise ValueError("Composition requires one to five evidence units")
    slots = tuple(create_model(f"EvidenceUnit{i}", __base__=UnitClaim,
        unit_id=(Literal[unit["unit_id"]], ...), component_id=(Literal[unit["component_id"]], ...))
        for i, unit in enumerate(units))
    # Ordered subsets retain the existing omission fallback; no unit may repeat.
    variants = [tuple[()]]
    variants += [tuple[subset] for size in range(1, len(slots) + 1) for subset in combinations(slots, size)]
    return create_model("ComposedBrief", __base__=UnitBrief,
        title=(Literal["Analyst research brief"], ...), claims=(Union[tuple(variants)], ...))


def _missing_requested_cause(text, evidence, question):
    """Conservative lexical omission check, not a semantic judge."""
    if not question or not re.search(r"\bwhy\b|\bwhat (?:supported|drove)\b|\bactivities supported\b|\bcauses?\b|\bdrivers?\b|\b(?:which|what) factors? explains?\b", question, re.I):
        return False
    stop = {"that", "with", "from", "this", "higher", "lower", "increase", "increased", "increases", "prices", "demand", "which", "they", "their", "after", "following"}
    words = lambda value: {w.casefold() for w in re.findall(r"[^\W\d_]{4,}", value) if w.casefold() not in stop}
    actual = words(text)
    for quote in evidence:
        match = re.search(r"(?:\b(?:supported by|driven (?:primarily )?by|due to|because|reflecting)|,\s*as)\s+(.+)", quote.quote, re.I)
        if match:
            for part in re.split(r"\bas well as\b", match[1], flags=re.I):
                expected = words(part)
                # Any missing literal causal term conservatively retains the
                # selected excerpt. Shared subject words alone are insufficient:
                # "long-haul tourists increased" can omit "higher proportion".
                if len(expected) >= 2 and not expected.issubset(actual):
                    return True
    return False


def _missing_requested_list_item(text, evidence, question):
    """Detect literal omissions from explicit selected lists, not semantic completeness.

    Synonyms can cause an extractive fallback. Unselected passages and lists without
    explicit markers remain outside this deliberately narrow check.
    """
    if not re.search(r"\b(?:which|what)\b.{0,45}\b(?:categories|products|groups|markets|sectors|measures|factors)\b", question, re.I):
        return False
    generic = {"and", "or", "the", "of", "in", "products", "product", "categories", "category", "these", "included"}
    def terms(value):
        return {w[:-1] if len(w) > 4 and w.endswith("s") else w
                for w in re.findall(r"[^\W\d_]+", value.casefold()) if w not in generic}
    actual = terms(text)
    for quote in evidence:
        numbered = list(re.finditer(r"\b\d+\)\s*", quote.quote))
        labels = []
        if len(numbered) >= 2:
            for index, marker in enumerate(numbered):
                stop = numbered[index + 1].start() if index + 1 < len(numbered) else len(quote.quote)
                part = quote.quote[marker.end():stop]
                labels.append(re.split(r",|;|\b(?:mainly|due to|because|while|supported by)\b", part, maxsplit=1, flags=re.I)[0])
        example = re.search(r"\bsuch as\s+([^.;]+)", quote.quote, re.I)
        if example:
            labels.extend(re.split(r",\s*(?:and\s+)?|\s+and\s+", example[1]))
        if any(expected and not expected.issubset(actual) for expected in map(terms, labels)):
            return True
    return False


def _measure_qualifiers(text):
    """Recognize only explicit seasonal status and gold exclusion, not entailment."""
    normalized = ' '.join(text.casefold().split())
    labels = set()
    for label, pattern in [('unadjusted', r'\b(?:non-seasonally adjusted|unadjusted|not seasonally adjusted|not after seasonal adjustment)\b'),
                           ('seasonally_adjusted', r'\b(?:seasonally adjusted|after seasonal adjustment)\b'),
                           ('gold_excluded', r'\b(?:excluding gold|gold excluded)\b')]:
        if any(not re.search(r'(?:non-|not )$', normalized[:m.start()]) for m in re.finditer(pattern, normalized)):
            labels.add(label)
    return labels


def project(value, mapping, question, scope_context, diagnostics=None):
    composed = UnitBrief.model_validate(value)
    units = composition_units(mapping)
    canonical = canonical_units(mapping, scope_context)
    by_id = {unit['unit_id']: unit for unit in canonical}
    representatives = {origin['unit_id']: unit['unit_id'] for unit in canonical for origin in unit['origins']}
    chosen = {}
    for claim in composed.claims:
        if claim.unit_id not in by_id or claim.component_id != by_id[claim.unit_id]["component_id"]:
            raise ValueError("Composed claim references an unknown or mismatched evidence unit")
        if claim.unit_id in chosen:
            raise ValueError("Composed draft repeats an evidence unit")
        chosen[claim.unit_id] = claim.text
    components = {c.component_id: c for c in mapping.components}
    projected, claims, fallback = [], [], []
    fallback_reasons = {}
    omitted_qualifiers = {}
    baseline_normalizations = []
    for unit in units:
        uid = unit["unit_id"]
        evidence = [EvidenceQuote.model_validate(e) for e in unit["evidence"]]
        projected.append(components[unit["component_id"]].model_copy(update={"component_id": uid, "evidence": evidence}))
        text = chosen.get(representatives[uid])
        invalid_period = False
        if text is not None:
            # Reject the composed assertion; only the original selected excerpt
            # may replace it. All checks run again in project_draft below.
            try:
                qualify_claim(text, projected[-1], {**scope_context, "components": {
                    uid: scope_context.get("components", {}).get(unit["component_id"], {})},
                    "fields": {name: {**field, "evidence": [{**e, "component_id": uid}
                        for e in field["evidence"] if e["component_id"] == unit["component_id"]]}
                        for name, field in scope_context.get("fields", {}).items()}})
            except UnsupportedClaimPeriod:
                invalid_period = True
        missing_cause = text is not None and _missing_requested_cause(text, evidence, question)
        missing_list = text is not None and _missing_requested_list_item(text, evidence, question)
        missing_qualifiers = sorted(set().union(*(_measure_qualifiers(e.quote) for e in evidence)) - _measure_qualifiers(text or ''))
        if text is not None and missing_qualifiers:
            omitted_qualifiers[uid] = missing_qualifiers
        if text is None or missing_cause or missing_list or missing_qualifiers or invalid_period:
            # An explicitly logged extractive fallback, never the lossy summary.
            text = " ".join(e.quote for e in evidence)
            if len(text) > 800:
                raise ValueError("Omitted evidence unit exceeds the safe extractive fallback limit")
            fallback.append(uid)
            fallback_reasons[uid] = ("unestablished_composed_period" if invalid_period else
                'source_measure_qualifier_absent' if missing_qualifiers and representatives[uid] in chosen else
                "requested_cause_absent_from_synthesis" if missing_cause else
                "requested_list_items_absent_from_synthesis" if missing_list else "unit_omitted")
        elif (scope_context.get("components", {}).get(unit["component_id"], {}).get("scenario")
              and any(re.search(r"\btoday\b", e.quote, re.I) for e in evidence)):
            clarified = re.sub(r"(\bFrom\b.{1,160}?)\btoday\b(?=,)",
                lambda m: m[1] + "in the source report's baseline", text, flags=re.I)
            if clarified != text:
                baseline_normalizations.append({"unit_id": uid, "before": text, "after": clarified,
                    "role": "source-relative baseline; no measurement year inferred"})
                text = clarified
        claims.append({"component_id": uid, "text": text})
    projected += [c for c in mapping.components if c.status not in {"supported", "partial"}]
    # Reuse the existing citation, gap, scope, measure and number checks, now at
    # the exact evidence-unit granularity rather than an entire broad request.
    unit_mapping = mapping.model_copy(update={"components": projected})
    context = dict(scope_context)
    context["components"] = {u["unit_id"]: scope_context.get("components", {}).get(u["component_id"], {}) for u in units}
    context["fields"] = {name: {**field, "evidence": [{**e, "component_id": u["unit_id"]}
        for u in units for e in field["evidence"] if e["component_id"] == u["component_id"]]}
        for name, field in scope_context.get("fields", {}).items()}
    draft, _ = project_draft({"title": composed.title, "claims": claims}, unit_mapping, question, context)
    # Collapse only byte-identical text and ordered citations, after every unit
    # has passed validation. A repeated public claim still covers all its units.
    unique, positions, coverage = [], {}, []
    for unit, claim in zip(units, draft["claims"], strict=True):
        key = (claim["text"], tuple(claim["source_ids"]))
        if key not in positions:
            positions[key] = len(unique)
            unique.append(claim)
            coverage.append({"claim_index": len(unique) - 1, "unit_ids": [], "component_ids": []})
        group = coverage[positions[key]]
        group["unit_ids"].append(unit["unit_id"])
        if unit["component_id"] not in group["component_ids"]:
            group["component_ids"].append(unit["component_id"])
    draft["claims"] = unique
    if fallback:
        draft["warnings"] = list(dict.fromkeys([*draft["warnings"],
            "Some claims retain verbatim source excerpts because synthesis omitted evidence, its causal explanation, or used an unestablished period; review their relevance and readability."]))[:10]
    if diagnostics is not None:
        diagnostics["fallback_reasons"] = fallback_reasons
        diagnostics["source_baseline_normalizations"] = baseline_normalizations
        diagnostics["public_claim_coverage"] = coverage
        diagnostics['canonical_composition_units'] = canonical
        diagnostics['omitted_measure_qualifiers'] = omitted_qualifiers
    return draft, fallback
