"""Offline concurrent composer capture/validation. No model or safety client."""
import hashlib
import json
import time
from pathlib import Path


class CapturedComposer(Exception):
    pass


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capture_composer(contract_path, case_id, mapping_path, *, expected, response=None):
    """Replay one pinned mapper; capture or validate composition before safety.

    `response` is a fixed JSON value supplied by the caller, never a callback.
    The two logical ModelAccess slots are explicitly replay/validation slots,
    not inference. Future service execution is a separate authorized operation.
    """
    if (set(expected) != {"contract", "mapping", "corpus"}
            or sha(contract_path) != expected["contract"]
            or sha(mapping_path) != expected["mapping"]):
        raise ValueError("Frozen composer replay identity changed")
    contract = json.loads(Path(contract_path).read_text(encoding="utf-8"))
    case = contract["cases"][case_id]
    if sha(case["corpus_path"]) != expected["corpus"]:
        raise ValueError("Frozen composer corpus changed")
    retained = json.loads(Path(mapping_path).read_text(encoding="utf-8"))
    if retained["stage"] != "mapping":
        raise ValueError("Expected a retained mapper response")
    # Heavy imports remain offline and happen after immutable-input checks.
    from src.pilot.subtasks.contracts import Plan
    from src.pilot.subtasks.generation import ConcurrentComposer
    from src.pilot.subtasks.retrieval import LocalBM25Adapter
    from src.pilot.subtasks.runner import ModelAccess
    from src.pilot.subtasks.scheduler import run_plan

    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    report = run_plan(plan, "a"*32, "b"*32, LocalBM25Adapter(case["corpus_path"]))
    captured = {}
    counts = {"frozen_mapper_replays":0, "fixed_composer_validations":0}

    def transport(stage, schema, instruction, inputs):
        if stage == "mapping":
            counts["frozen_mapper_replays"] += 1
            if counts["frozen_mapper_replays"] != 1:
                raise AssertionError("Unexpected repeated mapper replay")
            return {**retained, "parsed":json.loads(retained["raw"])}
        if stage != "composition" or captured:
            raise AssertionError("Unexpected repeated composition")
        captured.update(schema=schema.model_json_schema(), messages=[
            {"type":"system", "content":instruction},
            {"type":"human", "content":json.dumps(inputs, ensure_ascii=False, separators=(",", ":"))}])
        if response is None:
            raise CapturedComposer()
        counts["fixed_composer_validations"] += 1
        return {"parsed":response, "raw":json.dumps(response), "usage":None}

    access = ModelAccess(time.monotonic()+30)
    outcome = {"actual_model_calls":0, "nemo_invocations":0, "captured":captured,
               "input_identity":expected}
    try:
        result = ConcurrentComposer(plan, case["bindings"], contract["as_of"], transport,
            complete_required_branches=case.get("complete_required_branches"))(report, access)
    except CapturedComposer:
        outcome["status"] = "captured without inference"
    except ValueError as exc:
        if not captured:
            raise  # Invalid mapping is not a composer-only diagnostic.
        outcome.update(status="composition validation failed", error_type=type(exc).__name__, error=str(exc))
    else:
        outcome.update(status="composition validated; safety not executed; source assessment pending",
                       draft=result.draft, provenance=result.provenance, diagnostics=result.diagnostics,
                       safety_passed=result.safety_passed)
        if result.safety_passed:
            raise AssertionError("Offline capture cannot establish final safety")
    outcome.update(counts, logical_access_slots=access.calls)
    assert counts["frozen_mapper_replays"] == 1 and access.guards == 0
    return outcome
