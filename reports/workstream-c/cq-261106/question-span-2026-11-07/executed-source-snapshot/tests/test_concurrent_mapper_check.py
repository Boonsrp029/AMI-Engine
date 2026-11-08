"""Mocked authorization/process controls; synthetic grants authorize no inference."""
import json
from pathlib import Path
import time

import pytest

from scripts import concurrent_mapper_check as controller
from scripts._mapper_transport import sha, request_body


def write(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def packet(tmp_path, monkeypatch):
    from src.pilot.subtasks.contracts import Plan, Subtask
    from src.pilot.subtasks.generation import ConcurrentComposer
    from src.pilot.subtasks.retrieval import LocalBM25Adapter
    from src.pilot.subtasks.scheduler import run_plan
    from src.pilot.subtasks.runner import ModelAccess
    project = Path.cwd()
    for name in controller.REQUIRED_PROJECT_FILES:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((project / name).read_bytes())
    (tmp_path / "src").mkdir()
    (tmp_path / "src/synthetic.py").write_text("# Synthetic pinning fixture\n")
    for name in ("requirements.txt", "requirements-serving.txt", "constraints-pilot.txt"):
        (tmp_path / name).write_text("# synthetic dependency declaration\n")
    corpus = tmp_path / "corpus.json"
    write(corpus, [{"feed_id": "solar", "clean_content": "In Peru, solar supplied 16% of total electricity generation in 2013."}])
    question = "Describe solar generation in Peru in 2013 and provide Peru retail gas tariffs yesterday."
    plan = Plan(query=question, corpus_sha256=sha(corpus), subtasks=(
        Subtask(subtask_id="s01", operation="retrieve", query="solar"),
        Subtask(subtask_id="s02", operation="retrieve", query="unknownrates")))
    case = {"plan": plan.model_dump(mode="json"), "corpus_path": str(corpus), "corpus_sha256": sha(corpus),
        "case_id": "cq-p02", "bindings": {"r1": ["s01", "s02"]}, "as_of": "2026-11-07",
        "complete_required_branches": {"r1": ["s01", "s02"]}, "model_snapshot": {"digest": "a" * 64}}
    frozen = {}
    inputs = {}
    class Captured(Exception):
        pass
    def capture(stage, schema, instruction, value):
        assert stage == "mapping"
        inputs.update(value)
        frozen.update(schema=schema.model_json_schema(), messages=[
            {"type": "system", "content": instruction},
            {"type": "human", "content": json.dumps(value, ensure_ascii=False, separators=(",", ":"))}])
        raise Captured()
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(corpus))
    with pytest.raises(Captured):
        ConcurrentComposer(plan, case["bindings"], case["as_of"], capture,
            complete_required_branches=case["complete_required_branches"])(report, ModelAccess(time.monotonic() + 30))
    folder = tmp_path / "packet"
    folder.mkdir()
    write(folder / "input.json", frozen)
    write(folder / "native.json", request_body(frozen))
    runtime = [*tmp_path.glob("src/*.py"), *(tmp_path / n for n in ("requirements.txt", "requirements-serving.txt", "constraints-pilot.txt"))]
    case.update(runtime_inputs={str(p.resolve()): sha(p) for p in runtime},
        input_sha256={str((folder / n).resolve()): sha(folder / n) for n in ("input.json", "native.json")})
    write(folder / "proposal.json", case)
    protocol = {"kind": "concurrent-mapper-only-v1", "limits": controller.LIMITS, "model": controller.MODEL,
        "case_id": "cq-p02", "output_directory": "actual-mapper", "input": "input.json", "native_body": "native.json",
        "proposal": "proposal.json", "native_body_sha256": sha(folder / "native.json"), "model_digest": "a" * 64,
        "authorization_reply": "SYNTHETIC TEST ONLY; never actual authorization",
        "project_files": {n: sha(tmp_path / n) for n in controller.REQUIRED_PROJECT_FILES},
        "files": {n: sha(folder / n) for n in ("input.json", "native.json", "proposal.json")}}
    path = folder / "protocol.json"
    write(path, protocol)
    source = inputs["evidence"][0]["spans"][0]["span_id"]
    start = question.index("Peru retail gas")
    response = {"wire_version": "cq-question-span-v1", "components": [{"component_id": "r1", "status": "partial",
        "evidence": [source], "gap": {"start": start, "end": len(question)-1}}],
        "geography": {"status": "unresolved", "value": "", "evidence": [], "reason": "Synthetic scope test."}}
    monkeypatch.chdir(tmp_path)
    return path, protocol, response


def grant(path, protocol):
    auth = path.parent / "synthetic-grant.json"
    write(auth, {"contract_sha256": sha(path), "human_reply": protocol["authorization_reply"],
        "authorization_reference": "SYNTHETIC TEST ONLY"})
    return auth


def service(response):
    return {"status": "completed_transport", "response_complete": True, "model_calls_started": 1,
        "identity_before": True, "identity_after": True, "finish": {"done_reason": "stop"},
        "content": json.dumps(response), "usage": {"input_tokens": 10, "output_tokens": 8, "total_tokens": 18},
        "inflight_usage_unknown": False}


def test_inspect_has_no_service_or_output(packet, monkeypatch):
    path, _, _ = packet
    monkeypatch.setattr(controller, "supervise", lambda *a: pytest.fail("No service during inspection"))
    assert controller.main(["--protocol", str(path), "--sha256", sha(path)]) == 0
    assert not (path.parent / "actual-mapper").exists()


