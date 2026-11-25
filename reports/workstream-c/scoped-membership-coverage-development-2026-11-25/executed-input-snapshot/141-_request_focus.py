"""Bind recognizable requests to exact retrieved spans."""
import re

from src.agents.local_retriever import _bm25_scores, _tokens
from .._quantities import _number, _SCALES
from ._request_coverage import source_field_focus

_YEAR = re.compile(r"\b[12][0-9]{3}\b")
_TABLE_HEADER = re.compile(r"^Energy source\r?\n(?P<unit>(?:Million |Billion )?(?:kWh|MWh|GWh|TWh))"
                           r"\r?\nShare of total\r?$", re.I | re.M)
_NUMBER = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
_TABLE_NUMBER = re.compile(r"-?" + _NUMBER.pattern)
_RATIO = re.compile(r"(?P<name>[\w -]+?) divides (?P<numerator>[^.;!?\n]+?) by "
                    r"(?P<denominator>[^.;!?\n]+)\.", re.I)
_ROW_REQUEST = re.compile(
    r"^(?:what (?:was|were|is|are) |give |report )?(?:the )?"
    r"(?P<label>.+?) (?:generation|amount) and (?:its|the) share\b", re.I)
_CONVERSION_REQUEST = re.compile(
    r"how many (?P<first>[a-z]+) and (?P<second>[a-z]+) "
    r"(?:does [\w ]+ say )?are equivalent to one (?P<base>[a-z]+)\??", re.I)
_CONVERSION_STATEMENT = re.compile(
    rf"^[ \t]*(?:(?P<label>[a-z]+) \((?P<symbol>[a-z]+)\): )?"
    rf"(?:one|1) (?P<base>[a-z]+) (?:is|equals) "
    rf"(?P<first_value>{_NUMBER.pattern}) (?P<first>[a-z]+)(?:,? or| and) "
    rf"(?P<second_value>{_NUMBER.pattern}) (?P<second>[a-z]+)\.[ \t]*\r?$",
    re.I | re.M)
_CONVERSION_UNITS = {"megawatt": "mw", "megawatts": "mw", "kilowatt": "kw", "kilowatts": "kw",
                     "watt": "w", "watts": "w", "hours": "hour", "minutes": "minute", "seconds": "second"}
_POWER_NAMES = {"w": "watt", "kw": "kilowatt", "mw": "megawatt", "gw": "gigawatt", "tw": "terawatt"}
_SINGLE_POWER_REQUEST = re.compile(
    r"how many (?P<target>(?:kilo|mega|giga|tera)?watts) (?:are equivalent to |"
    r"does [\w .-]+? say are in )one (?P<base>(?:kilo|mega|giga|tera)?watt)(?: in [^?]+)?\?")
_SINGLE_POWER_STATEMENT = re.compile(
    rf"^[ \t]*(?:one|1) (?P<base>[a-z]+) (?:is equal to|equals|is) "
    rf"(?P<value>{_NUMBER.pattern}) (?P<unit>[a-z]+)\.[ \t]*\r?$", re.I | re.M)
_CLAIM_VALUE = rf"(?:{_NUMBER.pattern}|one)(?: thousand| million| billion| trillion)?"
_CAPACITY_REQUEST = re.compile(
    r"what minimum (?P<measure>total (?:[a-z]+ )*capacity) [^?]+, "
    r"in (?P<first>[a-z]+) and (?P<second>[a-z]+)\?")
_CAPACITY_THRESHOLD = re.compile(
    rf"\bat least (?P<quantity_pair>{_CLAIM_VALUE} (?P<first>[a-z]+) "
    rf"\((?:or )?{_CLAIM_VALUE} (?P<second>[a-z]+)\)) "
    r"of (?P<measure>total (?:[a-z]+ )*capacity)\b", re.I)
_CONVERSION_CLAIM = re.compile(
    rf"(?:(?:according to [\w .-]+,|the [\w -]+ (?:says|states)(?: that)?) )?"
    rf"(?:one|1) (?P<base>[a-z]+) (?:is equivalent to|is equal to|is|equals) "
    rf"(?P<value>{_CLAIM_VALUE}) (?P<target>[a-z]+)\.", re.I)
