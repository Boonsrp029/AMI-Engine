"""Lexical coverage of two explicitly requested, source-listed members.

This check establishes phrase coverage only. Source interpretation and the
truth of a generated membership assertion still require safety/source review.
"""
import re


_PHRASE = r"[a-z][a-z -]*"
_REQUEST = re.compile(
    rf"does (?:the )?(?P<category>{_PHRASE}?) category include "
    rf"(?P<first>{_PHRASE}?) and (?P<second>{_PHRASE})\?", re.I)
_SOURCE = re.compile(
    r"(?:\d+\s+)?(?P<category>[a-z][a-z() -]*?) includes? "
    r"(?P<members>[a-z][a-z ,\-]*)\.", re.I)


def _normal(text):
    return " ".join(text.casefold().split())


def requested_membership(anchor, evidence):
    """Recognize one affirmative selected list that contains both requested items.

    Ambiguous, qualified, incomplete or differently scoped lists are left to
    the existing general path. Never search unselected records for support.
    """
    request = _REQUEST.fullmatch(_normal(anchor))
    if request is None:
        return None
    members = [request["first"], request["second"]]
    if members[0] == members[1] or any(" and " in member for member in members):
        return None
    matches = []
    for item in evidence:
        source = _SOURCE.fullmatch(_normal(item["quote"]))
        if source is None:
            continue
        category = _normal(re.sub(r"[()]", "", source["category"]))
        requested_category = request["category"]
        if requested_category != category and not requested_category.endswith(" " + category):
            continue
        listed = re.split(r",\s*(?:and\s+)?|\s+and\s+", source["members"])
        if (len(listed) < 2 or any(re.search(r"\b(?:not|except|excluding)\b", value) for value in listed)
                or not set(members).issubset(listed)):
            continue
        matches.append({"category": category, "members": members,
                        "source_id": item["source_id"], "quote": item["quote"]})
    return matches[0] if len(matches) == 1 else None


def validate_membership_coverage(claims, requirements):
    """Reject an omitted requested name before fallback or safety can hide it."""
    for unit_id, requirement in requirements.items():
        matching = [claim for claim in claims if claim["unit_id"] == unit_id
                    and claim["component_id"] == requirement["component_id"]]
        if len(matching) != 1 or any(
            re.search(r"(?<!\w)" + re.escape(member) + r"(?!\w)", _normal(matching[0]["text"])) is None
            for member in requirement["members"]
        ):
            raise ValueError("Raw membership claim omits a requested source-listed member")
