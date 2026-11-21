"""Offline candidate for literal actual-cost requests with a single explicit year."""
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent
SPEC = spec_from_file_location("baseline", ROOT / "check-fact-selection-baseline.py")
baseline = module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)

MEASURE = r"[a-z]+(?: [a-z]+){0,3}"
YEAR = r"(?:19|20)\d{2}"
PAIR = re.compile(rf"What were the (?P<first>{MEASURE}) and (?P<second>{MEASURE}) costs in (?P<year>{YEAR})\?", re.I)
SINGLE = re.compile(rf"What was the (?P<measure>{MEASURE}) cost in (?P<year>{YEAR})\??", re.I)
ACTUAL = re.compile(rf"(?P<measure>{MEASURE}) cost \d+(?:,\d{{3}})*(?:\.\d+)? "
                    rf"(?:baht|euros|dollars) in (?P<year>{YEAR})\.", re.I)


def candidate(question, texts):
    """Return candidates for the recognized literal shape only."""
    pair = PAIR.fullmatch(question)
    if pair:
        slots = [(pair[key], pair["year"]) for key in ("first", "second")]
    else:
        singles = [SINGLE.fullmatch(slot["question_anchor"])
                   for slot in baseline.requested_components(question)]
        if not singles or not all(singles):
            return None
        slots = [(slot["measure"], slot["year"]) for slot in singles]
    if len(set(slots)) != len(slots):
        return None
    facts = {sid: ACTUAL.fullmatch(text) for sid, text in texts.items()}
    return [{"measure": measure, "year": year,
             "candidates": [sid for sid, fact in facts.items() if fact
                            and fact["measure"].casefold() == measure.casefold() and fact["year"] == year]}
            for measure, year in slots]


def main():
    predictions = {cid: candidate(*inputs) for cid, inputs in baseline.CASES.items()}
    labels = json.loads((ROOT / "fact-selection-labels.json").read_bytes())
    assert predictions["reporting"] is None and predictions["conflict"] is None
    for cid in ("costs", "partial"):
        slots = predictions[cid]
        assert len(slots) == labels[cid]["requested_facts"]
        assert {sid for slot in slots for sid in slot["candidates"]} == set(labels[cid]["direct"])
        assert sum(not slot["candidates"] for slot in slots) == len(labels[cid]["unresolved"])

    question = "What were the delivery and storage costs in 2022?"
    result = candidate(question, {
        "delivery": "Delivery cost 65 euros in 2022.",
        "storage_a": "Storage cost 40 euros in 2022.",
        "storage_b": "Storage cost 48 euros in 2022.",
        "prior": "Storage cost 32 euros in 2021.",
        "projection": "Storage could cost 55 euros in 2022.",
        "definition": "Storage cost is the price of a storage service.",
    })
    assert [slot["candidates"] for slot in result] == [["delivery"], ["storage_a", "storage_b"]]
    assert candidate("What were the delivery and storage costs in 2021 and 2022?", {}) is None
    assert candidate("What were the delivery and delivery costs in 2022?", {}) is None
    print(json.dumps({"baseline_fixture_predictions": predictions, "new_fixture": result,
                      "boundary_checks": ["both opposing values retained", "prior year excluded",
                          "capability excluded", "definition excluded", "multi-year declined",
                          "duplicate slot declined"],
                      "runtime_activated": False, "model_calls": 0}, indent=2))


if __name__ == "__main__":
    main()
