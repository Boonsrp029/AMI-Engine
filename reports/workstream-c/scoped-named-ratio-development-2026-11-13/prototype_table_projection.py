"""Offline design proof using the closed batch's exact table-row selection."""
import hashlib
import json
from pathlib import Path
import socket

from src.pilot._composition import composition_units
from src.pilot._evidence import build_span_catalog
from src.pilot._source_selection import resolve_source_selection
from src.pilot.subtasks._disclosures import DisclosureScopes, validate_report, validate_scopes
from src.pilot.subtasks._request_focus import focused_text, request_focus
from src.pilot.subtasks._scoped_generation import application_selection, scoped_schema
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.generation import selection_schema
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.synthesis import project_report
from src.pilot._requests import requested_components


def blocked(*args, **kwargs):
    raise AssertionError("Network disabled in offline projection")


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    socket.socket.connect = blocked
    socket.create_connection = blocked
    root = Path(__file__).resolve().parent
    contract = read(root / "development-contract.json")
    assert all(digest(Path(path)) == expected for path, expected in contract["input_sha256"].items())
    case = contract["cases"]["cq-focus02"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    scopes = DisclosureScopes.model_validate_json(Path(case["requested_scopes"]).read_bytes())
    bindings = case["bindings"]
    validate_scopes(plan, bindings, scopes)
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    validate_report(plan, report)
    sources = {item.source.source_id: item.source.model_dump() for item in report.sources}
    catalog = build_span_catalog(sources)
    focuses = request_focus(requested_components(plan.query), catalog, report, bindings)
    output = Path(contract["output_directory"])
    raw_record = read(output / "cq-focus02.mapping.raw.json")
    raw = json.loads(raw_record["raw"])
    schema = scoped_schema(selection_schema(catalog, plan.query, report=report,
                           requirements=case["complete_required_branches"], requested_geography_only=True), focuses)
    candidate = application_selection(schema.model_validate(raw).model_dump(), plan.query)
    mapping, _ = resolve_source_selection(candidate, catalog, plan.query, sources, contract["as_of"])
    unit, = composition_units(mapping)
    component, = mapping.components
    focus = focuses[unit["component_id"]]
    assert focus["kind"] == "table_row" and component.status == "supported"
    span = catalog[focus["span_id"]]
    assert unit["evidence"] == [{"source_id": span["source_id"], "quote": span["text"]}]
    claim = {"component_id": unit["component_id"], "unit_id": unit["unit_id"], "text": focused_text(focus)}
    # Feed separately authored deterministic text through normal projection checks.
    result = project_report(plan, report, mapping.model_dump(exclude={"geography_resolution"}),
                            {"title": "Analyst research brief", "claims": [claim]}, bindings,
                            as_of=contract["as_of"], is_current=lambda: True, disclosure_scopes=scopes,
                            geographic_resolution=mapping.geography_resolution.model_dump())
    assert result.draft["claims"] == [{"text": claim["text"], "source_ids": [span["source_id"]]}]
    assert result.diagnostics["fallback_unit_ids"] == [] and not result.safety_passed
    assert result.provenance[0]["origins"][0]["source_id"] == span["source_id"]
    assert result.provenance[0]["origins"][0]["subtask_id"] == "s01"
    assert read(output / "cq-focus02.result.json")["technical_pass"] is False
    evidence = {
        "status": "offline prototype, safety pending, no persisted revision",
        "retained_failure_sha256": digest(output / "cq-focus02.result.json"),
        "raw_mapper_selection": raw,
        "historical_raw_composer_output": json.loads(read(output / "cq-focus02.composition.raw.json")["raw"]),
        "prototype_raw_composer_output": None,
        "application_rendered_claim": claim,
        "focus": focus,
        "selected_span": span,
        "draft": result.draft,
        "claim_provenance": result.provenance,
        "fallback_unit_ids": [],
        "editorial_correction": False,
        "actual_model_calls": 0,
        "actual_nemo_calls": 0,
    }
    with (root / "offline-table-projection-prototype.json").open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"draft": result.draft, "main_calls": 0, "nemo_calls": 0}))


if __name__ == "__main__":
    main()
