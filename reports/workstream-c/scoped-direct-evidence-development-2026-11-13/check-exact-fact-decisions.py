"""Offline proof of a fact decision with source-literal answer offsets."""
import json
from pathlib import Path

from src.pilot._evidence import _resolve_span, build_span_catalog


def resolve(decisions, requested, bindings, catalog, sources):
    """Validate decisions and return direct extracts with separate context."""
    if decisions.keys() != requested.keys():
        raise ValueError("Each fact requires one decision")
    resolved = {}
    for fact, decision in decisions.items():
        if decision is None:
            resolved[fact] = None
            continue
        direct, start, end, context = decision
        ids = [direct, *context]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate evidence role")
        quotes = [_resolve_span(sid, catalog, sources) for sid in ids]
        source_id = quotes[0]["source_id"]
        if source_id not in bindings[requested[fact]] or any(q["source_id"] != source_id for q in quotes):
            raise ValueError("Evidence leaves the bound source record")
        text = quotes[0]["quote"]
        if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text) or not text[start:end].strip():
            raise ValueError("Invalid answer offsets")
        resolved[fact] = {"answer": text[start:end], "direct": quotes[0], "context": quotes[1:]}
    return resolved


def main():
    root = Path(__file__).resolve().parent
    result = json.loads((root / "actual-development-v1/cq1-a20.result.json").read_bytes())["stored_run"]
    sources = result["sources"]
    catalog = build_span_catalog(sources)
    direct = "s_6af27ac482a98ade"
    text = catalog[direct]["text"]
    context, = [sid for sid, span in catalog.items()
                if span["source_id"] == "eia-measurement" and span["start"] == 1315]
    requested = {"reported_item": "r1", "recipient": "r2"}
    bindings = {component: {"eia-measurement"} for component in requested.values()}

    def decision(literal):
        start = text.index(literal)
        return (direct, start, start + len(literal), [context])

    selected = {"reported_item": decision("electricity use"), "recipient": decision("the utility")}
    output = resolve(selected, requested, bindings, catalog, sources)
    assert output["reported_item"]["answer"] == "electricity use"
    assert output["recipient"]["answer"] == "the utility"
    assert "could periodically report" in output["recipient"]["direct"]["quote"]
    assert "mechanical devices" in output["recipient"]["context"][0]["quote"]
    assert resolve({**selected, "recipient": None}, requested, bindings, catalog, sources)["recipient"] is None

    wrong_source = {**bindings, "r2": {"another-source"}}
    corrupted_catalog = {**catalog, direct: {**catalog[direct], "text": text + " Altered."}}
    bad = [
        ("missing decision", {"reported_item": selected["reported_item"]}, bindings, catalog),
        ("unbound record", selected, wrong_source, catalog),
        ("changed source span", selected, bindings, corrupted_catalog),
        ("out of bounds", {**selected, "recipient": (direct, 0, len(text) + 1, [])}, bindings, catalog),
        ("duplicate role", {**selected, "recipient": (direct, 0, 5, [direct])}, bindings, catalog),
    ]
    for label, decisions, scope, spans in bad:
        try:
            resolve(decisions, requested, scope, spans, sources)
        except ValueError:
            continue
        raise AssertionError(label)

    # Offsets alone cannot prove that a phrase answers the assigned fact.
    swapped = resolve({**selected, "recipient": decision("electricity use")}, requested, bindings, catalog, sources)
    assert swapped["recipient"]["answer"] == "electricity use"
    print(json.dumps({"model_calls": 0, "runtime_activated": False, "example": output,
                      "structural_rejections": [case[0] for case in bad],
                      "explicit_unresolved_preserved": True,
                      "wrong_role_passed_structure": swapped["recipient"]["answer"]}, indent=2))


if __name__ == "__main__":
    main()
