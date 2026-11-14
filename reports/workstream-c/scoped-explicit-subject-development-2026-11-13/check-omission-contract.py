"""Offline prototype for explicit omissions in concurrent composition."""
import json
from pathlib import Path


def check_omissions(unit_origins, emitted, omitted):
    """Check ID accounting and retain at least one emitted unit per covered component."""
    if len(set(emitted)) != len(emitted) or len(set(omitted)) != len(omitted):
        raise ValueError("Duplicate unit decision")
    emitted_ids, omitted_ids = set(emitted), set(omitted)
    if emitted_ids & omitted_ids or emitted_ids | omitted_ids != unit_origins.keys():
        raise ValueError("Every unit needs exactly one decision")
    kept_components = set().union(*(unit_origins[uid] for uid in emitted))
    if any(not unit_origins[uid] <= kept_components for uid in omitted):
        raise ValueError("Omission removes a component's only emitted evidence")
    return omitted_ids


def main():
    # An older reporting device could send a weekly manifest to a port clerk.
    # General port record-keeping supplies background but answers no part.
    origins = {"u1": {"r1", "r2"}, "u2": {"r1"}, "u3": {"r3"}}
    assert check_omissions(origins, ["u1", "u3"], ["u2"]) == {"u2"}
    assert check_omissions(origins, ["u1", "u2", "u3"], []) == set()
    for emitted, omitted, reason in [
        (["u1"], ["u2", "u3"], "only emitted evidence"),
        (["u1", "u3"], [], "exactly one decision"),
        (["u1", "u3"], ["u2", "u4"], "exactly one decision"),
        (["u1", "u3"], ["u1", "u2"], "exactly one decision"),
        (["u1", "u1", "u3"], ["u2"], "Duplicate unit decision"),
        (["u2", "u3"], ["u1"], "only emitted evidence"),
    ]:
        try:
            check_omissions(origins, emitted, omitted)
        except ValueError as error:
            assert reason in str(error)
        else:
            raise AssertionError("Expected rejection")
    record = {"synthetic_checks_passed": 8, "model_calls": 0,
              "activated": False, "semantic_coverage_verified": False}
    print(json.dumps(record))


if __name__ == "__main__":
    main()
