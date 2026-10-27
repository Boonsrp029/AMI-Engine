"""Explicit, corpus-pinned ranking/context policy, separate from fact validation."""
import json
import re
from pathlib import Path

from src.agents.local_retriever import _bm25_scores, _tokens


LEXICAL_VERSION = "pilot-intent-lexical-v1"
_STOP = set("a an the and or in on for of to from at by with as which what why how did do does is are was were has have had according its their it that this those these than then while s".split())
_MONTHS = set("january february march april may june july august september october november december".split())
_FORMS = {"seasonally": "seasonal", "adjusted": "adjust", "adjustment": "adjust",
          "increased": "increase", "decreased": "decrease", "grew": "grow", "rose": "rise", "fell": "fall",
          "remained": "remain", "stayed": "stay", "changed": "change"}


def lexical_terms(text, tourism=False):
    """Small English ranking vocabulary; never used to rewrite source evidence."""
    result = []
    for token in _tokens(text):
        token = _FORMS.get(token, token)
        if len(token) > 4 and token.endswith("ies"):
            token = token[:-3] + "y"
        elif len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        if tourism:
            token = {"tourism": "visitor", "tourist": "visitor", "receipt": "revenue"}.get(token, token)
        result.append(token)
    return result


def rank_evidence(query, sources, limit, requested_query=None):
    """Fuse user intent with the planner query; reject date-only token matches.

    This is lexical relevance, not entailment or a financial-measure conversion.
    The lower-level retriever and the corpus-pinned legacy profile stay unchanged.
    """
    intent = requested_query or query
    tourism = bool(re.search(r"\b(?:tourism|tourists?|visitors?)\b", intent, re.I))
    terms = list(dict.fromkeys(t for t in lexical_terms(intent + " " + query, tourism) if t not in _STOP and len(t) > 1))
    primary = [t for t in terms if t not in _MONTHS and not t.isdigit()]
    metadata = [t for t in terms if t not in primary]
    records = list(sources)
    documents = [lexical_terms(record["content"], tourism) for record in records]
    scores = _bm25_scores(" ".join(primary), documents)
    metadata_scores = _bm25_scores(" ".join(metadata), documents)
    minimum = 1 if primary else 0
    scored = []
    for index, (record, doc, score, extra) in enumerate(zip(records, documents, scores, metadata_scores)):
        matched = sorted(set(primary) & set(doc))
        # Calendar matches cannot make an otherwise unrelated snippet eligible.
        if not minimum or len(matched) < minimum or score <= 0:
            continue
        value = score * (1 + len(matched) / max(len(primary), 1)) + 0.1 * extra
        scored.append((value, index, record, matched))
    scored.sort(key=lambda row: (-row[0], row[1]))
    selected = [row[2] for row in scored[:limit]]
    return selected, {"policy": LEXICAL_VERSION, "original_query": query, "requested_query": intent,
        "effective_query": " ".join(primary), "ranking_metadata_terms": metadata,
        "tourism_vocabulary_active": tourism, "minimum_matched_terms": minimum,
        "eligible_records": len(scored), "source_ids": [record["source_id"] for record in selected],
        "ranked_preview": [{"source_id": row[2]["source_id"], "score": row[0], "matched_terms": row[3]} for row in scored[:10]],
        "scope_note": "Ranking vocabulary does not establish scope, dates, causality or semantic support; original requests and exact source text remain authoritative."}


def load_profile(path, corpus_sha):
    path = Path(path)
    if not path.is_file():
        return None
    profile = json.loads(path.read_text(encoding="utf-8"))
    return profile if profile.get("corpus_sha256") == corpus_sha else None


def contrast_evidence_choices(catalog, sources, requests):
    """Keep both literal views of an explicitly requested export contrast.

    Requires a numbered list immediately after an export-decline sentence and an
    explicit contrasting export-increase sentence in the same retrieved record.
    This constrains selection identity; it does not establish semantic support.
    An empty evidence selection remains legal for a genuinely unresolved request.
    """
    result = {}
    for request in requests:
        anchor = request["question_anchor"]
        if not (re.search(r"\bexport\w*\s+(?:categories|products|groups)\b", anchor, re.I)
                and re.search(r"\bopposite directions\b", anchor, re.I)):
            continue
        by_source = {}
        for sid, span in catalog.items():
            text = span["text"]
            views = by_source.setdefault(span["source_id"], {"declining_categories": [], "increasing_categories": []})
            preceding = sources[span["source_id"]]["content"][:span["start"]].rstrip()
            previous_sentence = re.split(r"(?<=[.!?;])\s+", preceding)[-1]
            if (len(re.findall(r"\b\d+\)", text)) >= 2
                    and re.search(r"\bexports?\b.{0,180}\b(?:decreased|declined|fell)\b", previous_sentence, re.I)):
                views["declining_categories"].append(sid)
            if re.search(r"^(?:However|By contrast|In contrast),?\s+exports?\b.{0,100}\b(?:increased|rose|grew)\b", text, re.I):
                views["increasing_categories"].append(sid)
        complete = [views for views in by_source.values() if all(views.values())]
        # Ambiguous parallel records require normal mapping, not an arbitrary choice.
        if len(complete) == 1:
            result[request["component_id"]] = [{"role": role, "span_ids": ids, "allow_extra": False}
                for role, ids in complete[0].items()]
    return result


