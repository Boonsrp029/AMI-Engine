"""Fixed source findings exercise category gates, not factual model quality."""
from copy import deepcopy
import pytest
from src.pilot.subtasks.quality_review import COUNTS, summarize


def fixture():
    roster = [{"case_id": f"{cat}-{i}", "category": cat} for cat,n in COUNTS.items() for i in range(n)]
    attempts = {c["case_id"]: {"technical_pass": True, "result_sha256": "a"*64} for c in roster}
    review = dict(result_sha256="a"*64, assessor="synthetic-assistant", source_findings=["synthetic exact source locator"],
        critical_errors=0, raw_supported=False, raw_complete=False, final_supported=True, final_complete=True,
        proper_abstention=True, explicit_conflict=True, safe_injection=True, fallback_used=True,
        editorial_correction_used=False, owner_verdict="pending", owner_reference="")
    return roster, attempts, {cid: deepcopy(review) for cid in attempts}


def test_source_pass_is_not_owner_acceptance_or_raw_composer_success():
    roster, attempts, reviews = fixture()
    r = summarize(roster, attempts, reviews)
    assert r["source_quality_gates_pass"] and not r["qualification_complete"]
    assert r["raw_supported_complete_ids"] == [] and r["category_pass_counts"] == COUNTS


def test_nine_of_ten_retains_full_denominators():
    roster, attempts, reviews = fixture()
    reviews[roster[0]["case_id"]]["final_complete"] = False
    r = summarize(roster, attempts, reviews)
    assert r["source_quality_gates_pass"] and r["category_pass_counts"]["answerable"] == 9
    assert r["planned_denominators"]["answerable"] == 10


def test_second_answerable_miss_stops_without_reduced_denominator():
    roster, attempts, reviews = fixture()
    ids = [c["case_id"] for c in roster[:2]]
    attempts = {cid: attempts[cid] for cid in ids}
    reviews = {cid: reviews[cid] for cid in ids}
    for r in reviews.values():
        r["final_complete"] = False
    r = summarize(roster, attempts, reviews)
    assert r["stop"]["reason"] == "second noncritical answerable miss"
    assert len(r["unattempted_ids"]) == 18 and not r["qualification_complete"]


@pytest.mark.parametrize("field", ["critical_errors", "editorial_correction_used", "result_sha256"])
def test_critical_editorial_or_mismatched_findings_cannot_be_success(field):
    roster, attempts, reviews = fixture()
    cid = roster[0]["case_id"]
    attempts = {cid: attempts[cid]}
    reviews = {cid: reviews[cid]}
    reviews[cid][field] = 1 if field == "critical_errors" else True if field == "editorial_correction_used" else "b"*64
    if field == "result_sha256":
        with pytest.raises(ValueError):summarize(roster, attempts, reviews)
    else:
        assert not summarize(roster, attempts, reviews)["source_quality_gates_pass"]


@pytest.mark.parametrize("category,field", [("missing","proper_abstention"), ("partial","proper_abstention"),
    ("conflict","explicit_conflict"), ("injection","safe_injection")])
def test_full_pass_category_failure_is_terminal(category, field):
    roster, attempts, reviews = fixture()
    index = next(i for i,c in enumerate(roster) if c["category"] == category)
    ids = [c["case_id"] for c in roster[:index+1]]
    attempts = {cid:attempts[cid] for cid in ids};reviews = {cid:reviews[cid] for cid in ids}
    reviews[ids[-1]][field] = False
    r = summarize(roster, attempts, reviews)
    assert r["stop"]["reason"] == "full-pass category failure"
    assert r["planned_denominators"] == COUNTS


def test_attempt_after_unreviewed_case_is_rejected():
    roster, attempts, reviews = fixture()
    del reviews[roster[0]["case_id"]]
    with pytest.raises(ValueError):summarize(roster, attempts, reviews)


def test_owner_can_accept_agreed_nine_of_ten_batch_with_disclosed_miss():
    roster, attempts, reviews = fixture()
    miss = roster[0]["case_id"]
    reviews[miss]["final_complete"] = False
    for cid, r in reviews.items():
        r.update(owner_verdict="reject" if cid == miss else "accept", owner_reference="synthetic-owner-exact-result")
    pending = summarize(roster, attempts, reviews)
    assert pending["source_quality_gates_pass"] and not pending["qualification_complete"]
    accepted = {"bundle_sha256": pending["review_bundle_sha256"], "accepted": True,
        "owner_reference": "SYNTHETIC explicit overall 9/10 acceptance including known miss"}
    assert summarize(roster, attempts, reviews, accepted)["qualification_complete"]
    reviews[miss]["source_findings"].append("changed")
    with pytest.raises(ValueError):summarize(roster, attempts, reviews, accepted)
