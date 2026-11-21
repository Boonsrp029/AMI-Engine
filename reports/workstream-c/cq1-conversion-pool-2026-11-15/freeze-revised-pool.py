"""Freeze two unused answerable questions while retaining 18 prior CQ1 cases."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))

from src.pilot._requests import requested_components
from src.pilot.subtasks._disclosures import DisclosureScopes, bindings_hash, validate_scopes
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.scheduler import run_plan

PRIOR = ROOT.parent / "cq1-fact-span-pool-2026-11-15"
ACTUAL = ROOT.parent / "scoped-table-focus-development-2026-11-15"
CONSUMED = ("cq1-a21", "cq1-a22")
REPLACEMENTS = (
    ("cq1-a23", "What were landfill gas generation and its share of US utility-scale generation in 2023?",
     ["8 billion kWh", "0.2% of total U.S. utility-scale generation in 2023"], "Landfill gas\n8\n0.2%"),
    ("cq1-a24", "Which gases does the EIA include in the other gases category?",
     ["blast furnace gas", "other manufactured and waste gases derived from fossil fuels"],
     "Other gases includes blast furnace gas and other manufactured and waste gases derived from fossil fuels."),
)


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def replace_json(path, value):
    # Only the newly copied contract metadata is mutable before this freeze.
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    old_pool = PRIOR / "pool"
    old_scope = PRIOR / "question-scopes"
    manifest = read(old_pool / "manifest.json")
    plans = read(old_pool / "plans-v3-explicit-coverage.json")
    scopes = read(old_scope / "manifest.json")
    old_audit = read(PRIOR / "freeze-audit.json")
    for path, field in ((old_pool / "manifest.json", "pool_sha256"),
                        (old_pool / "plans-v3-explicit-coverage.json", "plans_sha256"),
                        (old_scope / "manifest.json", "scope_manifest_sha256")):
        assert digest(path) == old_audit[field]
    assert all(digest(old_pool / name) == sha for name, sha in manifest["sha256"].items())
    assert all(digest(old_scope / item["path"]) == item["sha256"] for item in scopes["cases"].values())
    batch = read(ACTUAL / "qualification-batch-summary.json")
    assert batch["attempted_ids"] == list(CONSUMED)
    retained = batch["unattempted_ids"]
    assert len(retained) == 18 and manifest["case_order"] == [*CONSUMED, *retained]
    old_cases = {case["case_id"]: case for case in read(old_pool / "cases.json")}

    pool = ROOT / "pool"
    scope = ROOT / "question-scopes"
    shutil.copytree(old_pool, pool)
    scope.mkdir()
    for cid in retained:
        file = scopes["cases"][cid]["path"]
        shutil.copyfile(old_scope / file, scope / file)
        assert digest(scope / file) == scopes["cases"][cid]["sha256"]

    corpus = pool / "public-corpus.json"
    sources = {row["feed_id"]: row for row in read(corpus)}
    source = sources["eia-generation-2023"]
    corpus_sha = digest(corpus)
    new_cases, new_plans, new_scopes, provenance = [], {}, {}, []
    for cid, question, required, quote in REPLACEMENTS:
        assert len(requested_components(question)) == 1
        start = source["clean_content"].index(quote)
        entry = deepcopy(plans[CONSUMED[0]])
        entry["plan"]["query"] = entry["plan"]["subtasks"][0]["query"] = question
        assert entry["plan"]["corpus_sha256"] == corpus_sha
        plan = Plan.model_validate_json(json.dumps(entry["plan"]))
        bindings = entry["bindings"]
        payload = {"version": "cq-scoped-disclosures-v1", "plan_id": plan.plan_id, "corpus_sha256": corpus_sha,
                   "question_sha256": hashlib.sha256(question.encode()).hexdigest(),
                   "bindings_sha256": bindings_hash(bindings),
                   "declaration_ref": "Replacement question scope frozen before generation.",
                   "annotations": [{"component_id": "r1", "subtask_id": "s01",
                                    "question_span": {"start": 0, "end": len(question)}}]}
        validate_scopes(plan, bindings, DisclosureScopes.model_validate(payload))
        scope_name = cid + ".json"
        write(scope / scope_name, payload)
        new_scopes[cid] = {"path": scope_name, "sha256": digest(scope / scope_name)}
        new_plans[cid] = entry
        row = {**old_cases[CONSUMED[0]], "case_id": cid, "query": question, "required_findings": required}
        new_cases.append(row)
        report = run_plan(plan, "a" * 32, "b" * 32, LocalBM25Adapter(corpus))
        assert any(item.source_id == source["feed_id"] and item.role == "support"
                   for branch in report.results for item in branch.sources)
        provenance.append({"case_id": cid, "source_id": source["feed_id"], "url": source["url"],
                           "start": start, "end": start + len(quote), "quote": quote})

    cases = [*new_cases, *(old_cases[cid] for cid in retained)]
    revised_plans = {**new_plans, **{cid: plans[cid] for cid in retained}}
    order = [row["case_id"] for row in cases]
    assert dict(Counter(row["category"] for row in cases)) == manifest["categories"]
    replace_json(pool / "cases.json", cases)
    replace_json(pool / "plans-v3-explicit-coverage.json", revised_plans)
    proof = "conversion-replacement-provenance.json"
    write(pool / proof, {"prior_contract_sha256": batch["contract_sha256"], "retained_case_ids": retained,
                         "excluded_consumed_case_ids": list(CONSUMED), "replacement_sources": provenance,
                         "corpus_sha256": corpus_sha})
    manifest["sha256"]["cases.json"] = digest(pool / "cases.json")
    manifest["sha256"][proof] = digest(pool / proof)
    manifest.update(revision="conversion-development", case_order=order,
                    supersedes_manifest_sha256=old_audit["pool_sha256"],
                    excluded_consumed_case=list(CONSUMED), replacement_case=list(new_plans),
                    retained_unattempted_cases=retained)
    replace_json(pool / "manifest.json", manifest)
    pool_sha = digest(pool / "manifest.json")
    plans_sha = digest(pool / "plans-v3-explicit-coverage.json")
    replace_json(pool / "plans-v3-coverage-manifest.json", {
        "plans_file": "plans-v3-explicit-coverage.json", "sha256": plans_sha,
        "original_content_manifest_sha256": pool_sha, "note": "18 retained cases and two fresh answerable replacements."})
    write(scope / "manifest.json", {"version": scopes["version"], "pool_manifest_sha256": pool_sha,
                                   "plans_sha256": plans_sha, "case_ids": order,
                                   "cases": {**new_scopes, **{cid: scopes["cases"][cid] for cid in retained}}})
    write(ROOT / "freeze-audit.json", {
        "retained_case_ids": retained, "retained_questions_and_plans": 18, "retained_scope_sidecars": 18,
        "replacement_ids": list(new_plans), "pool_sha256": pool_sha, "plans_sha256": plans_sha,
        "scope_manifest_sha256": digest(scope / "manifest.json"), "prior_contract_sha256": batch["contract_sha256"],
        "prior_result_sha256": {cid: digest(ACTUAL / "actual-cq1" / (cid + ".result.json")) for cid in CONSUMED},
        "actual_model_calls": 0,
    })


if __name__ == "__main__":
    main()

