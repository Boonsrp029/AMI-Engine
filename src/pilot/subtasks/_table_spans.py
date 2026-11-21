"""Offer exact requested table rows that cross ordinary reading-span boundaries."""
import hashlib
import re

from ._request_focus import _TABLE_HEADER, _YEAR, _table_focus

_US = r"(?:US\b|U\.S\.(?:A\.)?|United States\b)"
_US_DENOMINATOR = re.compile(r"\bshare of (?:total )?" + _US + r" utility-scale (?:electricity )?generation\b", re.I)
_US_HEADING = re.compile(
    r"^[ \t]*" + _US + r" utility-scale electricity generation by source, amount, and share of total in "
    r"(?P<year>[12][0-9]{3})[ \t]*\r?\n(?=Energy source\r?\n)", re.I | re.M)
_TABLE_PUBLICATION_REQUEST = re.compile(
    r"\bwhich\b[^?\n]*\bpublication\b[^?\n]*\btable\b[^?\n]*\bcite\b[^?\n]*\bdata source\b", re.I)
_TABLE_ATTRIBUTION = re.compile(
    r"^Data source:[ \t]+[^\r\n]+,\r?\n"
    r"(?P<publication>[A-Z][\w &’'().:-]{1,120})\r?\n"
    r",[ \t]*(?:January|February|March|April|May|June|July|August|September|October|November|December)"
    r"[ \t]+[12][0-9]{3}(?:;[^\r\n]+)?[ \t]*$", re.M)


def table_us_scope(anchor, span, source, year):
    """Resolve explicit U.S. scope from the heading attached to the cited table."""
    if not _US_DENOMINATOR.search(anchor):
        return None
    content = source["content"]
    header = _TABLE_HEADER.search(span["text"])
    if header is None:
        return None
    offset = span["start"] + header.start()
    headings = [h for h in _US_HEADING.finditer(content) if h.end() == offset and h["year"] == year]
    if len(headings) != 1:
        return None
    heading = headings[0]
    text = heading.group().rstrip("\r\n")
    return {"label": "U.S.", "source_id": span["source_id"],
            "content_sha256": span["content_sha256"], "start": heading.start(),
            "end": heading.start() + len(text), "text": text}


def add_table_row_spans(requests, catalog, sources, report, bindings, existing_focuses):
    """Add a row only when its complete same-record table interpretation is unique."""
    branches = {branch.subtask_id: branch for branch in report.results}
    focuses = {}
    for request in requests:
        cid = request["component_id"]
        if cid in existing_focuses or len(bindings[cid]) != 1:
            continue
        branch = branches.get(bindings[cid][0])
        if branch is None or branch.outcome != "evidence":
            continue
        candidates = []
        for source in branch.sources:
            if source.role != "support":
                continue
            record = sources[source.source_id]
            text = record["content"]
            matches = _table_focus(request["question_anchor"], text)
            if not matches:
                continue
            content_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if content_sha != source.content_sha256:
                raise ValueError("Table row source content hash changed")
            for focus in matches:
                pattern = (r"(?m)^[ \t]*" + re.escape(focus["label"])
                           + r"[ \t]*\r?\n(?:[ \t]*[1-9][ \t]*\r?\n)?[ \t]*"
                           + re.escape(focus["amount"]) + r"[ \t]*\r?\n[ \t]*"
                           + re.escape(focus["share"]) + r"[ \t]*\r?$")
                rows = list(re.finditer(pattern, text))
                if len(rows) != 1:
                    continue
                row = rows[0]
                header = _TABLE_HEADER.search(text)
                # Keep the same-record measurement period and both column headings
                # in the selected quotation. A row alone loses its temporal scope.
                periods = list(_YEAR.finditer(text[:header.start()]))
                start, end = periods[-1].start(), row.end()
                while end > start and text[end - 1].isspace():
                    end -= 1
                if end - start > 600:
                    continue
                identity = f"{source.source_id}\0{content_sha}\0{start}\0{end}"
                sid = "s_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
                span = {"source_id": source.source_id, "content_sha256": content_sha,
                        "start": start, "end": end, "text": text[start:end]}
                candidates.append((sid, span, focus))
        if len(candidates) == 1:
            sid, span, focus = candidates[0]
            if sid in catalog and catalog[sid] != span:
                raise ValueError("Evidence span identity collision")
            catalog[sid] = span
            focuses[cid] = {**focus, "span_id": sid}
    return focuses


def add_table_publication_spans(requests, catalog, sources, report, bindings, existing_focuses):
    """Index complete line-broken attribution blocks from a unique bound table."""
    branches = {branch.subtask_id: branch for branch in report.results}
    focuses = {}
    for request in requests:
        cid, anchor = request["component_id"], request["question_anchor"]
        years = set(_YEAR.findall(anchor))
        if (cid in existing_focuses or len(bindings[cid]) != 1 or len(years) != 1
                or not _TABLE_PUBLICATION_REQUEST.search(anchor)):
            continue
        branch = branches.get(bindings[cid][0])
        if branch is None or branch.outcome != "evidence":
            continue
        candidates = []
        for source in branch.sources:
            if source.role != "support":
                continue
            content = sources[source.source_id]["content"]
            headers = list(_TABLE_HEADER.finditer(content))
            attributions = list(_TABLE_ATTRIBUTION.finditer(content))
            if len(headers) != 1 or len(attributions) != 1:
                continue
            header, attribution = headers[0], attributions[0]
            heading = content[:header.start()].rstrip().splitlines()[-1:]
            if (attribution.start() < header.end() or not heading
                    or "utility-scale electricity generation" not in heading[0].casefold()
                    or set(_YEAR.findall(heading[0])) != years
                    or attribution.end() - attribution.start() > 600):
                continue
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if digest != source.content_sha256:
                raise ValueError("Table attribution source content hash changed")
            start, end = attribution.span()
            identity = f"{source.source_id}\0{digest}\0{start}\0{end}"
            sid = "s_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
            candidates.append((sid, {"source_id": source.source_id, "content_sha256": digest,
                                     "start": start, "end": end, "text": content[start:end]},
                               attribution["publication"].strip()))
        if len(candidates) == 1:
            sid, span, title = candidates[0]
            if sid in catalog and catalog[sid] != span:
                raise ValueError("Evidence span identity collision")
            catalog[sid] = span
            focuses[cid] = {"kind": "table_publication", "span_id": sid, "publication": title}
    return focuses
