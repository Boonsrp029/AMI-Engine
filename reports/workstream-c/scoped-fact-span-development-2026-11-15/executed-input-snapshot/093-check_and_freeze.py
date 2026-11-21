"""Freeze the offline-verified whole-span development protocol."""
import hashlib
import json
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from scripts._llama_token_count import encoding
from src.pilot.subtasks._development_lineage import canonical, canonical_hash, runtime_inputs
from src.pilot.subtasks._fact_selection import SPAN_WIRE_VERSION
from src.pilot.subtasks._scoped_activation import SPAN_FACT_CONTRACT_VERSION, prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


class Captured(Exception):
    pass


def blocked(*args, **kwargs):
    raise AssertionError("Network disabled")


def inspect_case(contract, case, counter, fixture=None):
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    if digest(case["corpus_path"]) != plan.corpus_sha256:
        raise ValueError("Corpus identity changed")
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    stages = {}

    def fixed(stage, schema, instruction, inputs):
        reserved = len(counter.encode(instruction)) + len(counter.encode(
            json.dumps(inputs, ensure_ascii=False, separators=(",", ":")))) + 1156
        if reserved > 4096:
            raise ValueError("Request exceeds context budget")
        stages[stage] = {"reserved": reserved,
                         "format_schema_tokens": len(counter.encode(json.dumps(schema.model_json_schema())))}
        if fixture is None:
            assert stage == "mapping"
            raise Captured
        if stage == "mapping":
            spans = {span["span_id"]: span["text"] for source in inputs["evidence"] for span in source["spans"]}
            focus = inputs.get("request_focus", {}).get("r1")
            sid = focus["span_id"] if focus else next(sid for sid, text in spans.items()
                if text == "Eventually, automated meters could periodically report electricity use to the utility.")
            context = [] if focus else [next(sid for sid, text in spans.items()
                if text.startswith("In the past, electricity meters were mechanical"))]
            value = {"wire_version": SPAN_WIRE_VERSION,
                     "facts": [{"fact_id": fact["fact_id"], "state": "supported",
                                "alternatives": [[{"span_id": sid, "context": context}]]}
                               for fact in inputs["facts"]],
                     "geography": {"status": "unresolved", "value": "", "evidence": [],
                                   "reason": "No independently selected geographical span."}}
        else:
            unit, = inputs["units"]
            claim = {name: unit[name] for name in ("component_id", "unit_id")}
            if fixture == "cq1-a20":
                assert len(unit["selected_facts"]) == 2
                assert all("source_literal_answer" not in fact for fact in unit["selected_facts"])
                claim["text"] = ("Earlier automated electricity meters could periodically report "
                                 "electricity use to the utility.")
            else:
                assert unit["response_kind"] == "table_row"
            value = {"title": "Analyst research brief", "claims": [claim]}
        return {"parsed": schema.model_validate(value).model_dump()}

    callback = prepare_composer(contract, case, plan, fixed, None)
    try:
        result = callback(report, ModelAccess(time.monotonic() + 30))
    except Captured:
        return stages
    assert fixture and len(result.draft["claims"]) == 1 and not result.diagnostics["fallback_unit_ids"]
    return {"requests": stages, "fixture_draft": result.draft}


def main():
    socket.socket.connect = socket.create_connection = blocked
    prior = ROOT.parent / "scoped-fact-selection-development-2026-11-14"
    decoder = ROOT.parent / "scoped-fact-decoder-2026-11-14"
    pool = ROOT.parent / "cq1-fact-selection-pool-2026-11-14"
    original = read(prior / "development-contract.json")
    tokenizer = Path(original["tokenizer_path"])
    assert digest(tokenizer) == original["tokenizer_sha256"]
    counter = encoding(read(tokenizer))
    contract = {**original, "composition_contract": SPAN_FACT_CONTRACT_VERSION, "as_of": "2026-11-15",
                "mapping_version": SPAN_WIRE_VERSION, "output_directory": str(ROOT / "actual-development-v1"),
                "authorization_reply": "Authorize scoped whole-span development diagnostics",
                "purpose": "Validate whole-span fact selection, capability wording and biomass row selection."}
    dev = {cid: inspect_case(contract, case, counter, fixture=cid) for cid, case in contract["cases"].items()}
    manifest, plans, scopes = (pool / path for path in ("pool/manifest.json",
        "pool/plans-v3-explicit-coverage.json", "question-scopes/manifest.json"))
    audit = read(pool / "freeze-audit.json")
    assert [digest(path) for path in (manifest, plans, scopes)] == [
        audit["pool_sha256"], audit["plans_sha256"], audit["scope_manifest_sha256"]]
    scope_entries = read(scopes)["cases"]
    roster = {}
    for cid, entry in read(plans).items():
        item = scope_entries[cid]
        path = scopes.parent / item["path"]
        case = {**entry, "corpus_path": str(plans.parent / Path(entry["corpus_path"]).name),
                "requested_scopes": str(path), "requested_scopes_sha256": item["sha256"]}
        roster[cid] = inspect_case({**contract, "input_sha256": {str(path): item["sha256"]}}, case, counter)
    assert len(roster) == 20
    offline = ROOT / "offline-request-check.json"
    write(offline, {"model_calls": 0, "sockets_blocked": True, "development_fixed_responses": dev,
                    "roster_mapper_only": roster, "reservation_limit": 4096})
    runner = ROOT / "run_case.py"
    runner.write_text((prior / "run_case.py").read_text(encoding="utf-8").replace(
        original["composition_contract"], SPAN_FACT_CONTRACT_VERSION), encoding="utf-8")
    protocol = ROOT / "source-review-protocol.md"
    runtime = runtime_inputs()
    paths = [Path(__file__), runner, protocol, offline, tokenizer, manifest, plans, scopes,
             decoder / "batch-summary.json", prior / "batch-summary.json",
             ROOT.parents[2] / "tests/test_scoped_fact_selection.py"]
    for case in contract["cases"].values():
        paths.extend(Path(case[name]) for name in ("corpus_path", "requested_scopes"))
    contract.update(source_review_protocol=str(protocol), source_review_protocol_sha256=digest(protocol),
                    input_sha256={**runtime, **{str(path): digest(path) for path in paths}})
    identity = {key: contract[key] for key in ("model_snapshot", "settings", "composition_contract")}
    contract["pipeline_identity"] = hashlib.sha256(canonical({**identity, "runtime_inputs": runtime}).encode()).hexdigest()
    contract["contract_sha256"] = canonical_hash(contract)
    write(ROOT / "development-contract.json", contract)
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "pins": len(contract["input_sha256"]),
                      "development_max": max(row["reserved"] for case in dev.values() for row in case["requests"].values()),
                      "roster_mapper_max": max(row["mapping"]["reserved"] for row in roster.values())}))


if __name__ == "__main__":
    main()
