"""Offline conservative context audit; no LLM or model-metadata requests."""
import argparse
import hashlib
import json
from pathlib import Path
from scripts._llama_token_count import encoding
from src.pilot._evidence import build_span_catalog, selection_payload
from src.pilot._requests import requested_components
from src.pilot.subtasks.generation import CONCURRENT_MAPPING_INSTRUCTION, CONCURRENT_MAPPING_VERSION, selection_schema
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks._coverage import branch_payload
from src.pilot.subtasks._question_spans import question_span_context


def audit(root, plans_name="cq1/plans-v1.json"):
    root = Path(root)
    metadata = root / "tokenizer-metadata.json"
    counter = encoding(json.loads(metadata.read_text(encoding="utf-8")))
    plans = json.loads((root / plans_name).read_text(encoding="utf-8"))
    results = []
    for cid, entry in plans.items():
        plan = Plan.model_validate_json(json.dumps(entry["plan"]))
        report = run_plan(plan, "a"*32, "b"*32, LocalBM25Adapter(entry["corpus_path"]))
        sources = {r.source.source_id: r.source.model_dump() for r in report.sources}
        inputs = {"as_of": "2026-11-06", "question": plan.query,
                  "requests": requested_components(plan.query),
                  "question_spans": question_span_context(plan.query),
                  "evidence": selection_payload(sources, build_span_catalog(sources))}
        if entry.get("complete_required_branches"):
            inputs.update(complete_required_branches=entry["complete_required_branches"], branches=branch_payload(report))
        content = len(counter.encode(CONCURRENT_MAPPING_INSTRUCTION)) + len(counter.encode(
            json.dumps(inputs, ensure_ascii=False, separators=(",", ":"))))
        # json_schema is sent as format, not inserted into messages. Record its
        # size separately; it affects grammar resources but is not prompt text.
        schema = len(counter.encode(json.dumps(selection_schema(build_span_catalog(sources), plan.query,
            report=report, requirements=entry.get("complete_required_branches")).model_json_schema())))
        total = content + 256 + 900
        results.append({"case_id": cid, "message_content_tokens": content,
            "schema_format_tokens_not_in_messages": schema, "framing_allowance": 256,
            "completion_reservation": 900, "total_budget": total,
            "limit": 4096, "within_conservative_allowance": total <= 4096})
    return {"mapping_version": CONCURRENT_MAPPING_VERSION,
        "tokenizer_sha256": hashlib.sha256(metadata.read_bytes()).hexdigest(),
        "template_status": "known no-tools template; framing allowance, not server-observed tokens",
        "generation_calls": 0, "cases": results,
        "all_within_conservative_allowance": all(r["within_conservative_allowance"] for r in results)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--plans", default="cq1/plans-v1.json")
    args = parser.parse_args()
    output = Path(args.output)
    report = audit(args.root, args.plans)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"all_within_allowance": report["all_within_conservative_allowance"],
        "min_total": min(r["total_budget"] for r in report["cases"]),
        "max_total": max(r["total_budget"] for r in report["cases"])}))
