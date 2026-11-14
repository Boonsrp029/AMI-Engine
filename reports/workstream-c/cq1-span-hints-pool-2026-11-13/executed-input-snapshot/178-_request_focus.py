"""Bind recognizable table and ratio requests to exact retrieved spans."""
import re

from src.agents.local_retriever import _bm25_scores, _tokens

_YEAR = re.compile(r"\b[12][0-9]{3}\b")
_TABLE_HEADER = re.compile(r"^Energy source\r?\n(?P<unit>(?:Million |Billion )?(?:kWh|MWh|GWh|TWh))"
                           r"\r?\nShare of total\r?$", re.I | re.M)
_NUMBER = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
_RATIO = re.compile(r"(?P<name>[\w -]+?) divides (?P<numerator>[^.;!?\n]+?) by "
                    r"(?P<denominator>[^.;!?\n]+)\.", re.I)
_ROW_REQUEST = re.compile(
    r"^(?:what (?:was|were|is|are) |give |report )?(?:the )?"
    r"(?P<label>.+?) (?:generation|amount) and (?:its|the) share\b", re.I)
_QUERY_FILLER = frozenset(
    "a an and are as at be by can did do does for from had has have how in is it its "
    "let of on or some than that the their them they to was were what when where which who will with".split()
)


def _normal(text):
    return " ".join(text.casefold().split())


def _contains(text, phrase):
    return re.search(r"(?<!\w)" + re.escape(_normal(phrase)) + r"(?!\w)", _normal(text)) is not None


def _table_focus(anchor, text):
    years = set(_YEAR.findall(anchor))
    request = _ROW_REQUEST.match(_normal(anchor))
    if len(years) != 1 or request is None:
        return []
    header = _TABLE_HEADER.search(text)
    if (header is None or set(_YEAR.findall(text[:header.start()])) != years
            or not _contains(text[:header.start()], "utility-scale electricity generation")):
        return []
    lines = [line.strip() for line in text[header.end():].strip().splitlines()]
    if len(lines) >= 3 and lines[0].casefold().startswith("total ") and _NUMBER.fullmatch(lines[1]) and not lines[2].endswith("%"):
        lines = lines[2:]
    matches = []
    index = 0
    while index + 2 < len(lines):
        label = lines[index]
        index += 1
        if (index + 2 < len(lines) and re.fullmatch(r"[1-9]", lines[index])
                and _NUMBER.fullmatch(lines[index + 1]) and lines[index + 2].endswith("%")):
            index += 1  # A separately extracted footnote marker preceding both columns.
        amount, share = lines[index:index + 2]
        index += 2
        if not label or not _NUMBER.fullmatch(amount) or not share.endswith("%") or not _NUMBER.fullmatch(share[:-1]):
            break
        key = _normal(label)
        total = re.fullmatch(r"([a-z]{3,}[^suai]s) \(total\)", key)
        # Match the entire requested row subject. A single-word aggregate can
        # use its singular or plural name, but a child row keeps its full label.
        alias = {total[1], total[1].removesuffix("s")} if total else set()
        if request["label"] == key or request["label"] in alias:
            matches.append(dict(kind="table_row", label=label, amount=amount, share=share,
                                unit=header["unit"], year=next(iter(years)),
                                denominator="total utility-scale electricity generation"))
    return matches


def _ratio_focus(anchor, text):
    roles = set(re.findall(r"\b(?:numerator|denominator)\b", anchor.casefold()))
    match = _RATIO.fullmatch(text.strip())
    if len(roles) != 1 or match is None or not _contains(anchor, match["name"]):
        return []
    role = next(iter(roles))
    return [dict(kind="ratio_operand", ratio=match["name"], role=role, operand=match[role])]


def request_focus(requests, catalog, report, bindings):
    """Offer a focus only for one unambiguous match in a single bound branch."""
    branches = {result.subtask_id: result for result in report.results}
    result = {}
    for request in requests:
        cid = request["component_id"]
        if len(bindings[cid]) != 1:
            continue
        branch = branches.get(bindings[cid][0])
        if branch is None or branch.outcome != "evidence":
            continue
        allowed = {source.source_id for source in branch.sources if source.role == "support"}
        anchor = request["question_anchor"]
        matches = [{**focus, "span_id": sid} for sid, span in catalog.items() if span["source_id"] in allowed
                   for focus in (*_table_focus(anchor, span["text"]), *_ratio_focus(anchor, span["text"]))]
        if len(matches) == 1:
            result[cid] = matches[0]
    return result


def relevance_hints(requests, catalog, report, bindings, focuses):
    """Suggest query-relevant exact spans within each request's retrieved support."""
    support = {branch.subtask_id: {source.source_id for source in branch.sources if source.role == "support"}
               for branch in report.results if branch.outcome == "evidence"}
    hints = {}
    for request in requests:
        cid = request["component_id"]
        if cid in focuses:
            continue
        terms = list(dict.fromkeys(t for t in _tokens(request["question_anchor"]) if t not in _QUERY_FILLER))
        if len(terms) < 2:
            continue
        allowed = set().union(*(support.get(bid, set()) for bid in bindings[cid]))
        candidates = [(sid, _tokens(span["text"])) for sid, span in catalog.items() if span["source_id"] in allowed]
        if not candidates:
            continue
        scores = _bm25_scores(" ".join(terms), [tokens for _, tokens in candidates])
        ranked = sorted(zip(scores, candidates, strict=True), key=lambda item: (-item[0], item[1][0]))
        relevant = [sid for score, (sid, tokens) in ranked if score > 0 and len(set(terms).intersection(tokens)) >= 2]
        if relevant:
            hints[cid] = relevant[:2]
    return hints


def focused_text(focus):
    if focus["kind"] == "ratio_operand":
        return f"The {focus['role']} is {focus['operand']}."
    return (f"In {focus['year']}, the table gives {focus['label']} generation in {focus['unit']} as "
            f"{focus['amount']} and its share of {focus['denominator']} as {focus['share']}.")


def validate_focused_claims(claims, focuses):
    """Keep the raw claim bound to the recognized operand or table row."""
    for cid, focus in focuses.items():
        matching = [claim["text"] for claim in claims if claim["component_id"] == cid]
        if len(matching) != 1:
            raise ValueError("Focused request requires one raw claim")
        allowed = {_normal(focused_text(focus))}
        if focus["kind"] == "ratio_operand":
            name = re.sub(r"^the\s+", "", focus["ratio"], flags=re.I)
            allowed.add(_normal(f"The {focus['role']} of the {name} is {focus['operand']}."))
        if _normal(matching[0]) not in allowed:
            raise ValueError("Raw claim does not retain the requested table row or ratio operand")
