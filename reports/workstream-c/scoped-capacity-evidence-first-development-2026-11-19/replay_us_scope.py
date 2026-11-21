"""Replay the two consumed CQ1 table selections with fixed responses."""
import hashlib
import json
from pathlib import Path
import socket
import time

from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_bytes())


def block(*args, **kwargs):
    raise AssertionError("Network unavailable in offline replay")


def main():
    socket.socket.connect = socket.socket.connect_ex = socket.create_connection = block
    contract = read(ROOT / "qualification-contract.json")
    stored = {}
    for cid in ("cq1-a41", "cq1-a42"):
        f = contract["cases"][cid]
        plan = Plan.model_validate_json(json.dumps(f["plan"]))
        report = run_plan(plan, "a"*32, "b"*32, LocalBM25Adapter(f["corpus_path"]))

        def fixed(stage, schema, instruction, inputs):
            raw = read(ROOT / "actual-cq1" / f"{cid}.{stage}.raw.json")["raw"]
            return {"parsed": schema.model_validate_json(raw).model_dump()}

        out = prepare_composer(contract, f, plan, fixed, None)(report, ModelAccess(time.monotonic()+30))
        trace, = out.diagnostics["application_rendered_table_rows"]
        scope = trace["geographic_evidence"]
        source = next(entry.source for entry in report.sources if entry.source.source_id == scope["source_id"])
        assert hashlib.sha256(source.content.encode()).hexdigest() == scope["content_sha256"]
        assert source.content[scope["start"]:scope["end"]] == scope["text"]
        assert "U.S." in trace["text"] and not out.diagnostics["fallback_unit_ids"]
        stored[cid] = {"draft": out.draft, "table_trace": trace}
    with (ROOT / "us-scope-offline-replay.json").open("x", encoding="utf-8") as stream:
        json.dump({"sockets_blocked":True, "model_calls":0, "retained_cases":stored}, stream, indent=2)


if __name__ == "__main__":
    main()
