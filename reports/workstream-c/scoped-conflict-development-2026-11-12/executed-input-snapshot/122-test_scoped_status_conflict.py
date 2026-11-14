"""Test evidence needed for an explicit provisional-or-final conflict."""
from types import SimpleNamespace

import pytest

from src.pilot._evidence import EvidenceComponent
from src.pilot.subtasks._status_conflict import validate_publication_status_conflict


SUBJECT = "The 2017 Laos rice processing figures"
PROVISIONAL = f"{SUBJECT} are provisional."


@pytest.mark.parametrize(("second", "passes"), [
    ("In Laos, mills processed 14 tonnes of rice in 2017.", False),
    ("The 2016 Laos rice processing figures are final.", False),
    ("The 2017 Laos rice export figures are final.", False),
    (f"{SUBJECT} are not final.", False),
    (f"{SUBJECT} are preliminary.", False),
    (f"If {SUBJECT.lower()} are final", False),
    (f'"{SUBJECT} are final."', False),
    (f"{SUBJECT} are final.", True),
    (f"{SUBJECT} are not provisional.", True),
])
def test_publication_status_conflict_needs_opposed_same_subject_statements(second, passes):
    component = EvidenceComponent(
        component_id="r2", status="conflicting", short_answer="",
        question_anchor="were the figures provisional or final?",
        evidence=[{"source_id": "notice", "quote": PROVISIONAL},
                  {"source_id": "other", "quote": second}],
    )
    mapping = SimpleNamespace(components=[component])
    if passes:
        validate_publication_status_conflict(mapping)
    else:
        with pytest.raises(ValueError, match="opposed assertions"):
            validate_publication_status_conflict(mapping)