REQUIRED_TARGET_FIELDS = ("target_1", "target_2")
_MEMBERSHIP_REQUEST = re.compile(r"which [\w -]+ does [\w .-]+ include in the (?P<category>[\w -]+) category\??")
_MEMBERSHIP_GROUP = r"[a-z][a-z -]*"
_QUERY_FILLER = frozenset(
    "a an and are as at be by can did do does for from had has have how in is it its "
    "let of on or some than that the their them they to was were what when where which who will with".split()
)
_DEPENDENT_QUESTION = re.compile(
    r"^(?:who|where|when|how|what|which)\b.*\b(?:these|those|such|them|their)\b", re.I)


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
    if len(lines) >= 3 and lines[0].casefold().startswith("total ") and _TABLE_NUMBER.fullmatch(lines[1]) and not lines[2].endswith("%"):
        lines = lines[2:]
    matches = []
    index = 0
    while index + 2 < len(lines):
        label = lines[index]
        index += 1
        if (index + 2 < len(lines) and re.fullmatch(r"[1-9]", lines[index])
                and _TABLE_NUMBER.fullmatch(lines[index + 1]) and lines[index + 2].endswith("%")):
            index += 1  # A separately extracted footnote marker preceding both columns.
        amount, share = lines[index:index + 2]
        index += 2
        if not label or not _TABLE_NUMBER.fullmatch(amount) or not share.endswith("%") or not _TABLE_NUMBER.fullmatch(share[:-1]):
            break
        key = _normal(label)
        total = re.fullmatch(r"([a-z]{3,}[^suai]s) \(total\)", key)
        # Match the whole subject, allowing the table's aggregate suffix to
        # be omitted. Keep the existing singular alias for single words.
        subject = request["label"]
        if (subject == key or subject == key.removesuffix(" (total)")
                or (total and subject == total[1].removesuffix("s"))):
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


def _conversion_focus(anchor, text):
    request = _CONVERSION_REQUEST.fullmatch(_normal(anchor))
    if request is None:
        return []

    base = _conversion_unit(request["base"])
    targets = {_conversion_unit(request["first"]), _conversion_unit(request["second"])}
    if len(targets) != 2 or base in targets:
        return []
    return [{"kind": "unit_conversion", "base_unit": base,
             "targets": {unit: format(value.normalize(), "f")
                         for unit, value in _conversion_pairs(match).items()}}
            for match in _CONVERSION_STATEMENT.finditer(text)
            if _conversion_unit(match["base"]) == base
            and {_conversion_unit(match["first"]), _conversion_unit(match["second"])} == targets
            and (not match["label"] or _conversion_unit(match["label"]) == _conversion_unit(match["symbol"]) == base)]


def _conversion_unit(word):
    word = word.casefold()
    return _CONVERSION_UNITS.get(word, word)


def _power_unit(word):
    singular = word.casefold().removesuffix("s")
    return next((symbol for symbol, name in _POWER_NAMES.items() if singular == name), singular)


def _single_power_focus(anchor, text):
    """Bind a directed single-unit request to a literal equivalence in the same span."""
    request = _SINGLE_POWER_REQUEST.fullmatch(_normal(anchor))
    if request is None:
        return []
    base, target = _power_unit(request["base"]), _power_unit(request["target"])
    if base == target:
        return []
    values = []
    for match in _CONVERSION_STATEMENT.finditer(text):
        if (_power_unit(match["base"]) == base
                and (not match["label"] or _power_unit(match["label"]) == _power_unit(match["symbol"]) == base)):
            values.extend(_number(match[f"{slot}_value"]) for slot in ("first", "second")
                          if _power_unit(match[slot]) == target)
    values.extend(_number(match["value"]) for match in _SINGLE_POWER_STATEMENT.finditer(text)
                  if _power_unit(match["base"]) == base and _power_unit(match["unit"]) == target)
    return [{"kind": "single_power_conversion", "base": _POWER_NAMES[base],
             "target": _POWER_NAMES[target] + ("s" if value != 1 else ""),
             "value": format(value.normalize(), ",f")} for value in values if value > 0]


def _capacity_focus(anchor, text):
    request = _CAPACITY_REQUEST.fullmatch(_normal(anchor))
    if request is None:
        return []
    units = {request["first"].rstrip("s"), request["second"].rstrip("s")}
    if len(units) != 2:
        return []
    measures = {request["measure"]}
    if request["measure"] == "total generating capacity":
        measures.add("total electricity generating capacity")
    return [{"kind": "capacity_threshold", "measure": _normal(match["measure"]),
             "quantity_pair": " ".join(match["quantity_pair"].split())}
            for match in _CAPACITY_THRESHOLD.finditer(text)
            if _normal(match["measure"]) in measures
            and {match["first"].lower().rstrip("s"), match["second"].lower().rstrip("s")} == units]


def _conversion_pairs(match):
    return {_conversion_unit(match[role]): _conversion_value(match[f"{role}_value"])
            for role in ("first", "second")}


def _conversion_value(text):
    value = text.casefold().split()
    number = "1" if value[0] == "one" else value[0]
    return _number(number) * _SCALES[value[1] if len(value) == 2 else ""]


def conversion_prose(texts, focus):
    """Validate each required model-written sentence, then join the submitted prose."""
    sentences = []
    for field, (unit, value) in zip(REQUIRED_TARGET_FIELDS, focus["targets"].items(), strict=True):
        sentence = texts[field].strip()
        match = _CONVERSION_CLAIM.fullmatch(_normal(sentence))
        if (match is None or _conversion_unit(match["base"]) != focus["base_unit"]
                or _conversion_unit(match["target"]) != unit or _conversion_value(match["value"]) != _number(value)):
            raise ValueError("Conversion target sentence must retain its source base, value and unit")
        sentences.append(sentence)
    return " ".join(sentences)


