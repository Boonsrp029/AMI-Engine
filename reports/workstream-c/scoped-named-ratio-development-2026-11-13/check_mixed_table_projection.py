"""Offline boundary check for the proposed mixed table and model contract."""
import hashlib
import json
from pathlib import Path
import socket

from pydantic import ValidationError

from src.pilot._composition import canonical_units, payload, response_schema
from src.pilot._evidence import EvidenceMap
from src.pilot.subtasks._request_focus import _table_focus, focused_text
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.synthesis import project_report


def blocked(*args, **kwargs):
    raise AssertionError("Network disabled in the offline boundary check")


def main():
    socket.socket.connect = blocked
    socket.create_connection = blocked
    root = Path(__file__).resolve().parent
    table = (
        "Utility-scale electricity generation in 2018\nEnergy source\nBillion kWh\nShare of total\n"
        "Wind\n62\n12.2%\nHydropower\n119\n23.3%\nBiomass\n35\n6.9%"
    )
    note = "The 2018 generation figures are provisional."
    rows = [{"feed_id": "generation", "clean_content": table}, {"feed_id": "status", "clean_content": note}]
    corpus = root / "mixed-table-synthetic-corpus.json"
    corpus_bytes = json.dumps(rows, indent=2).encode()
    if corpus.exists():
        assert corpus.read_bytes() == corpus_bytes
    else:
        with corpus.open("xb") as stream:
            stream.write(corpus_bytes)
    anchor = "What were hydropower generation and its share of utility-scale generation in 2018"
    status_anchor = "were the figures provisional or final?"
    plan = Plan(query=f"{anchor}, and {status_anchor}", corpus_sha256=hashlib.sha256(corpus_bytes).hexdigest(),
                subtasks=(Subtask(subtask_id="s01", operation="retrieve", query="hydropower"),
                          Subtask(subtask_id="s02", operation="retrieve", query="provisional")))
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(corpus))
    focus, = _table_focus(anchor, table)
    mapping = EvidenceMap(components=[
        dict(component_id="r1", question_anchor=anchor, status="supported",
             short_answer=focused_text(focus), evidence=[dict(source_id="generation", quote=table)]),
        dict(component_id="r2", question_anchor=status_anchor, status="supported",
             short_answer=note, evidence=[dict(source_id="status", quote=note)]),
    ])
    owned, model = canonical_units(mapping, {})
    excluded = (owned["unit_id"],)
    inputs = payload(mapping, "2026-11-13", excluded_units=excluded, question=plan.query)
    assert [unit["unit_id"] for unit in inputs["units"]] == [model["unit_id"]]
    schema = response_schema(mapping, excluded_units=excluded)
    rendered = dict(component_id="r1", unit_id=owned["unit_id"], text=focused_text(focus))
    raw_claim = dict(component_id="r2", unit_id=model["unit_id"], text=note)
    raw = {"title": "Analyst research brief", "claims": [raw_claim]}
    schema.model_validate(raw)
    rejected = []
    for label, claims in {
        "application-owned ID": [rendered],
        "duplicate ID": [raw_claim, raw_claim],
        "wrong component": [{**raw_claim, "component_id": "r1"}],
        "unknown ID": [{**raw_claim, "unit_id": "u9"}],
    }.items():
        try:
            schema.model_validate({**raw, "claims": claims})
        except ValidationError:
            rejected.append(label)
        else:
            raise AssertionError(f"Expected rejection for {label}")
    merged = {**raw, "claims": [rendered, raw_claim]}
    result = project_report(plan, report, mapping.model_dump(), merged, {"r1": ["s01"], "r2": ["s02"]},
                            as_of="2026-11-13", is_current=lambda: True)
    assert [claim["source_ids"] for claim in result.draft["claims"]] == [["generation"], ["status"]]
    assert result.diagnostics["fallback_unit_ids"] == [] and not result.safety_passed
    assert [record["origins"][0]["unit_id"] for record in result.provenance] == ["u1", "u2"]
    proof = {"status": "offline projection, safety pending", "model_input_units": [model["unit_id"]],
             "rejected_raw_claims": rejected, "synthetic_raw_composer_output": raw,
             "application_rendered_claim": rendered, "draft": result.draft,
             "claim_provenance": result.provenance, "actual_model_calls": 0, "actual_nemo_calls": 0}
    with (root / "offline-mixed-table-projection.json").open("x", encoding="utf-8") as stream:
        json.dump(proof, stream, indent=2)
    print(json.dumps({"validated_claims": 2, "rejected_variants": rejected, "actual_model_calls": 0}))


if __name__ == "__main__":
    main()
