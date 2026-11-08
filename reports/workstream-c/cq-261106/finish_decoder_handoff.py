"""Record terminal offline evidence and an exact next step; no inference."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main():
    contract = json.loads((ROOT / "development-contract-v6.json").read_text())
    for name, expected in contract["input_sha256"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, name
    log = (ROOT / "decoder-coverage-full.txt").read_text()
    assert "1570 passed, 14 warnings in 451.25s" in log
    findings = json.loads((ROOT / "v5-diagnostic-findings.json").read_text())
    for name, expected in findings["evidence_sha256"].items():
        assert hashlib.sha256((ROOT / "actual-development-v4" / name).read_bytes()).hexdigest() == expected
    assert not (ROOT / "development-grant-v6.json").exists()
    assert not Path(contract["output_directory"]).exists()
    audit = {"offline_suite": "1570 passed,14 warnings,451.25seconds; terminal exit0",
        "targeted": "34passed", "frozen_contract_inputs_checked": len(contract["input_sha256"]),
        "contract_sha256": contract["contract_sha256"], "v5_actual_artifacts_unchanged": True,
        "generation_calls_this_repair": 0, "new_grant_exists": False,
        "new_output_directory_exists": False, "owner_acceptance": "pending new assessable outputs",
        "actual_quality": "v5 failed; repaired decoder unverified",
        "production_qualification": "not established", "usage": "five-hour reading unavailable"}
    with (ROOT / "decoder-final-audit.json").open("x", encoding="utf-8") as stream:
        json.dump(audit, stream, indent=2)
        stream.write("\n")
    with (ROOT / "decoder-coverage-source-manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(contract["input_sha256"], stream, indent=2)
        stream.write("\n")
    handoff = json.loads((ROOT / "handoff.json").read_text())
    handoff.update(status="offline_decoder_coverage_ready_actual_generation_requires_new_grant",
        next=["No model calls until an explicit matching v6 grant exists; all previous batches remain closed.",
              "Review authorization-packet-v6.md and contract008983029a7b3d7b1523b680fe80b1c909d484821bb2b8904228ef0091bf85c8.",
              "If authorized, reverify all112 inputs/model identity and as_of date before admission; record the actual user grant without minting permission.",
              "Run cq-p01 once; assess technical/source/completeness/safety/publication. Run cq-p02 only after all gates pass. Stop at first failure; no retries.",
              "No CQ1, Ragas, hosted inference, approval/export, publication or deployment. Human source/wording review only for new assessable outputs."],
        full_suite=audit["offline_suite"], active_full_suite_session=None,
        active_full_suite_log="reports/workstream-c/concurrent-qualification-2026-11-06/decoder-coverage-full.txt",
        prepared_contract=contract["contract_sha256"], final_contract_sha256=contract["contract_sha256"],
        closed_batch="actual-development-v4; cq-p01 omitted s02 support, one main call, zero NeMo, no saved draft; cq-p02/CQ1unattempted",
        offline_repair=audit,
        cumulative_actual={"main_request_starts":5,"nemo_invocations":1,
                           "interrupted_backend_tokens":"unknown", "internal_nemo_usage":"unknown"})
    handoff.pop("generation_calls", None)
    handoff["known_failure"] = "Actual v5 supported mapping omitted s02; application rejected before composition/NeMo/publication. Decoder repair has offline proof only."
    (ROOT / "handoff.json").write_text(json.dumps(handoff, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(audit))


if __name__ == "__main__":
    main()
