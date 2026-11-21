"""Offline prototype for recognizing a self-contained historical reporting fact."""
import hashlib
import json
from pathlib import Path
import re


_REPORT_QUESTION = re.compile(
    r"what did (?P<subject>[\w -]+?) report (?P<cadence>periodically|weekly|monthly),? "
    r"and who received those reports\?", re.I)
_REPORT_FACT = re.compile(
    r"(?:eventually, |previously, )?(?P<subject>[\w -]+?) could "
    r"(?:(?P<before>periodically|weekly|monthly) )?report "
    r"(?P<item>[\w -]+?) to (?P<recipient>[\w -]+?)"
    r"(?: (?P<after>periodically|weekly|monthly))?\.", re.I)


def focus(question, spans):
    """Return one already-bound sentence with both details and source modality."""
    request = _REPORT_QUESTION.fullmatch(question)
    if request is None:
        return None
    matches = []
    for span_id, text in spans.items():
        fact = _REPORT_FACT.fullmatch(text)
        if fact is None:
            continue
        cadence = [fact[key] for key in ("before", "after") if fact[key]]
        subject = request["subject"].casefold()
        source_subject = fact["subject"].casefold()
        if source_subject == subject and [item.casefold() for item in cadence] == [request["cadence"].casefold()]:
            matches.append({"span_id": span_id, "source_text": text})
    return matches[0] if len(matches) == 1 else None


def main():
    root = Path(__file__).resolve().parent
    result_path = root / "actual-development-v1" / "cq1-a20.result.json"
    result_bytes = result_path.read_bytes()
    saved = json.loads(result_bytes)["stored_run"]
    catalog = saved["metrics"]["composition_diagnostics"]["span_catalog"]
    source = saved["sources"]["eia-measurement"]["content"]
    spans = {sid: span["text"] for sid, span in catalog.items() if span["source_id"] == "eia-measurement"}
    exact_question_focus = focus(saved["query"], spans)
    assert exact_question_focus is None
    # Counterfactual only. No rewrite is used in the frozen attempt or runtime.
    literal_subject_question = saved["query"].replace("automated electricity meters", "automated meters")
    retained = focus(literal_subject_question, spans)
    assert retained["span_id"] == "s_6af27ac482a98ade"
    loc = catalog[retained["span_id"]]
    assert source[loc["start"]:loc["end"]] == retained["source_text"]

    query = "What did harbor beacons report weekly, and who received those reports?"
    direct = "Previously, harbor beacons could report berth vacancies to the port clerk weekly."
    tests = [
        ("direct and background", query, {"direct": direct, "background": "Harbor beacons used batteries."}, "direct"),
        ("distinct figures in split sentences", query,
         {"item": "Harbor beacons could report berth vacancies weekly.", "recipient": "The port clerk received reports."}, None),
        ("different recipient in two complete spans", query,
         {"direct": direct, "alternative": direct.replace("port clerk", "harbor master")}, None),
        ("different subject", query, {"wrong": direct.replace("harbor", "railway")}, None),
        ("different cadence", query, {"wrong": direct.replace("weekly", "monthly")}, None),
        ("current assertion", query, {"wrong": direct.replace("Previously, harbor beacons could report", "Harbor beacons report")}, None),
        ("unrelated two-part request", "What were installation and maintenance costs?", {"direct": direct}, None),
    ]
    outcomes = []
    for label, question, candidates, expected in tests:
        picked = focus(question, candidates)
        assert (picked and picked["span_id"]) == expected, label
        outcomes.append(label)
    print(json.dumps({"runtime_activated": False, "model_calls": 0,
                      "retained_result_sha256": hashlib.sha256(result_bytes).hexdigest(),
                      "exact_question_focus": exact_question_focus,
                      "literal_subject_counterfactual": literal_subject_question,
                      "retained_span": retained, "synthetic_checks_passed": outcomes}, indent=2))


if __name__ == "__main__":
    main()
