"""Check v10 against saved member selections and mocked final safety."""
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
    packet = read(ROOT / "development-contract.json")
    case = packet["cases"]["cq1-a24"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    capture = {stage: ROOT / "actual-development-v1" / f"cq1-a24.{stage}.raw.json"
               for stage in ("mapping", "composition")}
    assert {k: digest(p) for k, p in capture.items()} == read(ROOT / "actual-failure-replay.json")["capture_sha256"]
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))

    def fixed(stage, schema, instruction, inputs):
        raw = read(capture[stage])["raw"]
        if stage == "composition":
            assert "The application supplies the category sentence." in instruction
        return {"raw": raw, "parsed": schema.model_validate_json(raw).model_dump()}

    result = prepare_composer(packet, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
    draft, lineage = prepare(result, report)
    sources = {row.source.source_id: row.source.model_dump() for row in report.sources}
    draft = validate_citations(draft, sources)
    assert len(draft["claims"]) == 1
    claim, = draft["claims"]
    assert claim == {"text": "The other gases category includes blast furnace gas and other manufactured "
                            "and waste gases derived from fossil fuels.", "source_ids": ["eia-generation-2023"]}
    selection = json.loads(read(capture["composition"])["raw"])
    assert json.loads(json.dumps(result.diagnostics["raw_composer_output"])) == selection
    recorded, = result.diagnostics["application_rendered_memberships"]
    source = sources[recorded["source_id"]]["content"]
    exact = "Other gases includes blast furnace gas and other manufactured and waste gases derived from fossil fuels."
    assert exact in source[recorded["start"]:recorded["end"]] and recorded["text"] == claim["text"]
    assert not result.diagnostics["fallback_unit_ids"] and not result.diagnostics["editorial_correction"]

    class MockRails:
        def __init__(self, status):
            self.status = status

        def check(self, *, messages, rail_types):
            assert exact in messages[0]["content"]["relevant_chunks"]
            assert messages[2]["content"] == claim["text"]
            return SimpleNamespace(status=self.status, content=(claim["text"] if self.status == RailStatus.PASSED else ""),
                                   rail=None if self.status == RailStatus.PASSED else "mock check")

    with TemporaryDirectory(prefix="cq1-membership-v10-") as staging:
        for status, expected in ((RailStatus.PASSED, True), (RailStatus.BLOCKED, False)):
            runner = object.__new__(GuardrailsRunner)
            runner.rails = MockRails(status)
            with patch("src.utils.guardrails_runner.GuardrailsRunner", return_value=runner):
                assert LocalSafety(plan.query, packet["model_snapshot"]["model"], staging, status.name)(draft, sources) is expected

    print(json.dumps({"actual_model_calls": 0, "sockets_blocked": True, "draft_persisted": False,
                      "mocked_safety_outcomes": ["accepted", "blocked"], "raw_composer": selection,
                      "application_rendering": recorded, "projected_claim": claim}, indent=2))


if __name__ == "__main__":
    main()