def _membership_focus(anchor, text):
    request = _MEMBERSHIP_REQUEST.fullmatch(_normal(anchor))
    if request is None:
        return []
    category = request["category"]
    pattern = re.compile(rf"(?:the )?{re.escape(category)}(?: category)? includes? "
                         rf"(?P<first>{_MEMBERSHIP_GROUP}?) and (?P<second>other {_MEMBERSHIP_GROUP})\.", re.I)
    result = []
    for line in text.splitlines():
        match = pattern.fullmatch(" ".join(line.split()))
        if match and " and " not in _normal(match["first"]) and " and other " not in _normal(match["second"]):
            result.append({"kind": "category_membership", "category": category,
                           "members": [match["first"], match["second"]]})
    return result


def render_membership(texts, focus):
    """Verify both raw member phrases before rendering the recognized source relation."""
    first, second = focus["members"]
    if [_normal(texts[field]) for field in REQUIRED_TARGET_FIELDS] != [_normal(first), _normal(second)]:
        raise ValueError("Membership selection must retain both complete source members in order")
    return f"The {focus['category']} category includes {first} and {second}."


def request_focus(requests, catalog, report, bindings, *, include_conversions=False, include_membership=False,
                  include_source_fields=False):
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
        matchers = [_table_focus, _ratio_focus]
        if include_conversions:
            matchers.extend((_conversion_focus, _capacity_focus, _single_power_focus))
        if include_membership:
            matchers.append(_membership_focus)
        if include_source_fields:
            matchers.append(source_field_focus)
        matches = [{**focus, "span_id": sid} for sid, span in catalog.items() if span["source_id"] in allowed
                   for matcher in matchers for focus in matcher(anchor, span["text"])]
        if len(matches) == 1:
            result[cid] = matches[0]
    return result


def relevance_hints(requests, catalog, report, bindings, focuses):
    """Suggest query-relevant exact spans within each request's retrieved support."""
    support = {branch.subtask_id: {source.source_id for source in branch.sources if source.role == "support"}
               for branch in report.results if branch.outcome == "evidence"}
    hints = {}
    for index, request in enumerate(requests):
        cid = request["component_id"]
        if cid in focuses:
            continue
        anchor = request["question_anchor"]
        if index and _DEPENDENT_QUESTION.search(anchor):
            anchor = f'{requests[index - 1]["question_anchor"]} {anchor}'
        terms = list(dict.fromkeys(t for t in _tokens(anchor) if t not in _QUERY_FILLER))
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
    if focus["kind"] == "single_power_conversion":
        return f"One {focus['base']} is equivalent to {focus['value']} {focus['target']}."
    if focus["kind"] == "table_publication":
        return f"The table cites {focus['publication']} as its data source."
    if focus["kind"] == "capacity_threshold":
        return f"The minimum {focus['measure']} is {focus['quantity_pair']}."
    if focus["kind"] == "ratio_operand":
        return f"The {focus['role']} is {focus['operand']}."
    return (f"In {focus['year']}, the table gives {focus['label']} generation in {focus['unit']} as "
            f"{focus['amount']} and its share of {focus['denominator']} as {focus['share']}.")


def power_claim_texts(focus, source=None):
    """Allow a bounded attribution only to the already selected source record."""
    canonical = focused_text(focus)
    title = (source or {}).get("title") or ""
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 -]{1,79}", title):
        return (canonical,)
    labels = [title]
    if (source.get("url") == "https://www.eia.gov/energyexplained/electricity/measuring-electricity.php"
            and _normal(title) == "measuring electricity"):
        labels.append("EIA measurement guide")
    return (canonical, *(f"{canonical[:-1]} in the {label}." for label in labels))


def validate_focused_claims(claims, focuses, *, sources_by_component=None):
    """Keep the raw claim bound to the recognized operand or table row."""
    for cid, focus in focuses.items():
        matching = [claim["text"] for claim in claims if claim["component_id"] == cid]
        if len(matching) != 1:
            raise ValueError("Focused request requires one raw claim")
        variants = (power_claim_texts(focus, (sources_by_component or {}).get(cid))
                    if focus["kind"] == "single_power_conversion" else (focused_text(focus),))
        allowed = {_normal(text) for text in variants}
        if focus["kind"] == "ratio_operand":
            name = re.sub(r"^the\s+", "", focus["ratio"], flags=re.I)
            allowed.add(_normal(f"The {focus['role']} of the {name} is {focus['operand']}."))
        if _normal(matching[0]) not in allowed:
            if focus["kind"] == "single_power_conversion":
                raise ValueError("Raw conversion must preserve the source base, digit value and requested unit")
            if focus["kind"] == "table_publication":
                raise ValueError("Raw claim must name the verified table publication")
            if focus["kind"] == "capacity_threshold":
                raise ValueError("Raw capacity claim must retain the minimum and both requested units")
            raise ValueError("Raw claim does not retain the requested table row or ratio operand")
