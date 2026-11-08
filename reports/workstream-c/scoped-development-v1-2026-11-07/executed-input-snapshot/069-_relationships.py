"""Conservative literal relationship checks for the opt-in C boundary.

These checks are necessary conditions, not semantic entailment. Explicit
locatives and percentage denominators must survive paraphrasing literally;
unsupported aliases/conversions fail rather than being repaired.
"""
import re


_DENOMINATOR = re.compile(r"(\d+(?:\.\d+)?\s*%)\s+of\s+([^.;,]+)", re.I)


def _normal(text):
    return " ".join(text.casefold().split())


def validate_relationships(text, evidence):
    """Reject explicit scope/denominator changes within selected source units.

    Locations are only identified by capitalized source locatives (In Canada,
    across New Zealand). This does not establish implicit geographic scope.
    Denominators use the source's exact bounded phrase, without conversions.
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
    expected = {(_normal(m[1]), _normal(m[2])) for m in _DENOMINATOR.finditer(quotes)}
    actual = {(_normal(m[1]), _normal(m[2])) for m in _DENOMINATOR.finditer(text)}
    if expected and actual != expected:
        raise ValueError("Composed percentage denominator differs from selected evidence")
    if actual and not actual.issubset(expected):
        raise ValueError("Composed percentage denominator absent from selected evidence")
