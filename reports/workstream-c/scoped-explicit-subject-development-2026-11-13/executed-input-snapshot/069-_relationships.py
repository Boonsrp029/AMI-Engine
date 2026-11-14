"""Conservative literal relationship checks for the opt-in C boundary.

These literal checks preserve explicit locatives and percentage denominators.
The supported scope relocation requires the same words in the sentence body.
"""
import re


_DENOMINATOR = re.compile(r"(\d+(?:\.\d+)?\s*%)\s+of\s+([^.;,]+)", re.I)
_YEAR = r"[12][0-9]{3}"
_SCOPE = rf"(?:{_YEAR}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
_FRAMED_SENTENCE = re.compile(
    rf"(?i:in)\s+(?P<front>{_SCOPE}),\s+(?P<body>.+?)\s+(?i:in)\s+(?P<back>{_SCOPE})\.?"
)
_AMBIGUOUS_BODY = re.compile(r"[,;!?]|(?<!\d)\.|\.(?!\d)|\b(?:and|or|but)\b", re.I)


def _normal(text):
    return " ".join(text.casefold().split())


def _same_scopes_relocated(text, quote):
    claim = _FRAMED_SENTENCE.fullmatch(text.strip())
    source = _FRAMED_SENTENCE.fullmatch(quote.strip())
    if claim is None or source is None:
        return False
    front, body, back = source.group("front", "body", "back")
    return (
        bool(re.fullmatch(_YEAR, front)) != bool(re.fullmatch(_YEAR, back))
        and claim["front"] == back
        and claim["back"] == front
        and not _AMBIGUOUS_BODY.search(body)
        and _normal(claim["body"]) == _normal(body)
    )


def validate_relationships(text, evidence):
    """Reject explicit scope/denominator changes within selected source units.

    Locations are only identified by capitalized source locatives (In Canada,
    across New Zealand). This does not establish implicit geographic scope.
    A single matching sentence can reverse its fronted and trailing scope phrases.
    """
    quotes = " ".join(e.quote for e in evidence)
    # Match the preposition case-insensitively without making the name pattern
    # case-insensitive: ordinary 'in the report' is not a geographic assertion.
    locations = {m.group(1) for m in re.finditer(
        r"\b(?i:in|across|within)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", quotes)}
    asserted = {m.group(1) for m in re.finditer(
        r"\b(?i:in|across|within)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text)}
    if locations and (asserted - locations or any(
            not re.search(r"\b" + re.escape(location) + r"\b", text, re.I)
            for location in locations)):
        raise ValueError("Composed geographic scope differs from selected evidence")
    expected_matches = _DENOMINATOR.findall(quotes)
    actual_matches = _DENOMINATOR.findall(text)
    expected = {(_normal(value), _normal(denominator)) for value, denominator in expected_matches}
    actual = {(_normal(value), _normal(denominator)) for value, denominator in actual_matches}
    if expected and actual != expected:
        if len(evidence) == len(expected_matches) == len(actual_matches) == 1:
            if _same_scopes_relocated(text, quotes):
                return
        raise ValueError("Composed percentage denominator differs from selected evidence")
    if actual and not actual.issubset(expected):
        raise ValueError("Composed percentage denominator absent from selected evidence")
