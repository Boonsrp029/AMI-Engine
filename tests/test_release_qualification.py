"""Supervisor integrity/deadline gates without invoking a model or a container."""
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from src.pilot.qualify import identity, load_package, run_attempt, sha, verify_preflights
from src.pilot._model_identity import expected_snapshot
from src.pilot import qualify


def package_fixture(tmp_path):
    root = tmp_path/"sources"
    root.mkdir()
    (root/"source.html").write_text("Synthetic source snapshot", encoding="utf-8")
    package = root/"frozen"
    (package/"corpora").mkdir(parents=True)
    rows = [{"case_id": f"r{i:02}", "split": "heldout", "corpus": "public"} for i in range(1, 21)]
    rows += [{"case_id": cid, "split": "preflight", "corpus": "public"} for cid in ("p01", "p02")]
    files = {"cases.json": rows, "corpora/public.json": [{"clean_content": "Synthetic source snapshot"}],
             "sources.json": {"SYNTHETIC": {"file": "source.html", "sha256": sha(root/"source.html")}}}
    for name, data in files.items():
        (package/name).write_text(json.dumps(data), encoding="utf-8")
    manifest = {"sha256": {name: sha(package/name) for name in files}, "heldout_count": 20, "preflight_count": 2}
    (package/"manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return package


def test_frozen_package_rejects_changed_corpus_and_changed_outer_manifest(tmp_path):
    package = package_fixture(tmp_path)
    expected = sha(package/"manifest.json")
    assert len(load_package(package, expected)[2]) == 22
    with pytest.raises(ValueError, match="declared frozen identity"):
        load_package(package, "0"*64)
    (package/"corpora/public.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        load_package(package, expected)


def test_deadline_kills_only_owned_worker_retains_unknown_usage_and_prevents_repeat(monkeypatch, tmp_path):
    package = package_fixture(tmp_path)
    output = tmp_path/"attempts"
    output.mkdir()

    class HangingWorker:
        pid = 1234
        waits = 0
        killed = False

        def wait(self, timeout=None):
            self.waits += 1
            if self.waits == 1:
                raise subprocess.TimeoutExpired("synthetic worker", timeout)
            return -9

        def kill(self):
            self.killed = True

    fake = HangingWorker()
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **k: fake)
    result = run_attempt(package, "p01", output, timeout=1)
    assert fake.killed and fake.waits == 2
    assert result["timed_out"] and result["inflight_usage_unknown"]
    assert result["status"] == "technical_failure" and (output/"started-p01.json").exists()
    with pytest.raises(ValueError, match="retried"):
        run_attempt(package, "p01", output)
    with pytest.raises(ValueError, match="180"):
        run_attempt(package, "p02", output, timeout=181)


def preflight_fixture(tmp_path):
    identity = {"generation_sha256": "generator", "package_sha256": "package", "model_content": expected_snapshot("a" * 64)}
    assessment = {"author": "assistant-authored preflight assessment", "status": "passed", **identity, "cases": {}}
    for cid, status in (("p01", "answered"), ("p02", "abstained")):
        path = tmp_path/f"{cid}.json"
        path.write_text(json.dumps({"case_id": cid, "status": status, "identity": identity}), encoding="utf-8")
        process_path = tmp_path/f"process-result-{cid}.json"
        process_path.write_text(json.dumps({"case_id": cid, "process_returncode": 0, "timed_out": False,
            "status": status, "attempt_sha256": sha(path), "identity_verified": True}), encoding="utf-8")
        assessment["cases"][cid] = {"attempt": str(path), "sha256": sha(path), "verdict": "passed", "process_result_sha256": sha(process_path)}
    path = tmp_path/"assessment.json"
    path.write_text(json.dumps(assessment), encoding="utf-8")
    return identity, path


def test_heldout_gate_requires_both_unchanged_successful_preflights(tmp_path):
    identity, path = preflight_fixture(tmp_path)
    verify_preflights(path, identity)
    with pytest.raises(ValueError, match="different generator"):
        verify_preflights(path, {**identity, "generation_sha256": "changed"})
    (tmp_path/"p01.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="evidence changed"):
        verify_preflights(path, identity)


@pytest.mark.parametrize("failure", ["wrong_attempt_identity", "nonzero_exit", "missing_process", "changed_process", "unpinned_model"])
def test_assessment_cannot_promote_wrong_generator_or_bad_process(tmp_path, failure):
    current, path = preflight_fixture(tmp_path)
    assessment = json.loads(path.read_text(encoding="utf-8"))
    process_path = tmp_path/"process-result-p01.json"
    if failure == "wrong_attempt_identity":
        attempt = tmp_path/"p01.json"
        data = json.loads(attempt.read_text(encoding="utf-8"))
        data["identity"]["model_content"] = expected_snapshot("b" * 64)
        attempt.write_text(json.dumps(data), encoding="utf-8")
        assessment["cases"]["p01"]["sha256"] = sha(attempt)
    elif failure == "nonzero_exit":
        process = json.loads(process_path.read_text(encoding="utf-8"))
        process["process_returncode"] = -1073741816
        process_path.write_text(json.dumps(process), encoding="utf-8")
        assessment["cases"]["p01"]["process_result_sha256"] = sha(process_path)
    elif failure == "missing_process":
        process_path.unlink()
    elif failure == "changed_process":
        process_path.write_text("{}", encoding="utf-8")
    else:
        current["model_content"] = None
    path.write_text(json.dumps(assessment), encoding="utf-8")
    with pytest.raises(ValueError):
        verify_preflights(path, current)


def test_period_backstop_changes_invalidate_generator_identity(monkeypatch, tmp_path):
    package = package_fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    helper = tmp_path / "src/utils/_periods.py"
    helper.parent.mkdir(parents=True)
    helper.write_text("first implementation", encoding="utf-8")
    before = identity(package)
    helper.write_text("revised implementation", encoding="utf-8")
    after = identity(package)
    assert before["generation_sha256"] != after["generation_sha256"]
    assert before["package_sha256"] == after["package_sha256"]


def test_verification_mode_never_contacts_model(monkeypatch, tmp_path, capsys):
    package = package_fixture(tmp_path)
    monkeypatch.setattr(qualify, "inspect_model", lambda: (_ for _ in ()).throw(AssertionError("Unexpected metadata request")))
    assert qualify.main(["--package", str(package)]) == 0
    assert "verified; no generation" in capsys.readouterr().out


def test_generation_supervisor_passes_one_pinned_identity_to_every_case(monkeypatch, tmp_path):
    package = package_fixture(tmp_path)
    snapshot = expected_snapshot("a" * 64)
    monkeypatch.setattr(qualify, "inspect_model", lambda: snapshot)
    calls = []
    def run(package, cid, output, **kwargs):
        calls.append(kwargs)
        return {"status": "answered" if cid == "p01" else "abstained"}
    monkeypatch.setattr(qualify, "run_attempt", run)
    assert qualify.main(["--package", str(package), "--expected-manifest-sha256", qualify.sha(package/"manifest.json"),
                         "--stage", "preflight", "--output", str(tmp_path/"attempts")]) == 0
    assert len(calls) == 2
    assert all(c["model_digest"] == "a" * 64 and c["expected_identity"]["model_content"] == snapshot for c in calls)


def test_digest_changes_generation_identity_without_changing_package(tmp_path):
    package = package_fixture(tmp_path)
    a = identity(package, expected_snapshot("a" * 64))
    b = identity(package, expected_snapshot("b" * 64))
    assert a["generation_sha256"] != b["generation_sha256"] and a["package_sha256"] == b["package_sha256"]


@pytest.mark.parametrize("mismatch_check,expected_calls", [(1, 0), (3, 1)])
def test_worker_model_mismatch_stops_inference_and_retains_any_raw_result(monkeypatch, tmp_path, mismatch_check, expected_calls):
    from src.pilot import engine, launch
    from src.pilot._model_identity import ModelIdentityError
    package = package_fixture(tmp_path)
    cases = json.loads((package/"cases.json").read_text(encoding="utf-8"))
    for case in cases:
        case["query"] = "Synthetic model identity fixture"
    (package/"cases.json").write_text(json.dumps(cases), encoding="utf-8")
    manifest = json.loads((package/"manifest.json").read_text(encoding="utf-8"))
    manifest["sha256"]["cases.json"] = sha(package/"cases.json")
    (package/"manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path/"attempts"
    output.mkdir()
    calls, checks = [], []
    def verify(snapshot):
        checks.append(snapshot)
        if len(checks) >= mismatch_check:
            raise ModelIdentityError("Synthetic model changed")
    def backend(messages):
        calls.append(messages)
        return SimpleNamespace(content="Synthetic fixed output", tool_calls=[], response_metadata={}, usage_metadata={"input_tokens": 2, "output_tokens": 3})
    class Corpus:
        def __init__(self, path):
            self.sha, self.sources, self.context_sources = sha(path), {}, {}
    class Engine:
        def __init__(self, corpus, model=None, **kwargs):
            self.model = model
        def _model(self):
            return SimpleNamespace(bind_tools=lambda tools: SimpleNamespace(invoke=backend))
        def run(self, query, event):
            for _ in range(2):
                self.model.bind_tools([]).invoke([])
            return {"draft": {"claims": [{"text": "Synthetic fixture"}]}}
    monkeypatch.setattr(engine, "Corpus", Corpus)
    monkeypatch.setattr(engine, "PilotEngine", Engine)
    monkeypatch.setattr(launch, "configure_event_loop", lambda: None)
    monkeypatch.setattr(qualify.os, "environ", qualify.os.environ.copy())
    monkeypatch.setattr(qualify, "verify_model", verify)
    assert qualify.worker(package, "p01", output, sha(package/"manifest.json"), "a" * 64) == 1
    attempt = json.loads((output/"attempt-p01.json").read_text(encoding="utf-8"))
    assert attempt["status"] == "failed" and len(calls) == expected_calls
    assert len(attempt["captured_model_outputs"]) == expected_calls
    assert attempt["identity"]["model_content"] == expected_snapshot("a" * 64)


def test_parent_rejects_clean_process_result_with_another_identity(monkeypatch, tmp_path):
    package = package_fixture(tmp_path)
    output = tmp_path/"attempts"
    output.mkdir()
    expected = identity(package, expected_snapshot("a" * 64))
    def spawn(command, **kwargs):
        assert command[-2:] == ["--expected-model-digest", "a" * 64]
        (output/"attempt-p01.json").write_text(json.dumps({"status": "answered", "identity": {**expected, "generation_sha256": "other"}}), encoding="utf-8")
        return SimpleNamespace(pid=1234, wait=lambda **kwargs: 0)
    monkeypatch.setattr(subprocess, "Popen", spawn)
    result = run_attempt(package, "p01", output, model_digest="a" * 64, expected_identity=expected)
    assert result["process_returncode"] == 0 and result["status"] == "technical_failure"
    assert result["identity_verified"] is False
