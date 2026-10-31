"""Bounded synthesis units retain selected evidence without inventing new requests."""
import hashlib
import json
import re
from itertools import combinations
from typing import Literal, Union

from pydantic import create_model

from src.pilot._evidence import ComposedBrief, ComposedClaim, EvidenceQuote, project_draft, supported_components
from src.pilot._scope import UnsupportedClaimPeriod, qualify_claim, validate_claim_measure_and_numbers
from src.pilot._entity_comparison import request_spec, missing_comparison_conclusion, render_literal_comparison
from src.pilot._quantities import quantity_pairs


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
    anchors = {c.component_id: c.question_anchor for c in supported_components(mapping)}
    while len(groups) < 5:
        candidates = [i for i, group in enumerate(groups) if len(group["evidence"]) > 1
                      and not request_spec(anchors[group['component_id']])]
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


def payload(mapping, as_of, scope_context=None, *, excluded_units=()):
    # Global title scope must not be offered as factual scope for every unit.
    context = scope_context or {}
    units = [{k: v for k, v in unit.items() if k not in {'identity_sha256', 'scope_citation_ids'}}
             for unit in _model_units(mapping, context, excluded_units)]
    # Requests describe the task, never factual evidence. Keep mapper summaries
    # and unrestricted gap text out; preserve every alias of shared evidence.
    active = {origin['component_id'] for unit in units for origin in unit['origins']}
    requests = [{"component_id": c.component_id, "question_anchor": c.question_anchor, "status": c.status}
                for c in supported_components(mapping) if c.component_id in active]
    return {"as_of": as_of, "requests": requests, "units": units}


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


def _model_units(mapping, scope_context, excluded_units):
    units = canonical_units(mapping, scope_context)
    excluded = set(excluded_units)
    if not excluded.issubset({unit['unit_id'] for unit in units}):
        raise ValueError('Unknown application-owned composition unit')
    return [unit for unit in units if unit['unit_id'] not in excluded]


def literal_units(mapping, scope_context, sources):
    """Own a canonical unit only when every origin has the same literal answer."""
    components = {component.component_id: component for component in mapping.components}
    result = {}
    for unit in canonical_units(mapping, scope_context):
        if any(_measure_qualifiers(e['quote']) for e in unit['evidence']):
            continue
        answers = []
        for origin in unit['origins']:
            component = components[origin['component_id']].model_copy(update={
                'evidence': [EvidenceQuote.model_validate(e) for e in unit['evidence']]})
            answer = render_literal_comparison(component, sources)
            if answer is None:
                break
            answers.append(answer)
        if len(answers) == len(unit['origins']) and len({a['text'] for a in answers}) == 1:
            result[unit['unit_id']] = {**answers[0], 'unit_id': unit['unit_id'], 'origins': unit['origins']}
    return result


def response_schema(mapping, scope_context=None, *, excluded_units=()):
    if not 1 <= len(canonical_units(mapping, scope_context)) <= 5:
        raise ValueError("Composition requires one to five evidence units")
    units = _model_units(mapping, scope_context, excluded_units)
    if not units:
        return create_model('ComposedBrief', __base__=UnitBrief,
            title=(Literal['Analyst research brief'], ...), claims=(tuple[()], ...))
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
        match = re.search(r"(?:\b(?:supported by|driven (?:primarily )?by|due to|because|reflect(?:s|ed|ing)|(?:as )?a result of)|,\s*as)\s+(.+)", quote.quote, re.I)
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


def _missing_requested_value_context(text, component, period=''):
    """Detect literal omissions only; the existing source excerpt supplies facts."""
    if not re.search(r'\b(?:which|what)\b.{0,60}\b(?:led|leads|leading|largest|top|first)\b'
                     r'.{0,30}\bby\s+(?:application\s+)?value\b', component.question_anchor, re.I):
        return False
    quoted = ' '.join(e.quote for e in component.evidence)
    if not re.search(r'\b(?:led|leads|leading|largest|rankings?)\b', quoted, re.I):
        return False
    expected = {pair for pair in quantity_pairs(quoted) if pair[0] in {'baht', 'usd'}}
    if not expected:
        return False
    validate_claim_measure_and_numbers(text, component, component.question_anchor, period)
    percentages = lambda value: {re.sub(r'\s+', '', m[0]) for m in re.finditer(r'\d+(?:\.\d+)?\s*%', value)}
    return (not expected.issubset(quantity_pairs(text))
        or not percentages(quoted).issubset(percentages(text))
        or not re.search(r'\b(?:led|leads|leading|largest|rankings?)\b', text, re.I))


