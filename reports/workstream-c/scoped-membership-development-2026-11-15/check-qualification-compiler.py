"""Exercise compilation and run admission in an isolated offline fixture."""
import json
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
import sys

ROOT = Path(__file__).resolve().parent
POOL = ROOT.parent / "cq1-membership-pool-2026-11-15"
SHARED = ROOT.parent / "cq1-fact-span-pool-2026-11-15"
sys.path.insert(0, str(SHARED))

from build_qualification import build, canonical_hash, digest, Plan
from run_qualification_case import inspect


ROOT = Path(__file__).resolve().parent


def write(path, value):
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def blocked(*args, **kwargs):
    raise AssertionError("Network disabled")


def main():
    socket.socket.connect = socket.create_connection = blocked
    audit = json.loads((POOL / "freeze-audit.json").read_bytes())
    development = ROOT / "development-contract.json"
    original = json.loads(development.read_bytes())
    assert original["contract_sha256"] == canonical_hash(original)
    with TemporaryDirectory(prefix="cq1-compiler-fixture-") as directory:
        root = Path(directory)
        attempts = root / "synthetic-development"
        attempts.mkdir()
        source = root / "synthetic-contract.json"
        fixture = {**original, "output_directory": str(attempts)}
        fixture["contract_sha256"] = canonical_hash(fixture)
        write(source, fixture)
        for index, cid in enumerate(fixture["case_ids"]):
            plan = Plan.model_validate_json(json.dumps(fixture["cases"][cid]["plan"]))
            run, attempt = str(index + 1) * 32, str(index + 3) * 32
            identity = {"run_id": run, "attempt_id": attempt, "plan_id": plan.plan_id,
                        "corpus_sha256": plan.corpus_sha256}
            result = attempts / f"{cid}.result.json"
            write(result, {"technical_pass": True, "failure_type": None,
                "main_calls": 0, "nemo_invocations": 0, "elapsed_seconds": 0,
                "stored_run": {"id": run, "status": "needs_review",
                    "query": plan.query, "corpus_sha": plan.corpus_sha256,
                    "metrics": {"attempt_id": attempt, "model_calls": 0, "guardrail_invocations": 0},
                    "draft": {"title": "Synthetic fixture", "claims": [], "warnings": []},
                    "events": [
                        {"kind": "attempt_started", "payload": {"attempt_id": attempt}},
                        {"kind": "subtask_plan", "payload": {"identity": identity, "plan": plan.model_dump(mode="json")}},
                    ]}})
            write(attempts / f"{cid}.started.json", {"case_id": cid, "contract_sha256": fixture["contract_sha256"]})
            write(attempts / f"{cid}.assessment.json", {"verdict": "pass", "result_sha256": digest(result),
                "source_findings": ["Synthetic fixture for compiler verification only."]})

        def compile_fixture():
            return build(source, fixture["contract_sha256"], POOL / "pool",
                root / "qualification-contract.json", root / "actual-cq1", original["as_of"],
                expected_pool_sha256=audit["pool_sha256"], expected_plans_sha256=audit["plans_sha256"],
                scope_manifest_path=POOL / "question-scopes/manifest.json",
                expected_scopes_sha256=audit["scope_manifest_sha256"],
                recorded_pool_root=ROOT.parent / "concurrent-qualification-2026-11-06/cq1",
                review_protocol=SHARED / "source-review-protocol.md")

        stopped = attempts / "stopped.json"
        write(stopped, {"reason": "Synthetic failed-gate check"})
        try:
            compile_fixture()
        except ValueError as error:
            assert str(error) == "Failed development batch cannot qualify"
        else:
            raise AssertionError("Compiler accepted a stopped fixture")
        stopped.unlink()
        contract = compile_fixture()
        observed = inspect(root, contract["contract_sha256"])
        assert observed["case_ids"] == contract["case_ids"] and len(observed["case_ids"]) == 20
        assert observed["execution_authorized"] is False
        assert not (root / "actual-cq1").exists() and not (ROOT / "qualification-contract.json").exists()
    print(json.dumps({"synthetic_only": True, "sockets_blocked": True, "model_calls": 0,
        "compiler_rejected_stopped_fixture": True, "runner_verified_cases": 20,
        "actual_contract_created": False, "authorization_created": False}, indent=2))


if __name__ == "__main__":
    main()



