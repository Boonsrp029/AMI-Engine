"""Check literal disagreement for explicit provisional-or-final requests."""
import copy
from itertools import combinations
import re

from .._scope import same_pinned_document


_STATUS_QUESTION = re.compile(r"\b(?:preliminary|provisional)\s+or\s+final\b|"
                              r"\bfinal\s+or\s+(?:preliminary|provisional)\b", re.I)
_STATEMENT = re.compile(
    r"(?P<subject>[^.;!?\n]+?)\s+(?:is|are|was|were|remains?|remained)\s+"
    r"(?:still\s+)?(?P<negative>not\s+)?(?P<status>provisional|preliminary|final)\.?",
    re.I,
)
_NON_ASSERTION = re.compile(r"\b(?:if|whether|may|might|could|would|unless|or)\b|[\"“”]", re.I)
_YEAR = re.compile(r"\b[12][0-9]{3}\b")


def _status_assertion(quote):
    match = _STATEMENT.fullmatch(quote.strip())
    if match is None or _NON_ASSERTION.search(quote):
        return None
    subject = " ".join(match["subject"].casefold().split())
    return subject, match["status"].casefold(), match["negative"] is None


def _opposed(left, right):
    left_subject, left_status, left_positive = left
    right_subject, right_status, right_positive = right
    if left_subject != right_subject:
        return False
    if left_status == right_status:
        return left_positive != right_positive
    return (left_status == "final") != (right_status == "final") and left_positive and right_positive


def validate_publication_status_conflict(mapping):
    """Require opposed status assertions about the same literal subject.

    Unknown or ambiguous comparisons need further evidence. The check cannot
    establish that an asserted subject answers the request.
    """
    for component in mapping.components:
        if component.status != "conflicting" or not _STATUS_QUESTION.search(component.question_anchor):
            continue
        statements = [status for item in component.evidence if (status := _status_assertion(item.quote))]
        if not any(_opposed(left, right) for left, right in combinations(statements, 2)):
            raise ValueError("Publication-status conflict requires opposed assertions about the same subject")


def include_opposing_status(candidate, mapping, catalog, report, bindings, sources, question):
    """Preserve a literal opposing source before composing a status claim."""
    resolved = {component.component_id: component for component in mapping.components}
    branches = {result.subtask_id: result for result in report.results}
    updated = copy.deepcopy(candidate)
    changes = []
    for component in updated["components"]:
        cid = component["component_id"]
        anchor = resolved[cid].question_anchor
        if component["status"] not in {"supported", "partial"} or not _STATUS_QUESTION.search(anchor):
            continue
        allowed = {source.source_id for bid in bindings[cid] if bid in branches
                   and branches[bid].outcome in {"evidence", "conflicting"}
                   for source in branches[bid].sources if source.role == "support"}
        years = set(_YEAR.findall(anchor)) or set(_YEAR.findall(question))
        admitted = {sid: value for sid, span in catalog.items() if span["source_id"] in allowed
                    and (value := _status_assertion(span["text"]))
                    and len(years) == 1 and set(_YEAR.findall(value[0])) == years}
        pair = next(((sid, other) for sid in component["evidence"] if sid in admitted
                     for other, value in admitted.items()
                     if catalog[sid]["source_id"] != catalog[other]["source_id"] and _opposed(admitted[sid], value)),
                    None)
        if pair is None:
            continue
        changes.append({"component_id": cid, "original_status": component["status"],
                        "original_evidence": component["evidence"], "opposed_span_ids": list(pair),
                        "basis": "opposed publication status for the same literal subject and requested year"})
        component.update(status="conflicting", evidence=list(pair), gap_anchor="")
    if not changes:
        return candidate, changes

    # Geography in a remaining supported claim must retain its original source linkage.
    support = {catalog[sid]["source_id"] for component in updated["components"]
               if component["status"] in {"supported", "partial"} for sid in component["evidence"]}
    geography = updated["geography"]
    if support and geography["status"] == "known" and any(
            source_id not in support and not any(same_pinned_document(sources[source_id], sources[sid]) for sid in support)
            for source_id in (catalog[sid]["source_id"] for sid in geography["evidence"])):
        updated["geography"] = {"status": "unresolved", "value": "", "evidence": [],
                                "reason": "Selected geography is no longer linked to a supported component."}
    return updated, changes
