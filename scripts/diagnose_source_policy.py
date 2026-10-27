"""Explicitly authorized, once-only local source-policy diagnostic; never a workflow retry."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def identity(fixtures):
    paths = [Path(__file__), Path("src/utils/guardrails_runner.py"), Path("src/utils/_periods.py"), *Path("config/guardrails").glob("*")]
    return {"fixtures_sha256": sha(fixtures), "files": {p.as_posix(): sha(p) for p in paths if p.is_file()},
            "provider": "ollama", "model": "ami-llama3.1:8b-4k"}


def worker(case, output):
    from src.pilot.launch import configure_event_loop
    configure_event_loop()
    os.environ.update(AGENT_LLM_PROVIDER="ollama", LLM_PROVIDER="ollama", AGENT_LLM_MODEL="ami-llama3.1:8b-4k",
                      OLLAMA_MODEL="ami-llama3.1:8b-4k", OLLAMA_BASE_URL="http://localhost:11434",
                      NEMO_GUARDRAILS_NO_USAGE_STATS="1", LANGCHAIN_TRACING_V2="false", LANGSMITH_TRACING="false")
    from src.utils.guardrails_runner import GuardrailsRunner, strict_source_grounding
    from nemoguardrails.llm.types import Task
    started, responses = time.perf_counter(), []
    record = {"case_id": case["id"], "expected": case["expected_single_verdict"],
              "guard_invocations": 0, "internal_tokens": None, "owner_acceptance": "not assessed"}
    try:
        guard = GuardrailsRunner()
        def parse(value):
            responses.append(value)
            return strict_source_grounding(value)
        guard.rails.register_output_parser(parse, "strict_source_grounding")
        record["rendered_prompt"] = guard.rails.runtime.llm_task_manager.render_task_prompt(
            Task.SELF_CHECK_FACTS, context={"evidence": case["context"], "response": case["report"]})
        record["guard_invocations"] = 1
        checked = guard.validate_output(case["report"], case["context"], "Verify this synthetic market report")
        verdict = responses[0].strip().upper() if len(responses) == 1 else ""
        format_valid = verdict in {"YES", "YES.", "NO", "NO."}
        agrees = format_valid and verdict.rstrip(".") == case["expected_single_verdict"]
        # A bypass or a different policy block must not count as success.
        agrees = agrees and checked["passed_guardrails"] == (case["expected_single_verdict"] == "YES")
        record.update(status="assessed", contract_passed=agrees, verdict_format_valid=format_valid,
                      raw_judge_responses=responses, guard_result=checked)
    except Exception as exc:
        record.update(status="technical_failure", error_type=type(exc).__name__, raw_judge_responses=responses)
    record["elapsed_seconds"] = time.perf_counter() - started
    save(output, record)
    return 0 if record["status"] == "assessed" else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=Path("data/pilot/policy-diagnostic-2026-10-27.json"))
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if sha(args.fixtures) != args.expected_sha256:
        parser.error("Frozen policy fixtures changed")
    cases = json.loads(args.fixtures.read_text(encoding="utf-8"))["cases"]
    if len(cases) != 6 or len({c["id"] for c in cases}) != 6:
        parser.error("Exactly six unique frozen diagnostic cases required")
    if args.worker:
        case = next(c for c in cases if c["id"] == args.worker)
        if args.output.exists():
            parser.error("Worker result cannot overwrite an earlier check")
        return worker(case, args.output)
    args.output.mkdir(parents=True, exist_ok=False)
    starting = identity(args.fixtures)
    save(args.output / "identity.json", starting)
    summary = {"author": "assistant-authored policy diagnostic", "cases": [], "status": "running",
               "model_generation_calls": 0, "maximum_guard_invocations": 6, "automatic_retries": False,
               "internal_usage": "unavailable; provider-internal retries not fully measured"}
    for case in cases:
        cid = case["id"]
        if cid not in {"j01", "j02", "j03", "j04", "j05", "j06"}:
            raise ValueError("Unknown diagnostic identifier")
        save(args.output / f"started-{cid}.json", {"case_id": cid, "retries": 0})
        command = [sys.executable, "-m", "scripts.diagnose_source_policy", "--fixtures", str(args.fixtures),
                   "--expected-sha256", args.expected_sha256, "--worker", cid,
                   "--output", str(args.output / f"result-{cid}.json")]
        try:
            process = subprocess.run(command, capture_output=True, timeout=60)
            status = "completed" if process.returncode == 0 else "technical_failure"
            stdout, stderr, code = process.stdout, process.stderr, process.returncode
        except subprocess.TimeoutExpired as exc:
            status, stdout, stderr, code = "timeout", exc.stdout or b"", exc.stderr or b"", None
        (args.output / f"stdout-{cid}.txt").write_bytes(stdout)
        (args.output / f"stderr-{cid}.txt").write_bytes(stderr)
        row = {"case_id": cid, "process_status": status, "returncode": code}
        result = args.output / f"result-{cid}.json"
        if result.exists():
            observed = json.loads(result.read_text(encoding="utf-8"))
            row.update(contract_passed=observed.get("contract_passed", False), result_sha256=sha(result))
        else:
            row["inflight_usage_unknown"] = True
        summary["cases"].append(row)
        save(args.output / "summary.json", summary)
        if status != "completed" or identity(args.fixtures) != starting:
            summary["status"] = "technical_gate_failed; remaining checks stopped"
            break
    else:
        summary["status"] = "passed" if all(c.get("contract_passed") for c in summary["cases"]) else "policy_gate_failed; responses retained"
    summary["unattempted"] = [c["id"] for c in cases if c["id"] not in {r["case_id"] for r in summary["cases"]}]
    save(args.output / "summary.json", summary)
    print(json.dumps(summary))
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
