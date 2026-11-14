"""Concurrent title scope coverage; lexical checks are not semantic entailment."""
import hashlib
import re

from .._evidence import supported_components
from .._scope import same_pinned_document


TITLE_SCOPE_VERSION = "cq-title-scope-v1"
_LOCATIVE = re.compile(r"\b(?i:in|across|within)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b")
_QUALIFIERS = {"Province","Region","District","City","Country","County","State","Town"}


def normal(value):
    return " ".join(value.split())


def contains(text, phrase):
    return bool(re.search(r"(?<!\w)"+re.escape(normal(phrase))+r"(?!\w)",normal(text),re.I))


def render(title, scopes):
    missing = [s for s in scopes if s and normal(s).casefold() not in normal(title).casefold()]
    suffix = " ("+", ".join(missing)+")" if missing else ""
    return title[:160-len(suffix)].rstrip()+suffix


def qualify_title(draft, raw_title, mapping, sources, resolution=None):
    """Preserve a common label or suppress only its title suffix before safety.

    Document identity supports contextual qualification, not geographic truth.
    Context-based retention therefore carries an explicit review warning.
    Claims, source selection and the original mapper resolution remain unchanged.
    """
    geo = mapping.geography
    diagnostics = {"version":TITLE_SCOPE_VERSION,"candidate":geo,"title_before":draft["title"],
                   "semantic_applicability_proven":False,"evidence_coverage":[]}
    if not geo or not draft["claims"]:
        diagnostics.update(status="not_applicable",title_after=draft["title"])
        return draft,diagnostics
    evidence = [e for c in supported_components(mapping) for e in c.evidence]
    anchors = {e.source_id for e in evidence if contains(e.quote,geo)}
    if resolution is not None:
        if resolution.get("status") != "known" or resolution.get("value") != geo:
            raise ValueError("Title geography resolution differs from validated mapping")
        for span in resolution.get("evidence",[]):
            source = sources.get(span.get("source_id"))
            if (source is None or span.get("content_sha256") != source["content_sha256"]
                    or type(span.get("start")) is not int or type(span.get("end")) is not int
                    or not 0 <= span["start"] < span["end"] <= len(source["content"])
                    or source["content"][span["start"]:span["end"]] != span.get("quote")
                    or not contains(span["quote"],geo)):
                raise ValueError("Title geographic context is not exact pinned source evidence")
            anchors.add(span["source_id"])
    uncovered, context = False, False
    for item in evidence:
        locations = set(_LOCATIVE.findall(item.quote))-_QUALIFIERS
        conflict = any(normal(place).casefold()!=normal(geo).casefold() for place in locations)
        if conflict:
            basis = "different_explicit_locative"
        elif contains(item.quote,geo):
            basis = "literal_in_selected_quote"
        elif any(same_pinned_document(sources[item.source_id],sources[sid]) for sid in anchors):
            basis = "same_pinned_document_context"
            context = True
        else:
            basis = "not_established_for_selected_quote"
        uncovered |= basis in {"different_explicit_locative","not_established_for_selected_quote"}
        diagnostics["evidence_coverage"].append({"source_id":item.source_id,
            "quote_sha256":hashlib.sha256(item.quote.encode("utf-8")).hexdigest(),"basis":basis})
    projected = {**draft,"warnings":list(draft["warnings"])}
    if uncovered:
        if draft["title"] != render(raw_title,[geo,mapping.period]):
            raise ValueError("Unexpected title projection; cannot safely remove partial geography")
        projected["title"] = render(raw_title,[mapping.period])
        diagnostics["status"] = "suppressed_partial_geography"
    elif context:
        projected["warnings"].append("Title geography uses the same pinned document; verify its applicability to every claim before approval.")
        diagnostics["status"] = "retained_document_context_requires_review"
    else:
        diagnostics["status"] = "retained_literal_common_geography"
    diagnostics["title_after"] = projected["title"]
    return projected,diagnostics
