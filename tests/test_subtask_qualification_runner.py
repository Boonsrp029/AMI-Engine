"""Spawned end-to-end development execution with synthetic grants/responses."""
import hashlib
import json
import pytest
from test_subtask_generation import fixture, FixedTransport
from src.pilot.subtasks.qualification import DevelopmentLedger, digest
from src.pilot.subtasks.qualification_runner import execute_development


def safety(draft, sources):
    return True


def verify_identity(snapshot):
    assert snapshot == {"synthetic": True}


def ledger(tmp_path, granted=True):
    plan, _ = fixture(tmp_path)
    path = tmp_path / "corpus.json"
    case = {"plan": plan.model_dump(mode="json"), "corpus_path": str(path), "bindings": {"r1": ["s01"]}}
    contract = {"case_ids": ["p01", "p02"], "input_sha256": {str(path): digest(path)},
        "as_of": "2026-11-06", "model_snapshot": {"synthetic": True}, "cases": {"p01": case, "p02": case},
        "limits": {"main_calls_per_case": 4, "nemo_per_case": 1, "seconds_per_case": 180, "retries": 0}}
    contract["contract_sha256"] = hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    grant = {"contract_sha256": contract["contract_sha256"], "case_ids": contract["case_ids"],
        "limits": contract["limits"], "authorization_reference": "SYNTHETIC TEST ONLY"} if granted else None
    return DevelopmentLedger(tmp_path / "out", contract, grant)


def test_real_owned_runner_with_fixed_transport_and_review_gate(tmp_path):
    l = ledger(tmp_path)
    result = execute_development(l, "p01", FixedTransport(), safety, verify_identity)
    assert result["technical_pass"] and result["main_calls"] == 2 and result["nemo_invocations"] == 1
    assert result["source_assessment"] == result["owner_adjudication"] == "pending"
    assert (l.output / "p01.review.json").exists()
    assert result["stored_run"]["metrics"]["composition_provenance"]
    raw = json.loads((l.output / "p01.mapping.raw.json").read_text())
    assert raw["identity"]["run_id"] == result["stored_run"]["id"]
    assert raw["raw"] and (l.output / "p01.composition.raw.json").exists()
    with pytest.raises(ValueError, match="review is pending"):
        execute_development(l, "p02", FixedTransport(), safety, verify_identity)


def test_no_grant_creates_no_store_or_model_request(tmp_path):
    l = ledger(tmp_path, granted=False)
    with pytest.raises(ValueError, match="execution grant"):
        execute_development(l, "p01", FixedTransport(), safety, verify_identity)
    assert not l.output.exists()


def test_parser_failure_is_retained_and_closes_batch(tmp_path):
    l = ledger(tmp_path)
    with pytest.raises(ValueError, match="execution gate"):
        execute_development(l, "p01", FixedTransport(malformed=True), safety, verify_identity)
    result = json.loads((l.output / "p01.result.json").read_text())
    assert not result["technical_pass"] and result["failure_type"]
    raw = json.loads((l.output / "p01.mapping.raw.json").read_text())
    assert raw["raw"] == "invalid wire"
    assert not (l.output / "p01.composition.raw.json").exists()
    assert (l.output / "stopped.json").exists()
    with pytest.raises(ValueError, match="closed"):
        execute_development(l, "p02", FixedTransport(), safety, verify_identity)


def test_local_safety_forces_loopback_and_restores_environment(tmp_path, monkeypatch):
    import os
    import sys
    from types import SimpleNamespace
    from src.pilot.subtasks.qualification_runner import LocalSafety
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OLLAMA_BASE_URL", "https://example.invalid")
    class FakeGuard:
        def __init__(self):
            assert os.environ["AGENT_LLM_PROVIDER"] == "ollama"
            assert os.environ["OLLAMA_BASE_URL"] == "http://localhost:11434"
            assert os.environ["AGENT_LLM_MODEL"] == "pinned-test-model"
        def validate_output(self, **kwargs):
            assert kwargs == {"user_input":"test", "raw_report":"supported", "context":"evidence"}
            return {"passed_guardrails": True, "guardrail_status":"synthetic-pass"}
    monkeypatch.setitem(sys.modules, "src.utils.guardrails_runner", SimpleNamespace(GuardrailsRunner=FakeGuard))
    assert LocalSafety("test", "pinned-test-model", str(tmp_path), "p01")(
        {"claims":[{"text":"supported"}]}, {"s1":{"content":"evidence"}})
    assert json.loads((tmp_path/"p01.safety.json").read_text())["guardrail_status"] == "synthetic-pass"
    assert os.environ["AGENT_LLM_PROVIDER"] == "openai"
    assert os.environ["OLLAMA_BASE_URL"] == "https://example.invalid"


