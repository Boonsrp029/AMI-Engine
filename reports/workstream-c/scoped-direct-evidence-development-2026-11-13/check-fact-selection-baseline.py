"""Measure current request splitting and span hints against separate labels."""
import json
from pathlib import Path
from types import SimpleNamespace as Record

from src.pilot._requests import requested_components
from src.pilot.subtasks._request_focus import relevance_hints


CASES = {
    "costs": ("What were the installation and annual maintenance costs in 2021?", {
        "setup": "Installation cost 24,000 baht in 2021.",
        "service": "Annual maintenance cost 3,500 baht in 2021.",
        "future": "The 2023 forecast put annual maintenance costs at 4,000 baht.",
    }),
    "reporting": ("What did harbor transmitters report weekly, and who received those reports?", {
        "history": "Earlier harbor transmitters had an automated mode.",
        "direct": "In automated mode, harbor transmitters could report berth vacancies weekly to the port clerk.",
        "background": "The port office logged vessel arrivals.",
    }),
    "partial": ("What was the annual maintenance cost in 2021, and what was the repair cost in 2021?", {
        "service": "Annual maintenance cost 3,500 baht in 2021.",
        "future": "The forecast put the repair cost in 2023 at 7,000 baht.",
    }),
    "conflict": ("What did the two records report for reservoir capacity in 2020?", {
        "first": "Reservoir capacity was 120 million cubic metres in 2020.",
        "second": "Reservoir capacity was 140 million cubic metres in 2020.",
        "future": "The projected reservoir capacity in 2030 was 155 million cubic metres.",
    }),
}


def predict(question, texts):
    requests = requested_components(question)
    catalog = {key: {"source_id": key, "text": value} for key, value in texts.items()}
    report = Record(results=[Record(subtask_id="s01", outcome="evidence",
        sources=[Record(source_id=key, role="support") for key in texts])])
    bindings = {request["component_id"]: ["s01"] for request in requests}
    return {"anchors": [request["question_anchor"] for request in requests],
            "hints": relevance_hints(requests, catalog, report, bindings, {})}


def main():
    predictions = {case: predict(*inputs) for case, inputs in CASES.items()}
    labels = json.loads(Path(__file__).with_name("fact-selection-labels.json").read_bytes())
    assert set(predictions) == set(labels)
    comparisons = {}
    for case, prediction in predictions.items():
        label = labels[case]
        hinted = {span for spans in prediction["hints"].values() for span in spans}
        required = set(label["direct"])
        comparisons[case] = {
            **prediction, "labeled_slot_count": label["requested_facts"],
            "component_count_matches": len(prediction["anchors"]) == label["requested_facts"],
            "missing_direct_hints": sorted(required - hinted),
            "distractor_hints": sorted(hinted & set(label["distractors"])),
            "necessary_context_not_hinted": sorted(set(label["context"]) - hinted),
            "unresolved_facts": label["unresolved"], "conflicting": label["conflicting"],
        }
    print(json.dumps({"method": "baseline only; labels loaded after prediction",
                      "model_calls": 0, "cases": comparisons}, indent=2))


if __name__ == "__main__":
    main()