def effective_query(query, profile):
    text = query
    removed = []
    for phrase in sorted(profile["ranking_metadata_phrases"], key=len, reverse=True):
        pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"
        if re.search(pattern, text, re.I):
            text = re.sub(pattern, " ", text, flags=re.I)
            removed.append(phrase)
    words = list(dict.fromkeys(t for t in _tokens(text) if t not in set(profile["stop_terms"])))
    # An empty content query does not authorize replacing the task with arbitrary facts.
    return " ".join(words), removed


def select_catalog(catalog, query, profile):
    ids = list(catalog)
    scores = _bm25_scores(query, [_tokens(catalog[sid]["text"]) for sid in ids])
    # Prefer explanatory sentences over chart labels without excluding tables.
    predicate = re.compile(r"\b(?:increased?|decreased?|grew|grows?|rises?|rose|was|were|is|are|remained|moderated|supported|driven|projected|projects?|accounts?|meets?|represents?)\b", re.I)
    scores = [score if predicate.search(catalog[sid]["text"]) else score * 0.25 for sid, score in zip(ids, scores)]
    ranked = sorted(range(len(ids)), key=lambda i: (-scores[i], i))
    selected, used = set(), 0
    for i in ranked:
        size = len(catalog[ids[i]]["text"])
        if scores[i] <= 0 or used + size > profile["maximum_evidence_characters"]:
            continue
        selected.add(ids[i])
        used += size
        if len(selected) == profile["maximum_evidence_spans"]:
            break
    # Keep original source/offset order in the prompt after selecting by relevance.
    result = {sid: span for sid, span in catalog.items() if sid in selected}
    return result, {"policy": profile["version"], "effective_query": query,
        "full_span_count": len(catalog), "selected_span_ids": list(result), "selected_characters": used,
        "maximum_characters": profile["maximum_evidence_characters"], "maximum_spans": profile["maximum_evidence_spans"],
        "non_declarative_weight": 0.25,
        "omitted_span_ids": [sid for sid in ids if sid not in selected]}


def request_evidence_choices(catalog, sources, requests, profile):
    """For explicit change/activity subject slots, retain available overview/detail views.

    This binds evidence identity and literal subject coverage, not semantic support.
    It is inactive for other request grammars or when both views are unavailable.
    """
    result = {}
    change = re.compile(r"\b(?:increased?|decreased?|higher|lower|improved?|remained|moderated|grew|grows?|rose|rises?)\b", re.I)
    for request in requests:
        anchor = request["question_anchor"]
        if re.search(r"\belectricity demand\b", anchor, re.I) and re.search(r"\bproject\w*\b", anchor, re.I):
            horizons = re.findall(r"\b(?:by|to|until)\s+(\d{4})\b", anchor, re.I)
            scenarios = re.findall(r"\b(?:STEPS|APS|NZE)\b", anchor)
            views = {"annual_change": [], "level_projection": []}
            if len(set(horizons)) == 1 and len(set(scenarios)) == 1:
                horizon, scenario = horizons[0], scenarios[0]
                for sid, span in catalog.items():
                    text = span["text"]
                    if (not re.search(r"\belectricity demand\b", text, re.I) or horizon not in text
                            or not re.search(r"\b" + scenario + r"\b", text)):
                        continue
                    if re.search(r"\d+(?:\.\d+)?\s*%", text) and re.search(r"\b(?:annually|annual|per year)\b", text, re.I):
                        views["annual_change"].append(sid)
                    if re.search(r"\d\s*(?:TWh|GWh|MWh)\b", text) and re.search(r"\b(?:rise\w*|grow\w*|increas\w*|fall\w*|declin\w*)\b", text, re.I):
                        views["level_projection"].append(sid)
                if all(views.values()):
                    shared_sources = ({catalog[sid]["source_id"] for sid in views["annual_change"]}
                                      & {catalog[sid]["source_id"] for sid in views["level_projection"]})
                    if not shared_sources:
                        continue
                    primary = next(source_id for source_id in sources if source_id in shared_sources)
                    result[request["component_id"]] = [{"role": role,
                        "span_ids": [sid for sid in candidates if catalog[sid]["source_id"] == primary], "allow_extra": False}
                        for role, candidates in views.items()]
                    continue
        if "instruction" not in request:
            continue
        subject, _ = effective_query(request["question_anchor"], profile)
        phrase = r"\b" + r"\W+".join(re.escape(t) for t in _tokens(subject)) + r"\b"
        if not subject:
            continue
        views = {"overview": [], "detail": []}
        for sid, span in catalog.items():
            matches = list(re.finditer(phrase, span["text"], re.I))
            if not any(change.search(span["text"][max(0, m.start() - 40):min(len(span["text"]), m.end() + 120)]) for m in matches):
                continue
            source = sources[span["source_id"]]["content"].casefold()
            role = "overview" if any(marker.casefold() in source for marker in profile["overview_markers"]) else "detail"
            views[role].append(sid)
        if all(views.values()):
            def document(sid):
                source = sources[catalog[sid]["source_id"]]
                return tuple(source.get(k) for k in ("doc_name", "url", "published"))
            common = {document(sid) for sid in views["overview"]} & {document(sid) for sid in views["detail"]}
            if len(common) == 1 and all(next(iter(common))[:2]):
                document_id = next(iter(common))
                result[request["component_id"]] = [{"role": role, "span_ids": [sid for sid in ids if document(sid) == document_id]}
                    for role, ids in views.items()]
    return result
