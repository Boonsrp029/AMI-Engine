"""Offline contract check for multipassage support and competing records."""
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

from src.pilot._evidence import build_span_catalog


spec = spec_from_file_location("exact_decisions", Path(__file__).with_name("check-exact-fact-decisions.py"))
exact = module_from_spec(spec)
spec.loader.exec_module(exact)


def resolve_facts(decisions, requested, bindings, catalog, sources):
    if decisions.keys() != requested.keys():
        raise ValueError("Each requested fact must have a decision")
    result = {}
    for fact, (state, groups) in decisions.items():
        if state == "missing" and not groups:
            result[fact] = {"state": state, "alternatives": []}
            continue
        if ((state == "supported" and len(groups) != 1)
                or (state == "conflicting" and len(groups) < 2)
                or state not in {"supported", "conflicting"}
                or any(not group for group in groups)):
            raise ValueError("Invalid fact state or evidence groups")
        alternatives = []
        seen = set()
        for group in groups:
            extracts = []
            for decision in group:
                span_id = decision[0]
                if span_id in seen:
                    raise ValueError("Repeated direct span")
                seen.add(span_id)
                extracts.append(exact.resolve({fact: decision}, {fact: requested[fact]},
                                              bindings, catalog, sources)[fact])
            alternatives.append(extracts)
        if state == "conflicting":
            group_sources = [{item["direct"]["source_id"] for item in group} for group in alternatives]
            if sum(map(len, group_sources)) != len(set().union(*group_sources)):
                raise ValueError("Opposing records must retain distinct source identities")
        result[fact] = {"state": state, "alternatives": alternatives}
    return result


def main():
    texts = {
        "log": "The canal gate was open from April through June. The gate admitted vessels up to 42 metres long.",
        "district_a": "The inspected gate was 16 metres wide in 2022.",
        "district_b": "The inspected gate was 19 metres wide in 2022.",
    }
    sources = {sid: {"content": text} for sid, text in texts.items()}
    catalog = build_span_catalog(sources)

    def decision(source_id, literal):
        sid, span = next((sid, span) for sid, span in catalog.items()
                         if span["source_id"] == source_id and literal in span["text"])
        start = span["text"].index(literal)
        return (sid, start, start + len(literal), [])

    season = decision("log", "April through June")
    length = decision("log", "42 metres")
    first = decision("district_a", "16 metres")
    second = decision("district_b", "19 metres")
    requested = {"access": "r1", "width": "r2", "fees": "r3"}
    bindings = {"r1": {"log"}, "r2": {"district_a", "district_b"}, "r3": set()}
    decisions = {
        "access": ("supported", [[season, length]]),
        "width": ("conflicting", [[first], [second]]),
        "fees": ("missing", []),
    }
    result = resolve_facts(decisions, requested, bindings, catalog, sources)
    assert [x["answer"] for x in result["access"]["alternatives"][0]] == ["April through June", "42 metres"]
    assert [group[0]["answer"] for group in result["width"]["alternatives"]] == ["16 metres", "19 metres"]
    assert result["fees"] == {"state": "missing", "alternatives": []}
    negatives = [
        ("one conflict side", "width", ("conflicting", [[first]])),
        ("duplicate span", "width", ("conflicting", [[first], [first]])),
        ("unbound source", "access", ("supported", [[season, first]])),
        ("missing with evidence", "fees", ("missing", [[length]])),
        ("empty support group", "access", ("supported", [[]])),
        ("shared conflict source", "access", ("conflicting", [[season], [length]])),
    ]
    for label, fact, value in negatives:
        try:
            resolve_facts({**decisions, fact: value}, requested, bindings, catalog, sources)
        except ValueError:
            continue
        raise AssertionError(label)
    print(json.dumps({"resolved": result, "structural_rejections": [item[0] for item in negatives],
                      "checks_passed": 9, "model_calls": 0, "runtime_activated": False}, indent=2))


if __name__ == "__main__":
    main()
