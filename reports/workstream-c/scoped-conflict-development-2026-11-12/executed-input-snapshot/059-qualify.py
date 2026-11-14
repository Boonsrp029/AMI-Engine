"""Frozen local release diagnostics with a per-case subprocess deadline.

Default mode verifies inputs only. No Ragas, approval, export or hosted inference.
The older paired comparison CLI remains unchanged.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
import uuid
from types import SimpleNamespace
from src.pilot._model_identity import expected_snapshot, inspect_model, verify_model


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    temporary = path.with_name("." + path.name + "." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for attempt, delay in enumerate((0, 0.02, 0.1, 0.3)):
        if delay:
            time.sleep(delay)
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 3:
                raise  # Keep the previous report and the pending snapshot intact.


def load_package(package, expected_manifest=None):
    package = Path(package).resolve()
    manifest = read(package/"manifest.json")
    if expected_manifest is not None and sha(package/"manifest.json") != expected_manifest:
        raise ValueError("Manifest differs from the declared frozen identity")
    for name, expected in manifest["sha256"].items():
        path = (package/name).resolve()
        if not path.is_relative_to(package) or sha(path) != expected:
            raise ValueError("Frozen package integrity failed")
    for source in read(package/"sources.json").values():
        path = (package.parent/source["file"]).resolve()
        if not path.is_relative_to(package.parent) or sha(path) != source["sha256"]:
            raise ValueError("Pinned source file integrity failed")
    cases = read(package/"cases.json")
    if len({c["case_id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate case IDs")
    for split, field in (("heldout", "heldout_count"), ("preflight", "preflight_count")):
        if sum(c["split"] == split for c in cases) != manifest[field]:
            raise ValueError("Frozen case counts disagree with manifest")
    for case in cases:
        if not case["case_id"].replace("-", "").isalnum():
            raise ValueError("Invalid case ID")
        path = (package/"corpora"/(case["corpus"] + ".json")).resolve()
        if not path.is_relative_to(package) or not path.is_file():
            raise ValueError("Case corpus must be a pinned JSON file")
        if path.relative_to(package).as_posix() not in manifest["sha256"]:
            raise ValueError("Case corpus is not in the frozen manifest")
    return package, manifest, cases


def identity(package, model_snapshot=None):
    paths = [*Path("src/pilot").glob("*.py"), Path("src/agents/local_retriever.py"),
             Path("src/utils/env.py"), Path("src/utils/guardrails_runner.py"), Path("src/utils/_periods.py"),
             *Path("config/guardrails").glob("*"), Path("config/pilot_search_profile.json")]
    hashes = {p.as_posix(): sha(p) for p in paths if p.is_file()}
    generation = {"code_and_policy": hashes, "provider": "ollama", "model": "ami-llama3.1:8b-4k",
                  "context": 4096, "completion": 900, "temperature": 0, "python": platform.python_version(),
                  "model_content": model_snapshot}
    return {**generation, "generation_sha256": hashlib.sha256(json.dumps(generation, sort_keys=True).encode()).hexdigest(),
            "package_sha256": sha(Path(package)/"manifest.json"), "internal_guard_usage": "not fully measured"}


def worker(package, case_id, output, expected_manifest, model_digest=None):
    # Set the proven Windows startup policy before importing any model clients.
    from src.pilot.launch import configure_event_loop
    configure_event_loop()
    package, manifest, cases = load_package(package, expected_manifest)
    model_snapshot = expected_snapshot(model_digest) if model_digest is not None else None
    starting_identity = identity(package, model_snapshot)
    case = next(c for c in cases if c["case_id"] == case_id)
    os.environ.update(AGENT_LLM_PROVIDER="ollama", LLM_PROVIDER="ollama", AGENT_LLM_MODEL="ami-llama3.1:8b-4k",
                      OLLAMA_MODEL="ami-llama3.1:8b-4k", OLLAMA_BASE_URL="http://localhost:11434",
                      NEMO_GUARDRAILS_NO_USAGE_STATS="1", LANGCHAIN_TRACING_V2="false", LANGSMITH_TRACING="false",
                      HF_HUB_DISABLE_TELEMETRY="1")
    from src.pilot.engine import Corpus, PilotEngine
    from src.utils.guardrails_runner import GuardrailsRunner, strict_source_grounding
    captured, events = [], []
    started = time.perf_counter()
    output = Path(output)

    def persist():
        write(output/f"progress-{case_id}.json", {"case_id": case_id, "events": events, "captured_model_outputs": captured,
              "retrieved_sources": retrieved_sources(),
              "elapsed_seconds": time.perf_counter()-started})

    def event(kind, payload):
        events.append({"kind": kind, "payload": payload})
        persist()

    corpus = Corpus(package/"corpora"/(case["corpus"] + ".json"))
    if corpus.sha != manifest["sha256"][f"corpora/{case['corpus']}.json"]:
        raise ValueError("Corpus changed after package verification")
    def retrieved_sources():
        ids = {sid for e in events if e["kind"] in {"tool_result", "reporting_context"} for sid in e["payload"]["source_ids"]}
        return {sid: corpus.sources.get(sid, corpus.context_sources.get(sid)) for sid in ids}
    baseline = PilotEngine(corpus)._model()

    class CapturingModel:
        def wrap(self, client, stage):
            def invoke(messages):
                if model_snapshot is not None:
                    verify_model(model_snapshot)
                result = client.invoke(messages)
                raw = result.get("raw") if isinstance(result, dict) else result
                parsed = result.get("parsed") if isinstance(result, dict) else None
                captured.append({"stage": stage, "content": getattr(raw, "content", None),
                    "tool_calls": getattr(raw, "tool_calls", None), "usage": getattr(raw, "usage_metadata", None),
                    "finish": {k: v for k, v in (getattr(raw, "response_metadata", {}) or {}).items()
                               if k in {"done_reason", "finish_reason", "model", "prompt_eval_count", "eval_count"}},
                    "parsing_error_type": type(result["parsing_error"]).__name__ if isinstance(result, dict) and result.get("parsing_error") else None,
                    "parsed": parsed.model_dump() if hasattr(parsed, "model_dump") else parsed})
                persist()
                if model_snapshot is not None:
                    verify_model(model_snapshot)
                return result
            return SimpleNamespace(invoke=invoke)

        def bind_tools(self, tools):
            return self.wrap(baseline.bind_tools(tools), "tool")

        def with_structured_output(self, schema, **kwargs):
            return self.wrap(baseline.with_structured_output(schema, **kwargs), "structured")

    class CapturingGuard:
        def validate_output(self, **kwargs):
            if model_snapshot is not None:
                verify_model(model_snapshot)
            guard = GuardrailsRunner()
            def parse(value):
                event("guard_judge_response", {"text": value, "internal_usage": None})
                return strict_source_grounding(value)
            guard.rails.register_output_parser(parse, "strict_source_grounding")
            result = guard.validate_output(**kwargs)
            if model_snapshot is not None:
                verify_model(model_snapshot)
            return result

    try:
        if model_snapshot is not None:
            verify_model(model_snapshot)
        result = PilotEngine(corpus, model=CapturingModel(), guardrails=CapturingGuard()).run(case["query"], event)
        record = {"case_id": case_id, "query": case["query"], "status": "answered" if result["draft"]["claims"] else "abstained",
                  "result": result}
    except Exception as exc:
        # Raw model responses are retained separately; never copy provider error bodies.
        record = {"case_id": case_id, "query": case["query"], "status": "failed", "error_type": type(exc).__name__,
                  "os_errno": getattr(exc, "errno", None), "os_winerror": getattr(exc, "winerror", None),
                  "error_locations": [{"file": f.filename, "line": f.lineno, "function": f.name}
                                      for f in traceback.extract_tb(exc.__traceback__)]}
    record.update(events=events, captured_model_outputs=captured, elapsed_seconds=time.perf_counter()-started,
                  retrieved_sources=retrieved_sources(), owner_acceptance="pending; no human rating or approval",
                  identity=starting_identity)
    try:
        load_package(package, expected_manifest)
        unchanged = identity(package, model_snapshot) == starting_identity
        if model_snapshot is not None:
            verify_model(model_snapshot)
    except (OSError, ValueError, RuntimeError):
        unchanged = False
    if not unchanged:
        record.update(status="failed", error_type="InputIdentityChanged")
    write(output/f"attempt-{case_id}.json", record)
    return 0 if record["status"] != "failed" else 1


def run_attempt(package, case_id, output, timeout=180, *, model_digest=None, expected_identity=None):
    if not 0 < timeout <= 180:
        raise ValueError("Attempt deadline must not exceed the accepted 180 seconds")
    marker = output/f"started-{case_id}.json"
    if marker.exists() or (output/f"attempt-{case_id}.json").exists():
        raise ValueError("A frozen attempt cannot be retried or overwritten")
    write(marker, {"case_id": case_id, "deadline_seconds": timeout, "maximum_main_calls": 4, "maximum_guard_invocations": 1})
    with (output/f"stdout-{case_id}.txt").open("wb") as stdout, (output/f"stderr-{case_id}.txt").open("wb") as stderr:
        command = [sys.executable, "-m", "src.pilot.qualify", "--package", str(package),
                                   "--expected-manifest-sha256", sha(package/"manifest.json"),
                                   "--output", str(output), "--worker", case_id]
        if model_digest is not None:
            command += ["--expected-model-digest", model_digest]
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        write(output/f"process-{case_id}.json", {"pid": process.pid, "case_id": case_id, "live_handle_required": True})
        timed_out = False
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            code = process.wait()
    attempt = output/f"attempt-{case_id}.json"
    completed = read(attempt) if attempt.exists() else None
    result = {"case_id": case_id, "process_returncode": code, "timed_out": timed_out,
              "status": completed["status"] if code == 0 and completed and completed["status"] in {"answered", "abstained"} else "technical_failure",
              "attempt_sha256": sha(attempt) if attempt.exists() else None,
              "inflight_usage_unknown": timed_out or not completed}
    if expected_identity is not None:
        result["identity_verified"] = bool(completed and completed.get("identity") == expected_identity)
        if not result["identity_verified"]:
            result["status"] = "technical_failure"
    write(output/f"process-result-{case_id}.json", result)
    return result


def verify_preflights(path, current_identity):
    snapshot = current_identity.get("model_content")
    if not snapshot or snapshot != expected_snapshot(snapshot.get("digest")):
        raise ValueError("Pinned local model identity required for release preflights")
    assessment = read(path)
    if assessment.get("status") != "passed" or assessment.get("author") != "assistant-authored preflight assessment":
        raise ValueError("Passed, explicitly authored preflight assessment required")
    if any(assessment.get(k) != current_identity[k] for k in ("generation_sha256", "package_sha256")):
        raise ValueError("Preflight assessment is for a different generator or package")
    if set(assessment.get("cases", {})) != {"p01", "p02"}:
        raise ValueError("Both preflights must be assessed")
    for cid, evidence in assessment["cases"].items():
        attempt = Path(evidence["attempt"])
        if evidence.get("verdict") != "passed" or sha(attempt) != evidence["sha256"]:
            raise ValueError("Preflight evidence changed or was not accepted")
        result = read(attempt)
        if result.get("identity") != current_identity:
            raise ValueError("Preflight attempt has a different generator, model or package identity")
        process_path = attempt.with_name(f"process-result-{cid}.json")
        if not process_path.is_file() or evidence.get("process_result_sha256") != sha(process_path):
            raise ValueError("Preflight process evidence changed or is missing")
        process = read(process_path)
        expected = "answered" if cid == "p01" else "abstained"
        if (result["case_id"] != cid or result["status"] != expected or process.get("case_id") != cid
                or process.get("status") != expected or process.get("process_returncode") != 0
                or process.get("timed_out") is not False or process.get("attempt_sha256") != sha(attempt)
                or process.get("identity_verified") is not True):
            raise ValueError("Preflight attempt failed")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--stage", choices=("verify", "preflight", "heldout"), default="verify")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preflight-assessment", type=Path)
    parser.add_argument("--expected-manifest-sha256")
    parser.add_argument("--expected-model-digest", help="Optional predeclared digest; generation also pins current local metadata")
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        if args.output is None:
            parser.error("Worker output directory required")
        return worker(args.package, args.worker, args.output, args.expected_manifest_sha256, args.expected_model_digest)
    package, manifest, cases = load_package(args.package, args.expected_manifest_sha256)
    current_identity = identity(package)
    if args.stage == "verify":
        print(json.dumps({"status": "verified; no generation", "manifest": sha(package/"manifest.json"),
                          "heldout": manifest["heldout_count"], "preflights": manifest["preflight_count"]}))
        return 0
    if args.output is None or args.output.exists():
        parser.error("Provide a new output directory; do not overwrite an earlier batch")
    if args.expected_manifest_sha256 is None:
        parser.error("Generation requires the declared frozen manifest SHA-256")
    model_snapshot = inspect_model()
    if args.expected_model_digest is not None and expected_snapshot(args.expected_model_digest) != model_snapshot:
        parser.error("Local model differs from the predeclared digest")
    current_identity = identity(package, model_snapshot)
    if args.stage == "heldout":
        if args.preflight_assessment is None:
            parser.error("Held-out execution requires the passed preflight assessment")
        verify_preflights(args.preflight_assessment, current_identity)
    selected = [c for c in cases if c["split"] == args.stage]
    args.output.mkdir(parents=True)
    write(args.output/"identity.json", current_identity)
    summary = {"stage": args.stage, "selected_ids": [c["case_id"] for c in selected], "attempts": [],
               "status": "running", "model_quality": "unassessed", "automatic_retries": False}
    for case in selected:
        result = run_attempt(package, case["case_id"], args.output,
                             model_digest=model_snapshot["digest"], expected_identity=current_identity)
        summary["attempts"].append(result)
        if result["status"] == "technical_failure":
            summary["status"] = "technical_gate_failed; generation stopped"
            write(args.output/"summary.json", summary)
            return 1
        write(args.output/"summary.json", summary)
    summary["status"] = "attempts retained; source/quality assessment pending"
    write(args.output/"summary.json", summary)
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
