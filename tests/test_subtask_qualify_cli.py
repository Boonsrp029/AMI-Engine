"""Command admission and per-call checks with no local/hosted inference."""
import hashlib
import json
from types import SimpleNamespace
import pytest
from test_subtask_qualification_runner import ledger as make_ledger
from src.pilot.subtasks.qualify_cli import main
from src.pilot.subtasks.context_gate import BoundedTransport


def contract_file(tmp_path):
    l = make_ledger(tmp_path)
    p = tmp_path / "contract.json"
    p.write_text(json.dumps(l.contract), encoding="utf-8")
    return p


def test_verify_command_has_no_model_or_store_side_effects(tmp_path, monkeypatch, capsys):
    from src.pilot import _model_identity
    monkeypatch.setattr(_model_identity, "verify_model", lambda *_: pytest.fail("metadata access"))
    p = contract_file(tmp_path)
    assert main(["--contract", str(p)]) == 0
    assert not (tmp_path / "out").exists()
    assert json.loads(capsys.readouterr().out)["execution_authorized"] is False


def test_command_attempt_without_grant_aborts_before_clients(tmp_path):
    p = contract_file(tmp_path)
    with pytest.raises(SystemExit):main(["--contract", str(p), "--mode", "attempt", "--case", "p01"])
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("mode", ["ok", "oversize", "changed"])
def test_runtime_budget_and_model_identity_fence_transport(tmp_path, monkeypatch, mode):
    import scripts._llama_token_count as tokenizer
    from src.pilot import _model_identity
    p = tmp_path / "tokens.json"
    p.write_text("{}")
    calls, checks = [], []
    monkeypatch.setattr(tokenizer, "encoding", lambda _: SimpleNamespace(encode=lambda text: [0] * (5000 if mode == "oversize" else 2)))
    def verify(snapshot):
        checks.append(snapshot)
        if mode == "changed":raise ValueError("changed model")
    monkeypatch.setattr(_model_identity, "verify_model", verify)
    def transport(*args):calls.append(args);return {"parsed":"synthetic"}
    gate = BoundedTransport(transport, {"synthetic":True}, str(p), hashlib.sha256(p.read_bytes()).hexdigest())
    schema = SimpleNamespace(model_json_schema=lambda: {})
    if mode == "ok":
        assert gate("mapping", schema, "instruction", {}) == {"parsed":"synthetic"}
        assert len(checks) == 2 and len(calls) == 1
    else:
        with pytest.raises(ValueError):gate("mapping", schema, "instruction", {})
        assert calls == []
