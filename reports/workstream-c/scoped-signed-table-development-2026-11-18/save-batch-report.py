"""Summarize the two terminal actual attempts without generation or review mutation."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "actual-development-v1"


def read(path):
    return json.loads(path.read_bytes())


def save(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def main():
    contract = read(ROOT / "development-contract.json")
    rows = []
    text = ["# Actual signed-table development review — 18 November 2026", "",
            "Assistant source checks passed both consumed development cases. Owner acceptance is pending. "
            "The original generated drafts remain stored at revision 1 with needs_review status. "
            "This packet does not approve or export those revisions.", ""]
    editorials = []
    for cid in contract["case_ids"]:
        path = OUTPUT / f"{cid}.result.json"
        result = read(path)
        assessment = read(OUTPUT / f"{cid}.assessment.json")
        assert assessment["verdict"] == "pass"
        assert assessment["result_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        wall = read(ROOT / f"wall-clock-{cid}.json")
        stored = result["stored_run"]
        claim = stored["draft"]["claims"][0]["text"]
        proposal = claim.replace("total utility-scale electricity generation", "total U.S. utility-scale electricity generation")
        captures = {stage: read(OUTPUT / f"{cid}.{stage}.raw.json") for stage in ("mapping", "composition")}
        usage = {key: sum(item["usage"][key] for item in captures.values())
                 for key in ("input_tokens", "output_tokens", "total_tokens")}
        rows.append({"case_id": cid, "technical_pass": result["technical_pass"], "assistant_source_gate": "pass",
                     "main_calls": result["main_calls"], "nemo_invocations": result["nemo_invocations"],
                     "wall_seconds": wall["elapsed_seconds"], "capture_reported_main_usage": usage,
                     "result_sha256": assessment["result_sha256"], "owner_acceptance": "pending",
                     "context_note": assessment.get("context_note", "No extra context selected.")})
        editorials.append({"case_id": cid, "original_result_sha256": assessment["result_sha256"],
                          "original_stored_run_id": stored["id"], "original_stored_revision": stored["revision"],
                          "proposed_claim": proposal, "status": "Editorial proposal awaiting exact wording/source review"})
        text.extend([f"## {cid}", "", stored["query"], "", "Exact generated claim", "", f"> {claim}", "",
                     "Proposed editorial copy following the owner's U.S. preference", "", f"> {proposal}", "",
                     f"Source identifier eia-generation-2023. Pinned table heading states U.S. utility-scale electricity generation by source, amount, and share of total in 2023. "
                     f"Selected span {assessment['span_id']}, source character offsets {assessment['source_offsets'][0]}–{assessment['source_offsets'][1]}. "
                     "The column headings are Energy source, Billion kWh and Share of total. "
                     "These are preliminary 2023 net-generation data published in February 2024. PDF page is unavailable for this HTML source.", "",
                     assessment.get("context_note", "No extra context selected."), "",
                     "Raw composer selected the verified unit. Application rendering produced the final prose. "
                     "No fallback or editorial correction occurred in generation. NeMo passed.", "",
                     f"[Exact result](actual-development-v1/{cid}.result.json) · "
                     f"[Source assessment](actual-development-v1/{cid}.assessment.json)", ""])
    text.extend(["## Owner review", "",
                 "Confirm source support, requested amount/share completeness and wording for each case. "
                 "You may accept the proposed U.S.-explicit editorial copies, request a specific change or reject. "
                 "This records semantic/wording review. Saving an approved brief still requires review of that exact stored revision.", "",
                 "This diagnostic is consumed development evidence. It does not establish the twenty-case quality gates or production readiness.", ""])
    save(ROOT / "editorial-proposals.json", editorials)
    with (ROOT / "review-packet.md").open("x", encoding="utf-8") as handle:
        handle.write("\n".join(text))
    save(ROOT / "batch-summary.json", {"contract_sha256": contract["contract_sha256"],
        "status": "Both authorized development attempts complete; allowance exhausted",
        "attempted": 2, "assistant_passed": 2, "failed": 0, "unattempted": 0,
        "main_calls": sum(row["main_calls"] for row in rows),
        "nemo_invocations": sum(row["nemo_invocations"] for row in rows),
        "capture_reported_main_tokens": sum(row["capture_reported_main_usage"]["total_tokens"] for row in rows),
        "internal_nemo_usage": "unmeasured", "monetary_cost": "unmeasured", "cases": rows,
        "historical_cq1": "one pass, one failure, eighteen unattempted; unchanged",
        "owner_acceptance": "pending", "larger_qualification_authorized": False})
    print(json.dumps({"attempted": 2, "assistant_passed": 2, "owner_acceptance": "pending"}))


if __name__ == "__main__":
    main()
