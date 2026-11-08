"""Verify exact development contract/start/result provenance before CQ1."""
import hashlib
import json
import re
from pathlib import Path

from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",", ":"),allow_nan=False)


def canonical_hash(contract):
    body = {k:v for k,v in contract.items() if k != "contract_sha256"}
    return hashlib.sha256(canonical(body).encode()).hexdigest()


def checked(case, path_key, hash_key):
    if not isinstance(case.get(path_key), str) or not isinstance(case.get(hash_key), str):
        raise ValueError("Missing retained development lineage: " + path_key)
    path = Path(case[path_key])
    if digest(path) != case[hash_key]:
        raise ValueError("Retained development lineage identity changed: " + path_key)
    return json.loads(path.read_text(encoding="utf-8"))


def verify_lineage(contract):
    gate = contract["development_gate"]
    runs, attempts, development_contracts = set(), set(), set()
    if not contract.get("model_snapshot") or not contract.get("settings"):
        raise ValueError("Current pipeline needs explicit model/settings")
    for case in gate["cases"]:
        dev = checked(case,"development_contract_path","development_contract_file_sha256")
        start = checked(case,"started_path","started_sha256")
        result = checked(case,"result_path","result_sha256")
        assessment = checked(case,"assessment_path","assessment_sha256")
        reference = canonical_hash(dev)
        if dev.get("contract_sha256") != reference:
            raise ValueError("Development contract canonical identity changed")
        development_contracts.add(reference)
        if (dev.get("phase") != "development"
                or dev.get("case_ids") != contract["development_case_ids"]
                or len(set(dev["case_ids"])) != 2
                or case["case_id"] not in dev.get("cases", {})):
            raise ValueError("Retained development roster differs")
        if (dev.get("pipeline_identity") != contract["pipeline_identity"]
                or canonical(dev.get("model_snapshot")) != canonical(contract["model_snapshot"])
                or canonical(dev.get("settings")) != canonical(contract["settings"])
                or canonical(dev.get("limits")) != canonical(contract["limits"])):
            raise ValueError("Retained development pipeline/model/settings differ")
        if start != {"case_id":case["case_id"], "contract_sha256":reference}:
            raise ValueError("Development start does not bind this case and contract")
        findings = assessment.get("source_findings")
        if (assessment.get("verdict") != "pass" or assessment.get("result_sha256") != case["result_sha256"]
                or not isinstance(findings,list) or not findings
                or any(not isinstance(f,str) or not f.strip() for f in findings)):
            raise ValueError("Development needs exact-result source findings")
        if (result.get("technical_pass") is not True or result.get("failure_type") is not None
                or type(result.get("main_calls")) is not int or not 0 <= result["main_calls"] <= 4
                or type(result.get("nemo_invocations")) is not int or not 0 <= result["nemo_invocations"] <= 1
                or type(result.get("elapsed_seconds")) not in (int,float)
                or not 0 <= result["elapsed_seconds"] <= 180):
            raise ValueError("Development execution did not satisfy its bounds")
        stored = result.get("stored_run")
        if not isinstance(stored,dict) or stored.get("status") != "needs_review" or stored.get("draft") is None:
            raise ValueError("Development result has no reviewable stored revision")
        run_id = stored.get("id")
        metrics = stored.get("metrics",{})
        attempt_id = metrics.get("attempt_id")
        if (not isinstance(run_id,str) or not re.fullmatch(r"[0-9a-f]{32}",run_id)
                or not isinstance(attempt_id,str) or not re.fullmatch(r"[0-9a-f]{32}",attempt_id)
                or run_id in runs or attempt_id in attempts):
            raise ValueError("Development run/attempt identity is invalid or reused")
        runs.add(run_id); attempts.add(attempt_id)
        expected = Plan.model_validate_json(json.dumps(dev["cases"][case["case_id"]]["plan"]))
        if stored.get("query") != expected.query or stored.get("corpus_sha") != expected.corpus_sha256:
            raise ValueError("Development result query/corpus differs from started case")
        if metrics.get("model_calls") != result["main_calls"] or metrics.get("guardrail_invocations") != result["nemo_invocations"]:
            raise ValueError("Development result counters differ from stored attempt")
        events = stored.get("events",[])
        starts = [e for e in events if e.get("kind")=="attempt_started" and e.get("payload",{}).get("attempt_id")==attempt_id]
        plans = [e for e in events if e.get("kind")=="subtask_plan"
                 and e.get("payload",{}).get("identity",{}).get("attempt_id")==attempt_id]
        if len(starts)!=1 or len(plans)!=1:
            raise ValueError("Development attempt/plan event lineage is missing or ambiguous")
        actual = Plan.model_validate_json(json.dumps(plans[0]["payload"]["plan"]))
        expected_fields, actual_fields = expected.model_dump(mode="json"), actual.model_dump(mode="json")
        if (actual_fields.pop("deadline_seconds") > expected_fields.pop("deadline_seconds")
                or actual_fields != expected_fields):
            raise ValueError("Stored development plan differs beyond reserved deadline")
        identity = {"run_id":run_id,"attempt_id":attempt_id,"plan_id":actual.plan_id,
                    "corpus_sha256":expected.corpus_sha256}
        if plans[0]["payload"].get("identity") != identity:
            raise ValueError("Development plan identity differs from stored attempt")
    if len(development_contracts)!=1:
        raise ValueError("Development pair mixes different execution contracts")

