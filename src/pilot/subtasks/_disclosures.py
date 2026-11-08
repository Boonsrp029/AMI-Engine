"""Opt-in scoped branch disclosures. Execution facts are not semantic proof."""
import hashlib
import json
from typing import Literal

from pydantic import Field

from ..schemas import StrictModel
from .._requests import requested_components
from .contracts import Plan, Result, Identity, digest
from .scheduler import Report, aggregate
from ._question_spans import QuestionSpan


VERSION = "cq-scoped-disclosures-v1"


def bindings_hash(bindings):
    # Branch order is meaningful and must not be normalized away.
    encoded = json.dumps(bindings, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class RequestedScope(StrictModel):
    component_id: str = Field(pattern=r"^r[1-5]$")
    subtask_id: str = Field(pattern=r"^s0[1-5]$")
    question_span: QuestionSpan | None  # Explicit null means unresolved scope.


class DisclosureScopes(StrictModel):
    version: Literal[VERSION] = VERSION
    plan_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    corpus_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    question_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bindings_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    declaration_ref: str = Field(min_length=1, max_length=300)
    annotations: tuple[RequestedScope, ...] = Field(min_length=1, max_length=25)


def validate_scopes(plan, bindings, scopes):
    plan = Plan.model_validate_json(plan.model_dump_json())
    scopes = DisclosureScopes.model_validate_json(scopes.model_dump_json())
    if (scopes.plan_id != plan.plan_id or scopes.corpus_sha256 != plan.corpus_sha256
            or scopes.question_sha256 != hashlib.sha256(plan.query.encode("utf-8")).hexdigest()
            or scopes.bindings_sha256 != bindings_hash(bindings) or not scopes.declaration_ref.strip()):
        raise ValueError("Requested-scope identity differs from plan/question/corpus/bindings")
    components = {r["component_id"] for r in requested_components(plan.query)}
    branches = {s.subtask_id for s in plan.subtasks}
    if (set(bindings) != components or any(not ids or len(ids) != len(set(ids))
            or not set(ids) <= branches for ids in bindings.values())
            or set().union(*(set(ids) for ids in bindings.values())) != branches):
        raise ValueError("Requested scopes require exact component/branch bindings")
    expected = {(cid, bid) for cid, ids in bindings.items() for bid in ids}
    supplied = [(a.component_id, a.subtask_id) for a in scopes.annotations]
    if len(supplied) != len(set(supplied)) or set(supplied) != expected:
        raise ValueError("Every bound component/branch needs exactly one scope declaration")
    for annotation in scopes.annotations:
        span = annotation.question_span
        if span is not None and (not 0 <= span.start < span.end <= len(plan.query)
                                 or not plan.query[span.start:span.end].strip()):
            raise ValueError("Requested scope must be a nonblank original-question span")
    return scopes


def validate_report(plan, report):
    """Validate real A envelopes, including failures for diagnostic-only projection."""
    if not isinstance(report, Report):
        raise ValueError("Scoped disclosures require A's typed Report")
    identity = Identity.model_validate_json(report.identity.model_dump_json())
    if identity.plan_id != plan.plan_id or identity.corpus_sha256 != plan.corpus_sha256:
        raise ValueError("Disclosure report identity differs from plan")
    states = dict(report.states)
    declared = {s.subtask_id for s in plan.subtasks}
    if (len(report.states) != len(declared) or set(states) != declared
            or any(state not in {"completed", "failed", "cancelled", "blocked"} for state in states.values())
            or report.status not in {"completed", "partial", "failed", "cancelled", "deadline"}):
        raise ValueError("Disclosure report is not terminal and complete")
    results = {}
    for raw in report.results:
        result = Result.model_validate_json(raw.model_dump_json())
        if (result.identity != identity or result.subtask_id not in declared
                or result.subtask_id in results or states[result.subtask_id] != "completed"):
            raise ValueError("Disclosure result identity/state is invalid")
        results[result.subtask_id] = result
    order = [s.subtask_id for s in plan.subtasks if states[s.subtask_id] == "completed"]
    if list(results) != order or len({r.child_attempt_id for r in results.values()}) != len(results):
        raise ValueError("Disclosure results are missing, unordered or share an attempt")
    for task in plan.subtasks:
        if task.subtask_id not in results:
            continue
        dependencies = results[task.subtask_id].dependencies
        if [ref.subtask_id for ref in dependencies] != list(task.dependencies):
            raise ValueError("Disclosure dependency identities differ from plan")
        for ref in dependencies:
            parent = results.get(ref.subtask_id)
            if (parent is None or ref.child_attempt_id != parent.child_attempt_id
                    or ref.result_sha256 != digest(parent.model_dump_json())):
                raise ValueError("Disclosure dependency result lineage differs")
    if (report.sources != aggregate(report.results)
            or report.missing_branches != tuple(s.subtask_id for s in plan.subtasks if states[s.subtask_id] != "completed")):
        raise ValueError("Disclosure aggregate disagrees with branch results")
    required_done = all(not s.required or states[s.subtask_id] == "completed" for s in plan.subtasks)
    if report.can_compose and (not required_done or report.status in {"failed", "cancelled", "deadline"}):
        raise ValueError("Disclosure report falsely permits drafting")
    return states, results


def project_disclosures(plan, report, mapping, bindings, scopes):
    """Return traceable warnings; never approve a claim or infer database absence."""
    scopes = validate_scopes(plan, bindings, scopes)
    states, results = validate_report(plan, report)
    annotations = {(a.component_id, a.subtask_id): a for a in scopes.annotations}
    components = {c.component_id: c for c in mapping.components}
    if set(components) != set(bindings):
        raise ValueError("Disclosure mapping components differ from bindings")
    records, warnings, unresolved_records = [], [], []
    for request in requested_components(plan.query):
        cid = request['component_id']
        bids = bindings[cid]
        component = components[cid]
        allowed = {s.source_id for bid in bids if bid in results for s in results[bid].sources if s.role == "support"}
        if any(e.source_id not in allowed for e in component.evidence):
            raise ValueError("Disclosure evidence crosses a bound support boundary")
        component_unresolved = False
        for bid in bids:
            task = next(s for s in plan.subtasks if s.subtask_id == bid)
            result = results.get(bid)
            returned = [s.source_id for s in result.sources if s.role == "support"] if result else []
            selected = [sid for sid in returned if sid in {e.source_id for e in component.evidence}]
            if states[bid] != "completed":
                kind, text = "unverified_execution", f"Subtask did not complete ({states[bid]}); coverage remains unverified."
            elif result.outcome == "conflicting":
                kind, text = "reported_conflict", "The branch reported conflicting evidence; inspect the separate source statements."
            elif result.outcome == "missing":
                kind, text = "empty_retrieval", "This retrieval returned no supporting evidence; this does not establish absence in the database."
            elif not selected:
                kind, text = "unselected_evidence", "Sources were returned but not selected; requested coverage remains unresolved."
            else:
                kind, text = "selected_evidence", "Evidence selected; semantic support and within-branch completeness remain unproven."
            span = annotations[cid, bid].question_span
            label = plan.query[span.start:span.end] if span else None
            unresolved = kind != "selected_evidence" or label is None
            item = {"component_id": cid, "component_status": component.status,
                "subtask_id": bid, "required": task.required,
                "state": states[bid], "outcome": result.outcome if result else None, "kind": kind,
                "requested_scope": label, "question_span": span.model_dump() if span else None,
                "original_question": plan.query, "retrieval_query": task.query,
                "returned_support_ids": returned, "selected_support_ids": selected,
                "child_attempt_id": result.child_attempt_id if result else None,
                "disclosure": text, "semantic_support_proven": False,
                "scope_semantics_proven": False}
            records.append(item)
            if task.required and unresolved:
                component_unresolved = True
                unresolved_records.append(item)
        conflict_disclosed = any(item['component_id'] == cid and item['required']
            and item['kind'] == 'reported_conflict' for item in unresolved_records)
        if component.status == 'conflicting' and not conflict_disclosed:
            warnings.append(f"Component {cid} reports conflicting selected evidence; inspect the separate source statements. "
                f"Original request: {plan.query}")
        elif component.status != "supported" and not component_unresolved:
            warnings.append(f"Component {cid} remains {component.status}; branch selection does not locate every unresolved fact. "
                f"Original request: {plan.query}")
    branch_warnings = []
    for task in plan.subtasks:
        items = [record for record in unresolved_records if record['subtask_id'] == task.subtask_id]
        if not items:
            continue
        details = ' | '.join(f"component {item['component_id']}: {item['disclosure']} Requested scope: "
            + (item['requested_scope'] or 'requested scope not established') for item in items)
        branch_warnings.append(f"Subtask {task.subtask_id}: {details}. "
            f"Retrieval query (data): {task.query or '[source inspection]'}. Original request: {plan.query}")
    return {"version": VERSION, "identity": report.identity.model_dump(),
        "scope_contract": scopes.model_dump(mode="json"), "records": records,
        "warnings": branch_warnings + warnings, "drafting_allowed": report.can_compose,
        "semantic_support_proven": False, "owner_acceptance": "not inferred"}
