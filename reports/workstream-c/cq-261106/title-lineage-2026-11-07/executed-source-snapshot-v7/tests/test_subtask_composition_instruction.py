"""Fixed-response instruction wiring and evidence boundaries, not model quality."""
import time

import pytest
from test_subtask_generation import FixedTransport, fixture

from src.pilot._evidence import COMPOSITION_INSTRUCTION
from src.pilot.subtasks._composition_instruction import (
    CONCURRENT_COMPOSITION_INSTRUCTION, CONCURRENT_COMPOSITION_VERSION,
)
from src.pilot.subtasks.generation import ConcurrentComposer
from src.pilot.subtasks.runner import ModelAccess


class RecordingTransport(FixedTransport):
    def __init__(self, mode="complete"):
        super().__init__()
        self.mode = mode
        self.requests = {}

    def __call__(self, stage, schema, instruction, inputs):
        self.requests[stage] = (schema, instruction, inputs)
        response = super().__call__(stage, schema, instruction, inputs)
        if stage == "composition":
            if self.mode == "omit":
                response["parsed"]["claims"] = []
            elif self.mode == "paraphrase":
                response["parsed"]["claims"][0]["text"] = (
                    "Observed electricity demand increased 7.3% in 2014.")
            elif self.mode == "invalid":
                response["parsed"]["claims"][0]["text"] = (
                    "Observed electricity demand increased 42.8% in 2022.")
        return response


def run(tmp_path, mode):
    plan, report = fixture(tmp_path)
    transport = RecordingTransport(mode)
    access = ModelAccess(time.monotonic()+30)
    result = ConcurrentComposer(plan, {"r1": ("s01",)}, "2026-11-06", transport)(report, access)
    return result, transport, access


def test_private_instruction_wired_without_changing_sequential_prompt(tmp_path):
    from src.pilot.engine import DRAFT_INSTRUCTION
    result, transport, access = run(tmp_path, "complete")
    assert DRAFT_INSTRUCTION == COMPOSITION_INSTRUCTION
    assert transport.requests["composition"][1] == CONCURRENT_COMPOSITION_INSTRUCTION
    assert transport.requests["composition"][1] != DRAFT_INSTRUCTION
    assert result.diagnostics["concurrent_composition_version"] == CONCURRENT_COMPOSITION_VERSION
    assert access.calls == 2 and access.guards == 0 and not result.safety_passed
    unit = transport.requests["composition"][2]["units"][0]
    assert unit["evidence"][0]["quote"] == "Observed electricity demand grew 7.3% in 2014."
    assert unit["source_literal_cues"]["percentage_literals"] == ["7.3%"]
    assert result.draft["claims"][0]["source_ids"] == ["observed"]


def test_prose_is_not_replaced_by_extract_selection(tmp_path):
    result, _, _ = run(tmp_path, "paraphrase")
    assert result.draft["claims"][0]["text"] == "Observed electricity demand increased 7.3% in 2014."
    assert result.diagnostics["fallback_unit_ids"] == []
    assert result.diagnostics["editorial_correction"] is False


def test_omission_fallback_remains_separate_from_raw_composer(tmp_path):
    result, _, access = run(tmp_path, "omit")
    assert result.diagnostics["raw_composer_output"]["claims"] == ()
    assert result.diagnostics["fallback_unit_ids"] == ["u1"]
    assert "7.3%" in result.draft["claims"][0]["text"]
    assert access.calls == 2 and not result.safety_passed


def test_invalid_nonempty_prose_is_not_silently_repaired(tmp_path):
    plan, report = fixture(tmp_path)
    transport = RecordingTransport("invalid")
    access = ModelAccess(time.monotonic()+30)
    with pytest.raises(ValueError, match="numeric value absent"):
        ConcurrentComposer(plan, {"r1": ("s01",)}, "2026-11-06", transport)(report, access)
    assert transport.stages == ["mapping", "composition"]
    assert access.calls == 2 and access.guards == 0
