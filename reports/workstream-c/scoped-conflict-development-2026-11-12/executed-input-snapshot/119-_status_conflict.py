"""Check literal disagreement for explicit provisional-or-final requests."""
from itertools import combinations
import re


_STATUS_QUESTION = re.compile(r"\b(?:preliminary|provisional)\s+or\s+final\b|"
                              r"\bfinal\s+or\s+(?:preliminary|provisional)\b", re.I)
_STATEMENT = re.compile(
    r"(?P<subject>[^.;!?\n]+?)\s+(?:is|are|was|were|remains?|remained)\s+"
    r"(?:still\s+)?(?P<negative>not\s+)?(?P<status>provisional|preliminary|final)\.?",
    re.I,
)
_NON_ASSERTION = re.compile(r"\b(?:if|whether|may|might|could|would|unless|or)\b|[\"“”]", re.I)


def _status_assertion(quote):
    match = _STATEMENT.fullmatch(quote.strip())
    if match is None or _NON_ASSERTION.search(quote):
        return None
    subject = " ".join(match["subject"].casefold().split())
    return subject, match["status"].casefold(), match["negative"] is None


def validate_publication_status_conflict(mapping):
    """Require opposed status assertions about the same literal subject.

    Unknown or ambiguous comparisons need further evidence. The check cannot
    establish that an asserted subject answers the request.
    """
    for component in mapping.components:
        if component.status != "conflicting" or not _STATUS_QUESTION.search(component.question_anchor):
            continue
        statements = [status for item in component.evidence if (status := _status_assertion(item.quote))]
        for (left, left_status, left_positive), (right, right_status, right_positive) in combinations(statements, 2):
            if left != right:
                continue
            if left_status == right_status and left_positive != right_positive:
                break
            if (left_status == "final") != (right_status == "final") and left_positive and right_positive:
                break
        else:
            raise ValueError("Publication-status conflict requires opposed assertions about the same subject")