@pytest.mark.parametrize("damage", ["missing_reference", "wrong_reply", "wrong_protocol"])
def test_new_grant_required_before_output(packet, monkeypatch, damage):
    path, p, _ = packet
    auth = grant(path, p)
    value = json.loads(auth.read_text())
    value[{"missing_reference": "authorization_reference", "wrong_reply": "human_reply", "wrong_protocol": "contract_sha256"}[damage]] = ""
    write(auth, value)
    monkeypatch.setattr(controller, "supervise", lambda *a: pytest.fail("No service without authorization"))
    with pytest.raises(ValueError, match="user grant"):
        controller.execute(path, sha(path), auth)
    assert not (path.parent / "actual-mapper").exists()


@pytest.mark.parametrize("damage", ["input", "corpus", "runtime", "added_module", "path_escape", "limits"])
def test_frozen_identity_and_scope_are_strict(packet, damage):
    path, p, _ = packet
    if damage == "input":
        (path.parent / "input.json").write_text("{}")
    elif damage == "corpus":
        Path("corpus.json").write_text("[]")
    elif damage == "runtime":
        Path("src/synthetic.py").write_text("# drift")
    elif damage == "added_module":
        Path("src/new.py").write_text("# new module")
    else:
        if damage == "path_escape":
            p["files"] = {"../../outside.json": "a" * 64}
        else:
            p["limits"] = {**p["limits"], "main_calls": 2}
        write(path, p)
    with pytest.raises(ValueError):
        controller.check_protocol(path, sha(path))


def test_timeout_is_terminal_no_validation_and_no_restart(packet, monkeypatch):
    path, p, _ = packet
    calls = []
    def timeout(command, output, seconds):
        calls.append(command)
        assert 0 < seconds <= 60
        output.mkdir()
        write(output / "service-progress.json", {"model_calls_started": 1, "response_complete": False})
        return {"timed_out": True, "returncode": -1}
    monkeypatch.setattr(controller, "supervise", timeout)
    auth = grant(path, p)
    result = controller.execute(path, sha(path), auth)
    assert result["status"] == "failed; allowance closed" and result["inflight_usage_unknown"]
    assert len(calls) == 1 and result["nemo_invocations"] == result["composer_calls"] == 0
    with pytest.raises(FileExistsError):
        controller.execute(path, sha(path), auth)


def test_fixed_partial_validates_without_inference_or_semantic_acceptance(packet, monkeypatch):
    path, p, response = packet
    calls = []
    def fixed(command, output, seconds):
        calls.append(command)
        output.mkdir()
        if output.name == "service":
            assert 0 < seconds <= 60
            write(output / "service-result.json", service(response))
        else:
            assert 0 < seconds <= 30
            result = controller.validate_response(path, sha(path), output.parent / "service/service-result.json", output)
            assert result["network_blocked"] and result["status"].startswith("validated;")
            assert result["replay"]["actual_composer_calls"] == result["replay"]["nemo_invocations"] == 0
        return {"timed_out": False, "returncode": 0}
    monkeypatch.setattr(controller, "supervise", fixed)
    result = controller.execute(path, sha(path), grant(path, p))
    assert len(calls) == 2 and result["status"] == "validated; source review pending; allowance closed"
    assert result["source_assessment"] == result["owner_adjudication"] == "pending"
    assert result["conditional_workflow_authorized"] is False
    assert result["approvals_created"] == result["exports_created"] == 0


def test_exhausted_overall_budget_cannot_start_validation(packet, monkeypatch):
    path, p, response = packet
    now = [0.0]
    calls = []
    monkeypatch.setattr(controller.time, "monotonic", lambda: now[0])
    def slow(command, output, seconds):
        calls.append(command)
        output.mkdir()
        write(output / "service-result.json", service(response))
        now[0] = 96
        return {"timed_out": False, "returncode": 0}
    monkeypatch.setattr(controller, "supervise", slow)
    result = controller.execute(path, sha(path), grant(path, p))
    assert len(calls) == 1 and result["status"] == "failed; allowance closed"
    assert result["elapsed_budget_exceeded"] and result["error_type"] == "TimeoutError"


@pytest.mark.parametrize("damage", ["source_quote", "unknown_source", "wrong_wire", "truncated", "identity", "wrong_gap_semantics"])
def test_bad_mapping_or_transport_never_becomes_quality_success(packet, damage):
    path, _, response = packet
    record = service(response)
    c = response["components"][0]
    if damage == "source_quote":
        c.pop("gap"); c["gap_anchor"] = "In Peru, solar supplied 16%."
    elif damage == "unknown_source":
        c["evidence"] = ["invented"]
    elif damage == "wrong_wire":
        response["wire_version"] = "source-selection-v1"
    elif damage == "truncated":
        record["finish"]["done_reason"] = "length"
    elif damage == "identity":
        record["identity_after"] = False
    else:
        c["gap"] = {"start": 0, "end": 8}  # In-range does not imply an actual missing fact.
    record["content"] = json.dumps(response)
    retained = path.parent / "fixed-service.json"
    write(retained, record)
    output = path.parent / "offline-validation"; output.mkdir()
    result = controller.validate_response(path, sha(path), retained, output)
    if damage == "wrong_gap_semantics":
        assert result["status"].startswith("validated;") and result["source_assessment"] == "pending"
    else:
        assert result["status"] == "failed"
    assert result["actual_model_calls"] == result["nemo_invocations"] == 0
