"""Compare the archived parser and repaired fixed-response path without inference."""
import json
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
PREVIOUS = ROOT.parent / "scoped-table-boundary-development-2026-11-18"
sys.path.insert(0, str(PROJECT))
from scripts._llama_token_count import encoding
from src.pilot.subtasks._request_focus import _table_focus
from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


def read(path):
    return json.loads(path.read_bytes())


def blocked(*args, **kwargs):
    raise AssertionError("Offline replay cannot open sockets")


def main():
    socket.socket.connect = socket.create_connection = blocked
    archive = PREVIOUS / "executed-input-snapshot"
    index = read(archive / "manifest.json")
    assert all(digest(archive / item["file"]) == item["sha256"] for item in index["files"].values())
    item = index["files"][str(PROJECT / "src/pilot/subtasks/_request_focus.py")]
    old_module = {"__name__": "src.pilot.subtasks._request_focus_archived", "__package__": "src.pilot.subtasks"}
    exec(compile((archive / item["file"]).read_text(encoding="utf-8"), item["file"], "exec"), old_module)
    contract = read(PREVIOUS / "qualification-contract.json")
    counter = encoding(read(Path(contract["tokenizer_path"])))
    assert digest(contract["tokenizer_path"]) == contract["tokenizer_sha256"]
    cases = {}
    for cid, label, amount, share in (("cq1-a38", "Other sources", "10", "0.2%"),
                                      ("cq1-a37", "Other gases", "11", "0.3%")):
        case = contract["cases"][cid]
        plan = Plan.model_validate_json(json.dumps(case["plan"]))
        assert digest(case["corpus_path"]) == plan.corpus_sha256
        source = next(row for row in read(Path(case["corpus_path"])) if row["feed_id"] == "eia-generation-2023")
        previous_focus = old_module["_table_focus"](plan.query, source["clean_content"])
        current_focus = _table_focus(plan.query, source["clean_content"])
        assert len(current_focus) == 1 and current_focus[0]["label"] == label
        if cid == "cq1-a38":
            assert previous_focus == []
        report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
        stages = {}

        def fixed(stage, schema, instruction, inputs):
            reserved = len(counter.encode(instruction)) + len(counter.encode(
                json.dumps(inputs, ensure_ascii=False, separators=(",", ":")))) + 1156
            assert reserved <= 4096
            raw = read(PREVIOUS / "actual-cq1" / f"{cid}.{stage}.raw.json")["raw"]
            try:
                schema.model_validate_json(raw)
                old_valid = True
            except ValueError:
                old_valid = False
            stages[stage] = {"reserved_tokens": reserved, "retained_response_schema_valid": old_valid}
            if stage == "mapping":
                focus = inputs["request_focus"]["r1"]
                value = json.loads(raw)
                value["facts"][0]["alternatives"] = [[{"span_id": focus["span_id"], "context": []}]]
                stages[stage]["focus"] = focus
            else:
                value = {"title": "Analyst research brief", "claims": [{"component_id": "r1", "unit_id": "u1"}]}
            return {"parsed": schema.model_validate_json(json.dumps(value)).model_dump()}

        result = prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
        expected = (f"In 2023, the table gives {label} generation in Billion kWh as {amount} and its share "
                    f"of total utility-scale electricity generation as {share}.")
        assert result.draft["claims"] == [{"text": expected, "source_ids": ["eia-generation-2023"]}]
        assert not result.diagnostics["fallback_unit_ids"] and not result.diagnostics["editorial_correction"]
        cases[cid] = {"archived_focus": previous_focus, "repaired_focus": current_focus,
                      "stages": stages, "draft": result.draft}
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0, "nemo_invocations": 0,
                      "archived_input_files_verified": index["file_count"], "cases": cases}, indent=2))


if __name__ == "__main__":
    main()
