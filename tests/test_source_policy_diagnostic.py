"""Diagnostic supervision/attribution only; fixed responses do not prove entailment."""
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from scripts import diagnose_source_policy as diagnostic


@pytest.mark.parametrize("answer,passed", [("YES.", True), ("NO", False), ("YES because it is supported", False)])
def test_single_verdict_contract_and_once_only_policy_invocation(monkeypatch, tmp_path, answer, passed):
    from src.utils import guardrails_runner
    calls = []
    class Guard:
        def __init__(self):
            self.rails = SimpleNamespace(register_output_parser=self.register,
                runtime=SimpleNamespace(llm_task_manager=SimpleNamespace(render_task_prompt=lambda *a, **k: "fixed rendered prompt")))
        def register(self, parse, name):
            self.parse = parse
        def validate_output(self, report, context, user_input):
            calls.append((report, context))
            return {"passed_guardrails": not self.parse(answer)[0]}
    monkeypatch.setattr(guardrails_runner, "GuardrailsRunner", Guard)
    result = tmp_path / "result.json"
    assert diagnostic.worker({"id": "j01", "context": "Fixed causal evidence", "report": "Fixed report", "expected_single_verdict": "YES"}, result) == 0
    record = json.loads(result.read_text(encoding="utf-8"))
    assert record["contract_passed"] is passed
    assert record["guard_invocations"] == len(calls) == 1
    assert record["internal_tokens"] is None


def test_timeout_retains_partial_logs_and_stops_without_retry(monkeypatch, tmp_path):
    fixture = Path("data/pilot/policy-diagnostic-2026-10-27.json")
    output = tmp_path / "diagnostic"
    calls = []
    def timeout(command, **kwargs):
        calls.append((command, kwargs))
        raise subprocess.TimeoutExpired(command, kwargs["timeout"], output=b"partial", stderr=b"diagnostic")
    monkeypatch.setattr(subprocess, "run", timeout)
    assert diagnostic.main(["--fixtures", str(fixture), "--expected-sha256", diagnostic.sha(fixture), "--output", str(output)]) == 1
    assert len(calls) == 1 and calls[0][1]["timeout"] == 60
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert len(summary["unattempted"]) == 5
    assert summary["cases"][0]["inflight_usage_unknown"] is True
    assert (output / "stdout-j01.txt").read_bytes() == b"partial"
    with pytest.raises(FileExistsError):
        diagnostic.main(["--expected-sha256", diagnostic.sha(fixture), "--output", str(output)])
    assert len(calls) == 1