def project(value, mapping, question, scope_context, diagnostics=None, *, source_records=None):
    composed = UnitBrief.model_validate(value)
    units = composition_units(mapping)
    canonical = canonical_units(mapping, scope_context)
    by_id = {unit['unit_id']: unit for unit in canonical}
    representatives = {origin['unit_id']: unit['unit_id'] for unit in canonical for origin in unit['origins']}
    rendered = literal_units(mapping, scope_context, source_records) if source_records is not None else {}
    rendered_origins = {origin['unit_id']: item for item in rendered.values() for origin in item['origins']}
    chosen = {}
    for claim in composed.claims:
        if claim.unit_id in rendered:
            raise ValueError('Composed claim attempts to replace an application-owned project comparison')
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
    comparison_conclusions = []
    for unit in units:
        uid = unit["unit_id"]
        evidence = [EvidenceQuote.model_validate(e) for e in unit["evidence"]]
        projected.append(components[unit["component_id"]].model_copy(update={"component_id": uid, "evidence": evidence}))
        is_literal = uid in rendered_origins
        text = rendered_origins[uid]['text'] if is_literal else chosen.get(representatives[uid])
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
        missing_cause = not is_literal and text is not None and _missing_requested_cause(text, evidence, question)
        missing_list = not is_literal and text is not None and _missing_requested_list_item(text, evidence, question)
        missing_value = text is not None and not invalid_period and _missing_requested_value_context(
            text, projected[-1], scope_context.get('components', {}).get(unit['component_id'], {}).get('period', ''))
        missing_qualifiers = sorted(set().union(*(_measure_qualifiers(e.quote) for e in evidence)) - _measure_qualifiers(text or ''))
        if text is not None and missing_qualifiers:
            omitted_qualifiers[uid] = missing_qualifiers
        if text is None or missing_cause or missing_list or missing_value or missing_qualifiers or invalid_period:
            # An explicitly logged extractive fallback, never the lossy summary.
            text = " ".join(e.quote for e in evidence)
            if len(text) > 800:
                raise ValueError("Omitted evidence unit exceeds the safe extractive fallback limit")
            fallback.append(uid)
            fallback_reasons[uid] = ("unestablished_composed_period" if invalid_period else
                'source_measure_qualifier_absent' if missing_qualifiers and representatives[uid] in chosen else
                "requested_cause_absent_from_synthesis" if missing_cause else
                "requested_value_context_absent_from_synthesis" if missing_value else
                "requested_list_items_absent_from_synthesis" if missing_list else "unit_omitted")
        elif (scope_context.get("components", {}).get(unit["component_id"], {}).get("scenario")
              and any(re.search(r"\btoday\b", e.quote, re.I) for e in evidence)):
            clarified = re.sub(r"(\bFrom\b.{1,160}?)\btoday\b(?=,)",
                lambda m: m[1] + "in the source report's baseline", text, flags=re.I)
            if clarified != text:
                baseline_normalizations.append({"unit_id": uid, "before": text, "after": clarified,
                    "role": "source-relative baseline; no measurement year inferred"})
                text = clarified
        conclusion = missing_comparison_conclusion(text, projected[-1])
        if conclusion:
            before = text
            text = text.rstrip() + (' ' if text.rstrip().endswith(('.', '!', '?')) else '. ') + conclusion['clause']
            if len(text) > 800:
                raise ValueError('Explicit project conclusion exceeds the claim limit')
            comparison_conclusions.append({'unit_id': uid, 'before': before, 'after': text, **conclusion})
        claims.append({"component_id": uid, "text": text})
    projected += [c for c in mapping.components if c.status not in {"supported", "partial"}]
    # Reuse the existing citation, gap, scope, measure and number checks, now at
    # the exact evidence-unit granularity rather than an entire broad request.
    unit_mapping = mapping.model_copy(update={"components": projected})
    context = dict(scope_context)
    context['request_component_ids'] = {u['unit_id']: u['component_id'] for u in units}
    context["components"] = {u["unit_id"]: scope_context.get("components", {}).get(u["component_id"], {}) for u in units}
    context["fields"] = {name: {**field, "evidence": [{**e, "component_id": u["unit_id"]}
        for u in units for e in field["evidence"] if e["component_id"] == u["component_id"]]}
        for name, field in scope_context.get("fields", {}).items()}
    draft, _ = project_draft({"title": composed.title, "claims": claims}, unit_mapping, question, context)
    # Every origin has already passed validation. A duplicate assertion may
    # retain multiple citations; this does not establish source independence.
    unique, positions, cross_sources, coverage, merged = [], {}, {}, [], []
    for unit, claim in zip(units, draft["claims"], strict=True):
        key = (claim["text"], tuple(claim["source_ids"]))
        signature = (unit['component_id'], claim['text'], tuple(e['quote'] for e in unit['evidence']),
                     json.dumps(scope_context.get('components', {}).get(unit['component_id'], {}), sort_keys=True))
        index = positions.get(key)
        if index is None and signature in cross_sources:
            candidate = cross_sources[signature]
            citations = list(dict.fromkeys([*unique[candidate]['source_ids'], *claim['source_ids']]))
            if len(citations) <= 5:
                index = candidate
                unique[index]['source_ids'] = citations
                merged.append({'claim_index': index, 'unit_id': unit['unit_id'],
                               'retained_source_ids': list(citations)})
        if index is None:
            index = len(unique)
            unique.append({**claim, 'source_ids': list(claim['source_ids'])})
            coverage.append({"claim_index": index, "unit_ids": [], "component_ids": []})
        positions[key] = index
        cross_sources[signature] = index
        group = coverage[index]
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
        diagnostics['merged_duplicate_citations'] = merged
        diagnostics['literal_comparison_conclusions'] = comparison_conclusions
        diagnostics['source_rendered_comparisons'] = list(rendered.values())
    return draft, fallback
