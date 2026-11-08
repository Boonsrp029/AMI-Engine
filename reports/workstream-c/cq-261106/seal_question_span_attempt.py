"""Retain assistant source adjudication after the one authorized mapper attempt."""
import hashlib
import json
from pathlib import Path
import shutil

from scripts.concurrent_mapper_check import check_protocol
from scripts._mapper_transport import read_json, sha


def write(path, value):
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    root = Path(__file__).resolve().parent
    folder = root / "question-span-2026-11-07"
    protocol_path = folder / "execution-protocol.json"
    protocol_hash = "18f0cb6c0081602d17a6870f7ed245b488e6070948a85ad59d9fe562c51ce7dc"
    protocol, proposal = check_protocol(protocol_path, protocol_hash)
    actual = folder / "actual-mapper"
    service = read_json(actual / "service/service-result.json")
    validation = read_json(actual / "validation/validation-result.json")
    summary = read_json(actual / "summary.json")
    envelope = read_json(folder / "operator-envelope/result.json")
    raw = json.loads(service["content"])
    question = proposal["plan"]["query"]
    gap = raw["components"][0]["gap"]
    selected = question[gap["start"]:gap["end"]]
    assert selected == "and" and gap == {"start": 44, "end": 47}
    assert raw["components"][0]["status"] == "partial"
    assert raw["components"][0]["evidence"] == ["s_165fe1a5aff7d74a"]
    assert service["identity_before"] and service["identity_after"]
    assert service["finish"]["done_reason"] == "stop"
    assert summary["model_calls_started"] == 1 and summary["nemo_invocations"] == summary["composer_calls"] == 0
    assert not envelope["timed_out"] and envelope["returncode"] == 0
    assert validation["status"].startswith("validated;")
    identity = {str(p.relative_to(folder)): sha(p) for p in actual.rglob("*") if p.is_file()}
    identity["operator-envelope/result.json"] = sha(folder / "operator-envelope/result.json")
    findings = {"authorship": "assistant source assessment; owner acceptance not inferred",
        "protocol_sha256": protocol_hash, "case_id": "cq-p02", "source_kind": "consumed synthetic development fixture",
        "technical_validation": "passed", "parsing": "passed", "source_span_identity": "passed",
        "source_fact_retained": "In Denmark, wind supplied 29% of total electricity generation in 2015.",
        "gap_question_membership": "passed", "selected_gap_offsets": gap, "selected_gap_text": selected,
        "semantic_missingness": "failed", "completeness": "failed for requested price gap identification",
        "expected_unresolved_request": "Denmark retail electricity prices yesterday",
        "quality_gate_pass": False,
        "diagnosis": "The model selected the conjunction instead of the missing dated price request. Valid offsets established membership only; the existing source/coverage validators do not establish gap semantics.",
        "scope_of_diagnosis": "No evidence of truncation, missing source retrieval, GPU exhaustion or malformed JSON. This does not prove an inherent open-source-model limitation or a particular internal reasoning cause.",
        "model_calls_started": 1, "composer_calls": 0, "nemo_invocations": 0,
        "usage": service["usage"], "service_elapsed_seconds": service["elapsed_seconds"],
        "controller_elapsed_seconds": summary["elapsed_seconds"], "wall_envelope_seconds": envelope["elapsed_seconds"],
        "model_digest_verified_before_and_after": True, "finish_reason": "stop",
        "fallback_used": False, "editorial_correction_used": False, "generated_draft": False,
        "owner_adjudication": "not requested for technical/semantic gap failure; earlier valid cq-p01 review stays pending",
        "approvals_created": 0, "exports_created": 0, "retry_performed": False,
        "backend_cancellation_verified": False, "monetary_hardware_cost": "unmeasured",
        "evidence_sha256": identity, "allowance_status": "closed; no conditional workflow or CQ1 authorized"}
    write(actual / "assistant-source-assessment.json", findings)
    write(actual / "allowance-closed.json", {"status": "closed at semantic quality failure",
        "assessment_sha256": sha(actual / "assistant-source-assessment.json"),
        "protocol_sha256": protocol_hash, "main_calls": 1, "composer_calls": 0, "nemo_invocations": 0,
        "retry_allowed": False, "new_grant_required_for_any_later_generation": True,
        "workflow_pair_authorized": False, "CQ1attempted": 0, "CQ1unattempted": 20})
    snapshot = folder / "executed-source-snapshot"
    snapshot.mkdir(exist_ok=False)
    files = {Path(name): digest for name, digest in proposal["runtime_inputs"].items()}
    files.update({Path(name).resolve(): digest for name, digest in protocol["project_files"].items()})
    repo = Path.cwd().resolve()
    source_manifest = {}
    for path, digest in files.items():
        assert sha(path) == digest
        relative = path.relative_to(repo)
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        assert sha(target) == digest
        source_manifest[str(relative)] = digest
    for name in (*protocol["files"], "execution-protocol.json", "direct-user-grant.json"):
        shutil.copyfile(folder / name, snapshot / name)
    write(snapshot / "manifest.json", {"executed_source_sha256": source_manifest,
        "packet_sha256": {name: sha(folder / name) for name in (*protocol["files"], "execution-protocol.json", "direct-user-grant.json")},
        "actual_output_sha256": {str(p.relative_to(folder)): sha(p) for p in actual.rglob("*") if p.is_file()},
        "protocol_sha256": protocol_hash, "actual_quality_gate_pass": False})
    print(json.dumps({"quality_gate_pass": False, "selected_gap": selected,
        "known_main_tokens": service["usage"], "source_files_snapshotted": len(source_manifest),
        "new_model_calls_for_sealing": 0}))


if __name__ == "__main__":
    main()
