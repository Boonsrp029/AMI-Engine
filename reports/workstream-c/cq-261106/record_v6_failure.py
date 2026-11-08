"""Seal failed v6 evidence and source identities before any later offline edits."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "actual-development-v5"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_once(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    contract = json.loads((ROOT / "development-contract-v6.json").read_text())
    assert all(sha(name) == expected for name, expected in contract["input_sha256"].items())
    result = json.loads((OUTPUT / "cq-p01.result.json").read_text())
    assert result["technical_pass"] is False and (OUTPUT / "stopped.json").exists()
    assert not (OUTPUT / "cq-p02.started.json").exists()
    assert not (OUTPUT / "cq-p01.safety.json").exists()
    usage = {"input_tokens":0, "output_tokens":0, "total_tokens":0}
    for stage in ("mapping", "composition"):
        response = json.loads((OUTPUT / f"cq-p01.{stage}.raw.json").read_text())
        assert response["response_metadata"]["done_reason"] == "stop"
        for key in usage:
            usage[key] += response["usage"][key]
    snapshot = ROOT / "v6-failure-source-snapshot"
    snapshot.mkdir()
    copies = {}
    for name in ("src/pilot/subtasks/generation.py", "src/pilot/subtasks/_coverage_decoder.py",
                 "src/pilot/subtasks/_coverage.py", "src/pilot/subtasks/synthesis.py",
                 "src/pilot/subtasks/_relationships.py", "src/pilot/_composition.py",
                 "src/pilot/_scope.py", "src/pilot/subtasks/runner.py"):
        target = snapshot / Path(name).name
        target.write_bytes(Path(name).read_bytes())
        copies[name] = {"snapshot":target.name, "sha256":sha(target)}
    write_once(snapshot / "manifest.json", copies)
    findings = {"status":"v6 composition gate failed; allowance closed",
        "contract_sha256":contract["contract_sha256"], "technical_pass":False,
        "mapping_schema":"passed with both required source spans", "mapping_coverage":"passed",
        "raw_composition":"duplicated unsupported relative comparison in both units; omitted2.6percentprojection",
        "confirmed_replay_error":"Draft introduces a numeric value absent from its selected evidence",
        "failure_class":"unit-local evidence binding; not a demonstrated retrieval/schema/truncation/GPU-capacity defect",
        "main_requests":result["main_calls"], "nemo_invocations":result["nemo_invocations"],
        "known_main_usage_from_raw":usage, "finish_reasons":["stop","stop"],
        "elapsed_seconds":result["elapsed_seconds"],
        "stored_metrics_usage":"incomplete because worker failed; raw response usage retained separately",
        "internal_nemo_usage":"none invoked in this batch", "monetary_hardware_cost":"unmeasured",
        "publication":"not attempted; revision0, draft null", "development_planned":2,
        "development_attempted":["cq-p01"], "development_unattempted":["cq-p02"],
        "CQ1attempted":0, "CQ1unattempted":20,
        "evidence_sha256":{p.name:sha(p) for p in OUTPUT.glob("*.json")},
        "frozen_contract_verified_after_execution":True,
        "new_model_calls_for_diagnosis":0,
        "owner_review":"not requested for rejected technical output",
        "next":"Offline composition-contract diagnosis and different-fact regressions; no automatic retries, tuning within closed batch or qualification claim"}
    write_once(ROOT / "v6-diagnostic-findings.json", findings)
    handoff = json.loads((ROOT / "handoff.json").read_text())
    handoff.update(status="active_v6_composition_gate_failed_allowance_closed",
        latest_actual_result=findings, active_diagnostic_session=None,
        closed_batch="actual-development-v5; cq-p01 unit-binding failure,2main0NeMo; cq-p02/CQ1unattempted",
        next=["No generation: v6 closed at first failure; do not run cq-p02 or CQ1.",
              "Inspect v6-offline-replay.json and v6-failure-source-snapshot for exact unit-local numeric rejection.",
              "Compare existing composition instructions/unit cues against duplicated relative claim; propose any private composition-contract change explicitly.",
              "Use different synthetic facts for regression; retain strict validation, current failed outcomes and reserved evidence."],
        cumulative_actual={"main_request_starts":7, "nemo_invocations":1,
            "known_completed_main_input_tokens":3885,"known_completed_main_output_tokens":709,
            "known_completed_main_total_tokens":4594,
            "interrupted_backend_tokens":"unknown","internal_nemo_usage":"unknown"})
    (ROOT / "handoff.json").write_text(json.dumps(handoff, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"failure_sealed":True, "usage":usage, "generation_closed":True}))


if __name__ == "__main__":
    main()
