"""Replay saved source evidence and exercise the v9 membership response contract offline."""
import json
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from pydantic import ValidationError
from scripts._llama_token_count import encoding
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


def read(path):
    return json.loads(path.read_bytes())


def blocked(*args, **kwargs):
    raise AssertionError("Offline replay cannot open a socket")


def main():
    socket.socket.connect = socket.create_connection = blocked
    contract = read(ROOT / "qualification-contract.json")
    case = contract["cases"]["cq1-a24"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    tokenizer = Path(contract["tokenizer_path"])
    assert digest(tokenizer) == contract["tokenizer_sha256"]
    counter = encoding(read(tokenizer))
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    raw_dir = ROOT / "actual-cq1"
    capture = {stage: raw_dir / f"cq1-a24.{stage}.raw.json" for stage in ("mapping", "composition")}
    saved = {stage: json.loads(read(path)["raw"]) for stage, path in capture.items()}
    reservations = {}
    submitted = {}

    def fixed(stage, schema, instruction, inputs):
        reserved = len(counter.encode(instruction)) + len(counter.encode(
            json.dumps(inputs, ensure_ascii=False, separators=(",", ":")))) + 1156
        assert reserved <= 4096
        reservations[stage] = {"reserved": reserved, "format_schema_tokens":
                               len(counter.encode(json.dumps(schema.model_json_schema())))}
        value = saved[stage]
        if stage == "composition":
            assert inputs["units"][0]["required_membership"]["targets"] == {
                "target_1": "blast furnace gas", "target_2": "other manufactured and waste gases derived from fossil fuels"}
            try:
                schema.model_validate_json(json.dumps(value))
            except ValidationError:
                pass
            else:
                raise AssertionError("Old incomplete response passed v9")
            ids = {key: value["claims"][0][key] for key in ("unit_id", "component_id")}
            target_1 = "The other gases category includes blast furnace gas."
            value = {"title": value["title"], "claims": [{**ids, "targets": {
                "target_1": target_1, "target_2": "The other gases category includes other manufactured and waste gases derived from fossil fuels."}}]}
            submitted.update(value)
        return {"raw": json.dumps(value), "parsed": schema.model_validate_json(json.dumps(value)).model_dump()}

    result = prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
    assert json.dumps(result.diagnostics["raw_composer_output"], sort_keys=True) == json.dumps(submitted, sort_keys=True)
    assert not result.diagnostics["fallback_unit_ids"] and not result.diagnostics["editorial_correction"]
    assert result.draft["claims"] == [{"text": "The other gases category includes blast furnace gas. "
                                     "The other gases category includes other manufactured and waste gases derived from fossil fuels.", "source_ids": ["eia-generation-2023"]}]
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0, "saved_partial_rejected": True,
                      "capture_sha256": {k: digest(v) for k, v in capture.items()}, "requests": reservations,
                      "fixed_raw_composer": submitted, "fixed_projection": result.draft}, indent=2))


if __name__ == "__main__":
    main()

