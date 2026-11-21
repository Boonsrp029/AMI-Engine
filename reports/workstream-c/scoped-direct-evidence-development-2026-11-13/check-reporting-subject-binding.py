"""Offline check of an explicitly adjudicated, same-record subject binding."""
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = spec_from_file_location("reporting_focus", ROOT / "check-historical-reporting-focus.py")
prototype = module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


def digest(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def bind(question, source_id, source, spans, declaration):
    """Apply a reviewed subject relationship to one exact source and fact."""
    request = prototype._REPORT_QUESTION.fullmatch(question)
    if request is None or request["subject"].casefold() != declaration["question_subject"]:
        return None
    if source_id != declaration["source_id"] or digest(source) != declaration["source_sha256"]:
        return None
    target = spans.get(declaration["fact_span_id"])
    if target is None or target["source_id"] != source_id or target["content_sha256"] != digest(source):
        return None
    start, end = declaration["context_offsets"]
    if (not 0 <= start < end <= target["start"] < target["end"] <= len(source)
            or source[start:end] != declaration["context_text"]
            or source[target["start"]:target["end"]] != target["text"]):
        return None
    # Construct a comparison string only. The actual request and citations
    # retain their original text and identities.
    left, right = request.span("subject")
    comparison = question[:left] + declaration["source_subject"] + question[right:]
    same_record = {sid: span["text"] for sid, span in spans.items() if span["source_id"] == source_id}
    found = prototype.focus(comparison, same_record)
    if found is None or found["span_id"] != declaration["fact_span_id"]:
        return None
    return {**found, "source_id": source_id, "fact_offsets": [target["start"], target["end"]],
            "context_offsets": [start, end]}


def main():
    result_path = ROOT / "actual-development-v1" / "cq1-a20.result.json"
    result_bytes = result_path.read_bytes()
    result = json.loads(result_bytes)["stored_run"]
    sid = "eia-measurement"
    source = result["sources"][sid]["content"]
    spans = result["metrics"]["composition_diagnostics"]["span_catalog"]
    reviewed = {
        "question_subject": "automated electricity meters", "source_subject": "automated meters",
        "source_id": sid, "source_sha256": digest(source), "fact_span_id": "s_6af27ac482a98ade",
        "context_offsets": [1315, 1416], "context_text": source[1315:1416],
    }
    actual = bind(result["query"], sid, source, spans, reviewed)
    assert actual is not None and actual["fact_offsets"] == [1417, 1503]

    question = "What did harbor navigation beacons report weekly, and who received those reports?"
    context = "The port authority classified these devices as harbor navigation beacons."
    fact = "Previously, harbor beacons could report berth vacancies to the port clerk weekly."
    newer = "Modern radio beacons report electronic status to shipping crews."
    synthetic = f"{context} {fact} {newer}"
    start = len(context) + 1
    records = {
        "fact": {"source_id": "harbor", "content_sha256": digest(synthetic),
                 "start": start, "end": start + len(fact), "text": fact},
        "newer": {"source_id": "harbor", "content_sha256": digest(synthetic),
                  "start": start + len(fact) + 1, "end": len(synthetic), "text": newer},
    }
    declaration = {
        "question_subject": "harbor navigation beacons", "source_subject": "harbor beacons",
        "source_id": "harbor", "source_sha256": digest(synthetic), "fact_span_id": "fact",
        "context_offsets": [0, len(context)], "context_text": context,
    }
    assert bind(question, "harbor", synthetic, records, declaration)["source_text"] == fact
    negatives = [
        ("different subject", question.replace("navigation", "weather"), "harbor", synthetic, records, declaration),
        ("different cadence", question.replace("weekly", "monthly"), "harbor", synthetic, records, declaration),
        ("different record", question, "other", synthetic, records, declaration),
        ("changed source", question, "harbor", synthetic + " Extra text.", records, declaration),
        ("wrong fact offsets", question, "harbor", synthetic,
         {**records, "fact": {**records["fact"], "start": start + 1}}, declaration),
        ("new device substituted", question, "harbor", synthetic, records, {**declaration, "fact_span_id": "newer"}),
        ("wrong context", question, "harbor", synthetic, records, {**declaration, "context_text": newer}),
        ("multiple complete matches", question, "harbor", synthetic,
         {**records, "another": {**records["fact"], "text": fact.replace("port clerk", "harbor master")}}, declaration),
    ]
    for label, *args in negatives:
        assert bind(*args) is None, label
    print(json.dumps({
        "runtime_activated": False, "model_calls": 0,
        "result_sha256": hashlib.sha256(result_bytes).hexdigest(),
        "frozen_question_used": result["query"],
        "subject_binding": reviewed,
        "bound_fact": actual,
        "synthetic_checks_passed": ["reviewed context"] + [case[0] for case in negatives],
        "semantic_equivalence_basis": "assistant adjudication of the pinned local context",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
