"""Opt-in structural request coverage, not semantic evidence adjudication."""


def validate_requirements(requirements, bindings):
    if requirements is None:
        return {}
    if not isinstance(requirements, dict) or not set(requirements) <= set(bindings):
        raise ValueError("Unknown coverage component")
    for cid, ids in requirements.items():
        if (not isinstance(ids, (list, tuple)) or not ids or len(set(ids)) != len(ids)
                or not set(ids) <= set(bindings[cid])):
            raise ValueError("Invalid requested coverage branch")
    return requirements


def branch_payload(report):
    return [{"subtask_id": r.subtask_id, "outcome": r.outcome,
             "support_source_ids": [s.source_id for s in r.sources if s.role == "support"]}
            for r in report.results]


def coverage_checks(mapping, report, requirements):
    results = {r.subtask_id:r for r in report.results}
    components = {c.component_id:c for c in mapping.components}
    checks = {}
    for cid, branches in requirements.items():
        component = components[cid]
        selected = {e.source_id for e in component.evidence}
        unselected = []
        for bid in branches:
            result = results.get(bid)
            support = {s.source_id for s in result.sources if s.role == "support"} if result else set()
            if not result or result.outcome != "evidence" or not (support & selected):
                unselected.append(bid)
        checks[cid] = {"status":component.status, "required_branches":list(branches),
                       "unselected_branches":unselected, "semantic_support_proven":False}
        if component.status == "supported" and unselected:
            raise ValueError("Supported request leaves required branch coverage unselected: " + ", ".join(unselected))
    return checks
