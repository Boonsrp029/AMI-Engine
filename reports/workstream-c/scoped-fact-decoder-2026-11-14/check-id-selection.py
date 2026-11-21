"""Offline ID-only schema prototype over the existing exact source spans."""
from collections import defaultdict
import json
from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import Field, create_model

from src.pilot._evidence import _resolve_span, build_span_catalog
from src.pilot.schemas import StrictModel


def selection_schema(eligible, catalog):
    by_source = defaultdict(list)
    for span_id in eligible:
        by_source[catalog[span_id]["source_id"]].append(span_id)
    choices = []
    for index, ids in enumerate(by_source.values()):
        span_type = Literal[tuple(ids)]
        # Share a source-local ID set between direct and context fields.
        choices.append(create_model(f"SourceSelection{index}", __base__=StrictModel,
            direct=(span_type, ...), context=(list[span_type], Field(max_length=2))))
    if not choices:
        return create_model("MissingFact", __base__=StrictModel,
            state=(Literal["missing"], ...), groups=(tuple[()], ...))
    group = Annotated[list[Union[tuple(choices)]], Field(min_length=1, max_length=5)]
    supported = create_model("SupportedFact", __base__=StrictModel,
        state=(Literal["supported"], ...), groups=(list[group], Field(min_length=1, max_length=1)))
    missing = create_model("MissingFact", __base__=StrictModel,
        state=(Literal["missing"], ...), groups=(tuple[()], ...))
    conflict = create_model("ConflictingFact", __base__=StrictModel,
        state=(Literal["conflicting"], ...), groups=(list[group], Field(min_length=2, max_length=3)))
    return create_model("FactSelection", __base__=StrictModel, decision=(Union[supported, missing, conflict], ...))


def resolve(raw, schema, catalog, sources):
    parsed = schema.model_validate_json(json.dumps(raw)).model_dump()
    value = parsed.get("decision", parsed)
    groups = []
    seen = set()
    for group in value["groups"]:
        items = []
        for item in group:
            direct, contexts = item["direct"], item["context"]
            if direct in seen or len({direct, *contexts}) != 1 + len(contexts):
                raise ValueError("Duplicate direct or context role")
            seen.add(direct)
            quote = _resolve_span(direct, catalog, sources)
            context = [_resolve_span(sid, catalog, sources) for sid in contexts]
            if any(record["source_id"] != quote["source_id"] for record in context):
                raise ValueError("Context leaves the direct source record")
            items.append({**quote, "context": context,
                          "source_offsets": [catalog[direct]["start"], catalog[direct]["end"]]})
        groups.append(items)
    if value["state"] == "conflicting":
        records = [{item["source_id"] for item in group} for group in groups]
        if sum(map(len, records)) != len(set().union(*records)):
            raise ValueError("Conflict alternatives reuse a source record")
    return {"state": value["state"], "groups": groups}


def main():
    root = Path(__file__).resolve().parent
    previous = json.loads((root / "actual-mapper/service/service-result.json").read_bytes())
    evidence = json.loads((root.parent / "scoped-fact-selection-development-2026-11-14"
                          / "actual-development-v1/cq1-a20.result.json").read_bytes())["stored_run"]["sources"]
    catalog = build_span_catalog(evidence)
    allowed = [sid for sid, span in catalog.items() if span["source_id"] == "eia-measurement"]
    meter_schema = selection_schema(allowed, catalog)
    raw = json.loads(previous["content"])
    fixture_raw = {"decision": {"state": "supported", "groups": [[
        {"direct": item["span_id"], "context": item["context"]} for item in raw["facts"][0]["alternatives"][0]
    ]]}}
    try:
        resolve(fixture_raw, meter_schema, catalog, evidence)
    except ValueError:
        pass
    else:
        raise AssertionError("Free-text context must be rejected by the schema")

    sources = {
        "county": {"content": "The old sluice could release water weekly. The equipment was used in winter."},
        "vendor": {"content": "The sluice could release water monthly."},
    }
    spans = build_span_catalog(sources)
    county, context, vendor = spans
    schema = selection_schema(list(spans), spans)

    def build(state, *groups):
        return {"decision": {"state": state, "groups": list(groups)}}

    first = {"direct": county, "context": [context]}
    second = {"direct": vendor, "context": []}
    assert resolve(build("supported", [first]), schema, spans, sources)["groups"][0][0]["quote"].endswith("weekly.")
    assert resolve(build("missing"), schema, spans, sources)["groups"] == []
    assert len(resolve(build("conflicting", [first], [second]), schema, spans, sources)["groups"]) == 2
    invalid = {
        "cross-record context": build("supported", [{**first, "context": [vendor]}]),
        "direct repeated as context": build("supported", [{**first, "context": [county]}]),
        "unknown direct ID": build("supported", [{**first, "direct": "unknown"}]),
        "empty support": build("supported"),
        "one conflict side": build("conflicting", [first]),
    }
    for name, value in invalid.items():
        try:
            resolve(value, schema, spans, sources)
        except ValueError:
            continue
        raise AssertionError(name)
    print(json.dumps({"actual_model_calls": 0, "runtime_activated": False, "checks": 9,
        "saved_context_rejected": True, "negative_checks": list(invalid),
        "granularity": "complete application-generated source spans; no model-calculated offsets",
        "direct_relevance_verified": False}, indent=2))


if __name__ == "__main__":
    main()
