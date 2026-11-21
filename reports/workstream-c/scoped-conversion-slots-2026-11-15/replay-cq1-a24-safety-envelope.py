"""Reconstruct the stopped qualification case with no actual model calls."""
import hashlib
import json
from pathlib import Path
import socket
import sys
from tempfile import TemporaryDirectory
import time
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from src.pilot.subtasks._handoff import prepare
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.qualification_runner import LocalSafety
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess, validate_citations
from src.pilot.subtasks.scheduler import run_plan
from src.utils.guardrails_runner import GuardrailsRunner, RailStatus


def read(path):
    return json.loads(path.read_bytes())


def blocked(*args, **kwargs):
    raise AssertionError("Offline replay cannot open a socket")


def main():
    socket.socket.connect = socket.create_connection = blocked
    contract = read(ROOT / "qualification-contract.json")
    assert all(digest(name) == expected for name, expected in contract["input_sha256"].items())
    cid = "cq1-a24"
    case = contract["cases"][cid]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    source = ROOT / "actual-cq1"
    saved = {stage: (source / f"{cid}.{stage}.raw.json") for stage in ("mapping", "composition")}
    historic = read(source / f"{cid}.safety.json")
    identity = read(saved["mapping"])["identity"]
    report = run_plan(plan, identity["run_id"], identity["attempt_id"], LocalBM25Adapter(case["corpus_path"]))

    def fixed(stage, schema, instruction, inputs):
        raw = read(saved[stage])["raw"]
        return {"raw": raw, "parsed": schema.model_validate_json(raw).model_dump()}

    synthesis = prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
    draft, lineage = prepare(synthesis, report)
    sources = {entry.source.source_id: entry.source.model_dump() for entry in report.sources}
    draft = validate_citations(draft, sources)
    observed = {}

    class MockRails:
        def check(self, *, messages, rail_types):
            observed.update(messages=messages, rail_types=[str(rail) for rail in rail_types])
            return SimpleNamespace(status=RailStatus.BLOCKED, content="", rail="mocked block")

    runner = object.__new__(GuardrailsRunner)
    runner.rails = MockRails()
    with TemporaryDirectory(prefix="cq1-a24-safety-replay-") as staging:
        with patch("src.utils.guardrails_runner.GuardrailsRunner", return_value=runner):
            assert LocalSafety(plan.query, contract["model_snapshot"]["model"], staging, "offline")(draft, sources) is False
    messages = observed["messages"]
    context = messages[0]["content"]["relevant_chunks"]
    claim = messages[2]["content"]
    exact = "Other gases includes blast furnace gas and other manufactured and waste gases derived from fossil fuels."
    matched, = [sid for sid, item in sources.items() if exact in item["content"]]
    assert claim == historic["raw_output"] and matched in draft["claims"][0]["source_ids"]
    assert exact in context and "manufactured and waste gases" not in claim
    context_hash = hashlib.sha256(context.encode()).hexdigest()
    print(json.dumps({"actual_model_calls": 0, "sockets_blocked": True, "mocked_rail_verdict": "blocked",
                      "historic_rail": historic["blocking_rail"], "historic_reason_available": False,
                      "reconstructed_claim": claim, "identical_to_historic_raw_report": True,
                      "exact_source_member_statement": exact, "omitted_member_group": "other manufactured and waste gases derived from fossil fuels",
                      "source_id": matched, "envelope": {"evidence_chars": len(context), "evidence_sha256": context_hash,
                      "ordered_sources": list(sources), "direct_statement_present": True,
                      "check_facts": messages[0]["content"]["check_facts"]},
                      "fallback_used": bool(synthesis.diagnostics["fallback_unit_ids"]),
                      "retained_capture_sha256": {stage: digest(path) for stage, path in saved.items()}}, indent=2))


if __name__ == "__main__":
    main()
