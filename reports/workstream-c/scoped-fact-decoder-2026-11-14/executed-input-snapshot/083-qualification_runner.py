"""One authorized development attempt through A's owned process, never a batch loop.

This internal function trusts its operator to verify actual user authorization
before supplying the grant document. Default callers must not synthesize grants.
"""
import time
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from ..schemas import ResearchRequest
from ..store import Store
from .contracts import Plan
from ._scoped_activation import prepare_composer
from .retrieval import LocalBM25Adapter
from .runner import run_stored_plan
from .qualification import _write_once


@dataclass(frozen=True)
class CaptureResponse:
    output: str
    case_id: str

    def __call__(self, record):
        if record["stage"] not in {"mapping", "composition"}:
            raise ValueError("Unknown captured model stage")
        _write_once(Path(self.output) / (self.case_id + "." + record["stage"] + ".raw.json"), record)


@dataclass(frozen=True)
class LocalSafety:
    query: str
    model: str
    output: str
    case_id: str
    model_snapshot: dict | None = None

    def __call__(self, draft, sources):
        from src.utils.guardrails_runner import GuardrailsRunner
        from src.pilot._model_identity import verify_model
        if self.model_snapshot is not None:
            verify_model(self.model_snapshot)
        forced = {"AGENT_LLM_PROVIDER": "ollama", "AGENT_LLM_MODEL": self.model,
                  "OLLAMA_BASE_URL": "http://localhost:11434"}
        previous = {key: os.environ.get(key) for key in forced}
        try:
            os.environ.update(forced)
            result = GuardrailsRunner().validate_output(user_input=self.query,
                raw_report="\n".join(c["text"] for c in draft["claims"]),
                context="\n".join(source["content"] for source in sources.values()))
            _write_once(Path(self.output) / (self.case_id + ".safety.json"), result)
            if self.model_snapshot is not None:
                verify_model(self.model_snapshot)
            return result.get("passed_guardrails") is True
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


def execute_development(ledger, case_id, transport, safety, verify_identity):
    started = time.monotonic()
    ledger.start(case_id)  # No client/store creation before admission.
    row = None
    error = None
    try:
        frozen = ledger.contract["cases"][case_id]
        plan = Plan.model_validate_json(json.dumps(frozen["plan"]))
        verify_identity(ledger.contract["model_snapshot"])
        remaining = 180 - (time.monotonic() - started)
        if remaining <= 0:
            raise TimeoutError("Preparation exhausted attempt deadline")
        # The owned runner enforces its process deadline including safety. This
        # reduction reserves preparation time within the outer 180-second bound.
        plan = plan.model_copy(update={"deadline_seconds": min(plan.deadline_seconds, remaining)})
        store = Store(ledger.output / (case_id + ".sqlite3"))
        run_id, _ = store.create(ResearchRequest(query=plan.query, request_key="qualify-" + hashlib.sha256(case_id.encode()).hexdigest()[:32]), plan.corpus_sha256)
        try:
            run_stored_plan(store, run_id, plan, frozen["corpus_path"],
                LocalBM25Adapter(frozen["corpus_path"]),
                prepare_composer(ledger.contract, frozen, plan, transport,
                    CaptureResponse(str(ledger.output), case_id)), safety)
        finally:
            row = store.get(run_id)
        verify_identity(ledger.contract["model_snapshot"])
    except Exception as exc:
        error = type(exc).__name__  # Bounded failure classification, no secret-bearing text.
    metrics = row["metrics"] if row is not None else {}
    result = {"technical_pass": error is None and row is not None and row["status"] == "needs_review",
        "main_calls": metrics.get("model_calls", 0),
        "nemo_invocations": metrics.get("guardrail_invocations", 0),
        "elapsed_seconds": time.monotonic() - started,
        "failure_type": error, "stored_run": row,
        "internal_nemo_usage": "unavailable", "monetary_cost": "unmeasured",
        "source_assessment": "pending", "owner_adjudication": "pending"}
    ledger.finish(case_id, result)  # Retain failed result before closing allowance.
    _write_once(ledger.output / (case_id + ".review.json"), {
        "status": "assistant assessment and owner adjudication pending",
        "result_file": case_id + ".result.json", "draft": row["draft"],
        "sources": row["sources"], "diagnostics": metrics.get("composition_diagnostics"),
        "note": "Review raw composer, application fallback and final claims separately; no approval/export."})
    return result
