"""Test source-bound action and example coverage on archived CQ1 outputs."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

_ACTION = re.compile(r"(?P<subject>Some [a-z -]+) can (?:even )?(?P<first>[^.;]+?) and (?P<second>[^.;]+)\.", re.I)
_EXAMPLE = re.compile(r"For example, if (?P<conditions>[^,]+), (?P<result>[^,.;]+)"
                      r"(?:, or [^,;]+, of [^.;]+)?\.", re.I)


def normalize(value):
    return " ".join(value.casefold().split())


def coverage_kind(question, quote):
    """Only use a single affirmative source sentence with a recognized relationship."""
    if re.match(r"What two capabilities\b", question, re.I):
        found = _ACTION.fullmatch(quote)
        if found and " and " not in normalize(found["second"]):
            return "counted_capabilities", {k: found[k] for k in ("subject", "first", "second")}
    if re.search(r"\bhow much\b.*\bexample\b", question, re.I):
        found = _EXAMPLE.fullmatch(quote)
        if found:
            return "example_conditions", {k: found[k] for k in ("conditions", "result")}
    return None


def probe(cid, summary):
    path = ROOT / "actual-cq1" / f"{cid}.result.json"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == next(row["result_sha256"] for row in summary["rows"] if row["id"] == cid)
    run = json.loads(path.read_bytes())["stored_run"]
    trace = run["metrics"]["composition_diagnostics"]
    matches = []
    for unit in trace["canonical_composition_units"]:
        for evidence in unit["evidence"]:
            matched = coverage_kind(run["query"], evidence["quote"])
            if matched:
                matches.append((unit, matched))
    (unit, (kind, required)), = matches
    drafts = trace["raw_composer_output"]["claims"]
    raw, = [claim["text"] for claim in drafts if claim["unit_id"] == unit["unit_id"]]
    # This literal probe exposes lost source structure; it is not an entailment judge.
    missing = [name for name, value in required.items()
               if name != "result" and normalize(value) not in normalize(raw)]
    assert missing
    others = [claim["unit_id"] for claim in drafts if claim["component_id"] == unit["component_id"]
              and claim["unit_id"] != unit["unit_id"]]
    return {"kind": kind, "unit": unit["unit_id"], "source": unit["evidence"][0]["source_id"],
            "result_sha256": digest, "source_fields": required, "saved_raw_text": raw,
            "missing_literal_fields": missing, "other_same_component_units": others}


def main():
    summary = json.loads((ROOT / "qualification-batch-summary.json").read_bytes())
    assert len(summary["unattempted"]) == 10
    results = {cid: probe(cid, summary) for cid in ("cq1-a26", "cq1-a10")}
    assert {"subject", "second"} <= set(results["cq1-a26"]["missing_literal_fields"])
    assert results["cq1-a10"]["missing_literal_fields"] == ["conditions"]
    assert results["cq1-a10"]["other_same_component_units"] == ["u3"]

    capability = "What two capabilities does the report describe for refrigerated lockers?"
    two = "Some refrigerated lockers can detect door openings and log temperature remotely."
    example = "How much water does the garden sprinkler example use?"
    amount = "For example, if you run a six-liter-per-minute sprinkler for four minutes, you have used 24 liters."
    fixtures = [(capability, two, "counted_capabilities"),
                (capability, "Some refrigerated lockers can detect door openings.", None),
                (capability, two.replace("can", "cannot"), None),
                (capability, two.replace("remotely", "remotely and send alerts"), None),
                (example, amount, "example_conditions"),
                (example, "For example, the total is 24 liters.", None),
                ("How much water does it use?", amount, None)]
    for question, quote, expected in fixtures:
        match = coverage_kind(question, quote)
        assert (match[0] if match else None) == expected
    print(json.dumps({"offline_only": True, "actual_model_calls": 0, "runtime_changed": False,
                      "synthetic_checks": len(fixtures), "archived_replays": results}, indent=2))


if __name__ == "__main__":
    main()