@pytest.mark.parametrize("mode", ["match", "wrong_quantity", "wrong_citation", "ambiguous", "default"])
def test_capacity_evidence_view_keeps_full_context_and_guard_verdict(tmp_path, monkeypatch, mode):
    import hashlib
    import sys
    from types import SimpleNamespace
    from src.pilot.subtasks.qualification_runner import CAPACITY_EVIDENCE_FIRST, LocalSafety

    question = "What minimum total payload capacity does the guide specify, in kilograms and grams?"
    passage = "Eligible crates carry at least 3 kilograms (or 3,000 grams) of total payload capacity."
    text = "The minimum total payload capacity is 3 kilograms (or 3,000 grams)."
    sources = {"record": {"content": passage}, "other": {"content": "Earlier crates used wooden lids."}}
    if mode == "ambiguous":
        sources["other"]["content"] = passage.replace("3 kilograms", "4 kilograms").replace("3,000", "4,000")
    if mode == "wrong_quantity":
        text = text.replace("3,000", "4,000")
    full = "\n".join(source["content"] for source in sources.values())
    expected = (f"Selected source excerpt:\n{passage}\n\nComplete retrieved evidence:\n{full}"
                if mode == "match" else full)
    calls = []

    class FakeGuard:
        def validate_output(self, **kwargs):
            calls.append(kwargs)
            return {"passed_guardrails": False, "blocking_rail": "self check facts"}

    monkeypatch.setitem(sys.modules, "src.utils.guardrails_runner", SimpleNamespace(GuardrailsRunner=FakeGuard))
    view = None if mode == "default" else CAPACITY_EVIDENCE_FIRST
    claim = {"text": text, "source_ids": ["other" if mode == "wrong_citation" else "record"]}
    assert LocalSafety(question, "model", str(tmp_path), "p01", evidence_view=view)(
        {"claims": [claim]}, sources) is False
    assert calls == [{"user_input": question, "raw_report": text, "context": expected}]
    saved = json.loads((tmp_path / "p01.safety.json").read_text())
    if view is None:
        assert "evidence_view" not in saved
    else:
        assert saved["context_sha256"] == hashlib.sha256(expected.encode()).hexdigest()
        assert (saved["leading_excerpt"] is not None) == (mode == "match")


@pytest.mark.parametrize("attributed", [False, True])
def test_directed_power_safety_view_records_the_real_parser_decision(tmp_path, monkeypatch, attributed):
    from src.utils import guardrails_runner
    from src.pilot.subtasks.qualification_runner import POWER_EVIDENCE_FIRST, LocalSafety

    quote = "Terawatts (TW): One TW is 1,000 GW, or 1,000,000,000 kW."
    question = "How many kilowatts are equivalent to one terawatt in the guide?"
    claim = "One terawatt is equivalent to 1,000,000,000 kilowatts"
    claim += " in the Thermal Grid Handbook." if attributed else "."

    class FixedGuard:
        def __init__(self):
            self.rails = self

        def register_output_parser(self, callback, name):
            assert name == "strict_source_grounding"
            self.parser = callback

        def validate_output(self, *, user_input, raw_report, context):
            assert user_input == question and raw_report == claim
            assert context == f"Selected source excerpt:\n{quote}\n\nComplete retrieved evidence:\n{quote}\nUnrelated context."
            assert self.parser("YES with explanation") == [True]
            return {"passed_guardrails": False, "blocking_rail": "self check facts"}

    monkeypatch.setattr(guardrails_runner, "GuardrailsRunner", FixedGuard)
    assert LocalSafety(question, "model", str(tmp_path), "test", evidence_view=POWER_EVIDENCE_FIRST)(
        {"claims": [{"text": claim, "source_ids": ["s1"]}]},
        {"s1": {"content": quote, "title": "Thermal Grid Handbook"},
         "s2": {"content": "Unrelated context."}}) is False
    saved = json.loads((tmp_path / "test.safety.json").read_text())
    assert saved["raw_fact_verdicts"] == ["YES with explanation"]
    assert saved["leading_excerpt"]["text"] == quote
