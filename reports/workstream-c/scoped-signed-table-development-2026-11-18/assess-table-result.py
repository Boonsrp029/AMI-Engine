"""Record assistant source checks for an actual attempt; opens no model connection."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_bytes())


def main():
    cid = sys.argv[1]
    label, amount, share = {"cq1-a38": ("Other sources", "10", "0.2%"),
                            "cq1-a37": ("Other gases", "11", "0.3%")}[cid]
    path = ROOT / "actual-development-v1" / f"{cid}.result.json"
    result = read(path)
    stored = result["stored_run"]
    diagnostics = stored["metrics"]["composition_diagnostics"]
    claim, = stored["draft"]["claims"]
    expected = (f"In 2023, the table gives {label} generation in Billion kWh as {amount} and its share "
                f"of total utility-scale electricity generation as {share}.")
    assert result["technical_pass"] and result["main_calls"] <= 4 and result["nemo_invocations"] == 1
    assert stored["status"] == "needs_review" and stored["revision"] == 1
    assert claim == {"text": expected, "source_ids": ["eia-generation-2023"]}
    source = stored["sources"]["eia-generation-2023"]
    source_hash = hashlib.sha256(source["content"].encode()).hexdigest()
    assert source_hash == source["content_sha256"]
    assert "U.S. utility-scale electricity generation by source, amount, and share of total in 2023" in source["content"]
    focus = diagnostics["request_evidence_focus"]["r1"]
    span = diagnostics["span_catalog"][focus["span_id"]]
    assert span["content_sha256"] == source_hash
    assert source["content"][span["start"]:span["end"]] == span["text"]
    assert len(span["text"]) <= 600 and "2023" in span["text"]
    assert "Energy source\nBillion kWh\nShare of total" in span["text"]
    assert re.search(re.escape(label) + r"\s+(?:[1-9]\s+)?" + amount + r"\s+" + re.escape(share), span["text"])
    raw = json.loads(read(path.with_name(f"{cid}.mapping.raw.json"))["raw"])
    group, = raw["facts"][0]["alternatives"]
    direct, = group
    assert direct["span_id"] == focus["span_id"]
    assert len(direct["context"]) == len(set(direct["context"]))
    context_quotes = []
    for sid in direct["context"]:
        part = diagnostics["span_catalog"][sid]
        assert part["source_id"] == "eia-generation-2023" and part["content_sha256"] == source_hash
        assert source["content"][part["start"]:part["end"]] == part["text"]
        context_quotes.append(part["text"])
    assert diagnostics["raw_composer_output"]["claims"] == [{"unit_id": "u1", "component_id": "r1"}]
    assert not diagnostics["fallback_unit_ids"] and not diagnostics["editorial_correction"]
    rendered, = diagnostics["application_rendered_table_rows"]
    assert rendered["text"] == expected and rendered["source_id"] == "eia-generation-2023"
    safety = read(path.with_name(f"{cid}.safety.json"))
    assert safety["passed_guardrails"] is True and safety["validated_report"] == expected
    with sqlite3.connect(path.with_name(f"{cid}.sqlite3").resolve().as_uri() + "?mode=ro", uri=True) as db:
        row = db.execute("SELECT status,revision,draft FROM runs WHERE id=?", (stored["id"],)).fetchone()
        assert row[:2] == ("needs_review", 1) and json.loads(row[2]) == stored["draft"]
        assert db.execute("SELECT COUNT(*) FROM exports").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0] == 0
    assessment = {"result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "assessor": "assistant", "verdict": "pass", "source_findings": [
            f"Pinned EIA U.S. utility-scale 2023 table gives {label}, {amount} billion kWh and {share} of total.",
            f"Exact source window {focus['span_id']} at offsets {span['start']}:{span['end']} retains year, column headings and row.",
            "Actual mapper selects one evidence span. Raw composer selects the verified row unit; application renders the claim. No fallback or editorial correction.",
            "NeMo passed; exact revision 1 is stored as needs_review with no review or export.",
            "U.S. scope is established by the question and pinned table heading but remains implicit in generated wording. Owner prefers explicit U.S.; wording review remains pending."],
        "owner_acceptance": "pending", "source_url": source["url"],
        "source_id": "eia-generation-2023", "source_content_sha256": source_hash,
        "span_id": focus["span_id"], "source_offsets": [span["start"], span["end"]],
        "context_quotes": context_quotes,
        "context_note": ("The model selected additional same-record contextual spans, retained as exact excerpts. "
                         "These passages supply no standalone claim. "
                         "Record as unnecessary context, with the complete direct row and final answer supported."
                         if context_quotes else "No extra context selected.")}
    destination = ROOT / f"{cid}-assessment-input.json"
    with destination.open("x", encoding="utf-8") as handle:
        json.dump(assessment, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"case_id": cid, "assistant_source_gate": "pass", "owner_acceptance": "pending"}))


if __name__ == "__main__":
    main()
