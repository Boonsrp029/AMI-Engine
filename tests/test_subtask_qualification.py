"""Synthetic grant documents test admission mechanics, not real authorization."""
import hashlib
import json
import pytest
from src.pilot.subtasks.qualification import DevelopmentLedger, digest


def ledger(tmp_path, grant=True):
    source = tmp_path / "source.json"
    source.write_text("[]")
    contract = {"case_ids": ["p01", "p02"], "input_sha256": {str(source): digest(source)},
        "limits": {"main_calls_per_case": 4, "nemo_per_case": 1, "seconds_per_case": 180, "retries": 0}}
    contract["contract_sha256"] = hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    authorization = {"contract_sha256": contract["contract_sha256"], "case_ids": contract["case_ids"],
        "limits": contract["limits"], "authorization_reference": "SYNTHETIC TEST ONLY"} if grant else None
    return DevelopmentLedger(tmp_path / "out", contract, authorization), source


def result(**changes):
    return {"technical_pass": True, "main_calls": 2, "nemo_invocations": 1, "elapsed_seconds": 12, **changes}


@pytest.mark.parametrize("mode", ["missing", "changed", "scope", "order"])
def test_no_attempt_without_matching_grant_inputs_and_prior_review(tmp_path, mode):
    l, source = ledger(tmp_path, mode != "missing")
    if mode == "changed":
        source.write_text("changed")
    if mode == "scope":
        l.grant["case_ids"] = ["other"]
    with pytest.raises(ValueError):
        l.start("p02" if mode == "order" else "p01")
    assert not list(l.output.glob("*.started.json"))


def test_once_only_and_exact_source_review_required(tmp_path):
    l, _ = ledger(tmp_path)
    l.start("p01")
    with pytest.raises(FileExistsError):
        l.start("p01")
    l.finish("p01", result())
    with pytest.raises(ValueError):
        l.start("p02")
    l.assess("p01", {"verdict": "pass", "source_findings": ["synthetic support check"],
        "result_sha256": digest(l.output / "p01.result.json")})
    l.start("p02")
    with pytest.raises(FileExistsError):
        l.assess("p01", {"verdict": "pass", "source_findings": ["changed"],
            "result_sha256": digest(l.output / "p01.result.json")})


@pytest.mark.parametrize("changes", [{"main_calls": 5}, {"nemo_invocations": 2},
    {"elapsed_seconds": 181}, {"technical_pass": False}])
def test_failed_attempt_closes_batch_and_retains_result(tmp_path, changes):
    l, _ = ledger(tmp_path)
    l.start("p01")
    with pytest.raises(ValueError):
        l.finish("p01", result(**changes))
    assert (l.output / "p01.result.json").exists()
    with pytest.raises(ValueError):
        l.start("p02")


def test_failed_source_review_cannot_be_regraded_to_continue(tmp_path):
    l, _ = ledger(tmp_path)
    l.start("p01")
    l.finish("p01", result())
    l.assess("p01", {"verdict": "fail", "source_findings": ["unsupported"],
        "result_sha256": digest(l.output / "p01.result.json")})
    with pytest.raises(ValueError):
        l.start("p02")
