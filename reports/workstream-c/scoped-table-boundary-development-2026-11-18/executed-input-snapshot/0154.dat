"""Recognize explicit two-action and condition/result source statements."""
import re


_CAPABILITY_REQUEST = re.compile(r"what two capabilities does [\w .-]+ describe for (?P<subject>[\w -]+)\??", re.I)
_CAPABILITY = re.compile(r"(?P<subject>Some [\w -]+) can (?P<first>[^.;]+?) and (?P<second>[^.;]+)\.", re.I)
_EXAMPLE_REQUEST = re.compile(r"\bhow much\b.*?\b(?P<object>[a-z]+(?:-[a-z]+)*) example\b", re.I)
_EXAMPLE = re.compile(r"For example, if (?P<conditions>[^,;]+), "
                      r"(?P<result>you have used \d(?:[^.;]|\.(?=\d))*)\.", re.I)
SOURCE_FIELD_KINDS = frozenset({"counted_capabilities", "worked_example"})


def _normal(value):
    return " ".join(value.casefold().split())


def source_field_focus(anchor, text):
    """Return a focus only when a full source sentence explicitly matches the request."""
    text = " ".join(text.split())
    request = _CAPABILITY_REQUEST.fullmatch(anchor.strip())
    if request:
        match = _CAPABILITY.fullmatch(text)
        if (match and _normal(match["subject"]) == "some " + _normal(request["subject"])
                and " and " not in _normal(match["second"])
                and not any(re.match(r"(?:not|never)\b", match[part], re.I) for part in ("first", "second"))):
            return [{"kind": "counted_capabilities", "subject": match["subject"],
                     "fields": [match["first"], match["second"]]}]
        return []
    request = _EXAMPLE_REQUEST.search(anchor)
    match = _EXAMPLE.fullmatch(text) if request else None
    if match:
        label = _normal(request["object"]).replace("-", " ")
        conditions = _normal(match["conditions"]).replace("-", " ")
        if re.search(rf"\b{re.escape(label)}\b", conditions):
            return [{"kind": "worked_example", "fields": [match["conditions"], match["result"]]}]
    return []


def render_source_fields(texts, focus):
    """Check each model-selected phrase before preserving the source relation."""
    first, second = focus["fields"]
    if [_normal(texts[field]) for field in ("target_1", "target_2")] != [_normal(first), _normal(second)]:
        raise ValueError("Required coverage must retain both complete source fields in order")
    if focus["kind"] == "counted_capabilities":
        return f"{focus['subject']} can {first} and {second}."
    return f"For example, if {first}, {second}."
