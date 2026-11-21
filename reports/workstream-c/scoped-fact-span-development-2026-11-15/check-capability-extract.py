"""Exercise a proposed capability extract through the existing offline projector."""
import json
from pathlib import Path
import re
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from src.pilot.subtasks._scoped_activation import prepare_composer
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import ModelAccess
from src.pilot.subtasks.scheduler import run_plan


_HISTORICAL = re.compile(r"^(?:earlier|eventually|previously|formerly|in the past),?\s+", re.I)
_DEPENDENT = re.compile(r"^(?:these|those|such|it|they|the former|the latter)\b", re.I)


def capability_extract(unit):
    """Offer only a complete single-sentence capability from a direct passage."""
    if len(unit["evidence"]) != 1 or not unit.get("selected_facts") or unit.get("response_kind"):
        return None
    quote = unit["evidence"][0]["quote"]
    prefix = _HISTORICAL.match(quote)
    if not prefix or not re.fullmatch(r"[^.!?;\r\n]+\.", quote):
        return None
    statement = quote[prefix.end():]
    if _DEPENDENT.match(statement) or not re.match(r"^[\w -]+\s+could\s+\w+", statement, re.I):
        return None
    return quote


def blocked(*args, **kwargs):
    raise AssertionError("Offline replay cannot open a socket")


def main():
    socket.socket.connect = socket.create_connection = blocked
    contract = json.loads((ROOT / "development-contract.json").read_bytes())
    case = contract["cases"]["cq1-a20"]
    plan = Plan.model_validate_json(json.dumps(case["plan"]))
    assert digest(case["corpus_path"]) == plan.corpus_sha256
    report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(case["corpus_path"]))
    raw_dir = ROOT / "actual-development-v1"
    mapper_path = raw_dir / "cq1-a20.mapping.raw.json"
    composer_path = raw_dir / "cq1-a20.composition.raw.json"
    mapper = json.loads(mapper_path.read_bytes())["raw"]
    observed_composer = json.loads(json.loads(composer_path.read_bytes())["raw"])
    extract_trace = {}

    def fixed(stage, schema, instruction, inputs):
        if stage == "mapping":
            return {"raw": mapper, "parsed": schema.model_validate_json(mapper).model_dump()}
        unit, = inputs["units"]
        text = capability_extract(unit)
        assert text is not None
        selection = {key: unit[key] for key in ("unit_id", "component_id")}
        extract_trace.update(selection=selection, source_id=unit["evidence"][0]["source_id"], text=text)
        # Emulate the application's rendering step after a fixed ID selection.
        rendered = {"title": observed_composer["title"], "claims": [{**selection, "text": text}]}
        return {"parsed": schema.model_validate(rendered).model_dump()}

    result = prepare_composer(contract, case, plan, fixed, None)(report, ModelAccess(time.monotonic() + 30))
    assert result.draft["claims"] == [{"text": extract_trace["text"], "source_ids": [extract_trace["source_id"]]}]
    assert "could periodically report" in extract_trace["text"]
    assert not result.diagnostics["fallback_unit_ids"]
    assert not result.diagnostics["editorial_correction"]
    assert all("Utility companies measure" not in claim["text"] for claim in result.draft["claims"])

    def unit(*quotes):
        return {"evidence": [{"quote": quote} for quote in quotes], "selected_facts": [{"fact_id": "test"}]}

    positives = [
        "Previously, harbor transmitters could send cargo manifests weekly.",
        "Formerly, district gates could not admit vessels after dusk.",
    ]
    negatives = [
        "Harbor transmitters could send cargo manifests weekly.",
        "Previously, these transmitters could send cargo manifests weekly.",
        "Previously, harbor transmitters could send cargo manifests. Modern systems operate continuously.",
        "Previously, if visibility improved, operators could send the report.",
    ]
    for text in positives:
        assert capability_extract(unit(text)) == text
    for text in negatives:
        assert capability_extract(unit(text)) is None
    assert capability_extract(unit(*positives)) is None
    assert capability_extract({**unit(positives[0]), "response_kind": "table_row"}) is None
    print(json.dumps({"sockets_blocked": True, "actual_model_calls": 0, "runtime_changed": False,
        "mapper_capture_sha256": digest(mapper_path), "composer_capture_sha256": digest(composer_path),
        "original_raw_composition": observed_composer, "simulated_selection": extract_trace,
        "offline_projected_draft": result.draft, "synthetic_eligibility_checks": 8,
        "source_relevance_proven_by_eligibility": False}, indent=2))


if __name__ == "__main__":
    main()
