"""Verbatim request boundaries; no claim of semantic evidence completeness."""
import pytest

from src.pilot._requests import requested_components


@pytest.mark.parametrize("question,anchors", [
    ("In the 2018 bulletin, what share was foreign, which source led, and did North or South have more projects?",
     ["In the 2018 bulletin, what share was foreign", "which source led", "did North or South have more projects?"]),
    ("For Cedar Bay, what was output, and does that include imports?",
     ["For Cedar Bay, what was output", "does that include imports?"]),
    ("What changed, why did it change, and was it observed or projected?",
     ["What changed", "why did it change", "was it observed or projected?"]),
    ("In April 2018, what changed? Is this an observation?",
     ["In April 2018, what changed?", "Is this an observation?"]),
    ("For 2018, what was output?", ["For 2018, what was output?"]),
    ("What happened in North, South and West?", ["What happened in North, South and West?"]),
    ("What changed in demand and generation?", ["What changed in demand and generation?"]),
    ('What did "Alpha, which Beta" mean, and did output change?',
     ['What did "Alpha, which Beta" mean', 'did output change?']),
    ("What did 'Alpha, which Beta' mean?", ["What did 'Alpha, which Beta' mean?"]),
    ("What changed (including costs, which were provisional), and was scope clear?",
     ["What changed (including costs, which were provisional)", "was scope clear?"]),
])
def test_question_clauses_keep_scope_without_splitting_compound_subjects(question, anchors):
    slots = requested_components(question)
    assert [s["question_anchor"] for s in slots] == anchors
    assert all(a in question for a in anchors)
    assert [s["component_id"] for s in slots] == [f"r{i}" for i in range(1, len(slots)+1)]


def test_overflow_preserves_the_entire_question_instead_of_dropping_requests():
    question = "What was output, which source led, did costs fall, was growth observed, can scope be established, and how old is the source?"
    assert requested_components(question) == [{"component_id": "r1", "question_anchor": question}]
