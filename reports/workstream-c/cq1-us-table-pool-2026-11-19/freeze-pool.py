"""Freeze two unused source questions and retain eighteen unattempted CQ1 cases."""
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

PRIOR = ROOT.parent / "cq1-context-role-pool-2026-11-18"
ACTUAL = ROOT.parent / "scoped-capacity-evidence-first-development-2026-11-19"
REPLACEMENTS = (
    ("cq1-a43", "Which EIA publication does the 2023 U.S. utility-scale generation table cite as its data source?",
     ["Electric Power Monthly"], "eia-generation-2023",
     "Data source: U.S. Energy Information Administration,\nElectric Power Monthly\n, February 2024; preliminary data"),
    ("cq1-a44", "What information do electronic smart meters send wirelessly in real time, according to the EIA guide?",
     ["Power usage data"], "eia-measurement",
     "electronic smart meters\n. These meters wirelessly send power usage data in real time."),
)


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    old_pool, old_scopes = PRIOR / "pool", PRIOR / "question-scopes"
    manifest = read(old_pool / "manifest.json")
    plans = read(old_pool / "plans-v3-explicit-coverage.json")
    scopes = read(old_scopes / "manifest.json")
    cases = {case["case_id"]: case for case in read(old_pool / "cases.json")}
    prior_batch = read(ACTUAL / "actual-cq1/cq1-a42.summary.json")
    retained = prior_batch["unattempted_ids"]
    assert len(retained) == 18 and not {"cq1-a41", "cq1-a42"}.intersection(retained)
    assert all(digest(old_pool / name) == sha for name, sha in manifest["sha256"].items())
    prior_questions = set()
    inspected = {}
    for path in ROOT.parent.rglob("cases.json"):
        if path.is_relative_to(ROOT) or "executed-input-snapshot" in path.parts:
            continue
        rows = read(path)
        if isinstance(rows, list):
            prior_questions.update(row["query"].casefold() for row in rows if isinstance(row, dict) and "query" in row)
            inspected[str(path)] = digest(path)
    assert all(query.casefold() not in prior_questions for _, query, _, _, _ in REPLACEMENTS)
    pool, scope_folder = ROOT / "pool", ROOT / "question-scopes"
    shutil.copytree(old_pool, pool)
    scope_folder.mkdir()
    sources = {row["feed_id"]: row for row in read(pool / "public-corpus.json")}
    corpus_sha = digest(pool / "public-corpus.json")
    revised_cases, revised_plans, revised_scopes, provenance = [], {}, {}, []
    for cid, query, required, source_id, quote in REPLACEMENTS:
        source = sources[source_id]
        assert len(requested_components(query)) == 1
        start = source["clean_content"].index(quote)
        row = {**cases["cq1-a41"], "case_id": cid, "query": query, "required_findings": required}
        entry = deepcopy(plans["cq1-a41"])
        entry["plan"]["query"] = entry["plan"]["subtasks"][0]["query"] = query
        assert entry["plan"]["corpus_sha256"] == corpus_sha
        plan = Plan.model_validate_json(json.dumps(entry["plan"]))
        payload = {"version": "cq-scoped-disclosures-v1", "plan_id": plan.plan_id, "corpus_sha256": corpus_sha,
            "question_sha256": hashlib.sha256(query.encode()).hexdigest(),
            "bindings_sha256": bindings_hash(entry["bindings"]),
            "declaration_ref": "Unused question frozen before generation; source document is familiar.",
            "annotations": [{"component_id": "r1", "subtask_id": "s01",
                             "question_span": {"start": 0, "end": len(query)}}]}
        validate_scopes(plan, entry["bindings"], DisclosureScopes.model_validate(payload))
        write(scope_folder / f"{cid}.json", payload)
        revised_scopes[cid] = {"path": f"{cid}.json", "sha256": digest(scope_folder / f"{cid}.json")}
        revised_cases.append(row)
        revised_plans[cid] = entry
        provenance.append({"case_id": cid, "source_id": source["feed_id"], "url": source["url"],
            "quote": quote, "start": start, "end": start + len(quote),
            "note": "Distinct requested fact from a previously used source document."})
    for cid in retained:
        item = scopes["cases"][cid]
        assert not (ACTUAL / "actual-cq1" / f"{cid}.started.json").exists()
        shutil.copyfile(old_scopes / item["path"], scope_folder / item["path"])
        assert digest(scope_folder / item["path"]) == item["sha256"]
        revised_cases.append(cases[cid])
        revised_plans[cid] = plans[cid]
        revised_scopes[cid] = item
    assert dict(Counter(row["category"] for row in revised_cases)) == manifest["categories"]
    write(pool / "cases.json", revised_cases)
    write(pool / "plans-v3-explicit-coverage.json", revised_plans)
    proof = "us-table-replacement-provenance.json"
    write(pool / proof, {"retained_case_ids": retained, "excluded_consumed_ids": ["cq1-a41", "cq1-a42"],
        "replacement_sources": provenance, "corpus_sha256": corpus_sha,
        "prior_case_manifest_sha256": inspected, "question_holdout_only": True})
    manifest["sha256"].update({"cases.json": digest(pool / "cases.json"), proof: digest(pool / proof)})
    order = [row["case_id"] for row in revised_cases]
    manifest.update(revision="us-table-development", case_order=order,
        supersedes_manifest_sha256=digest(old_pool / "manifest.json"),
        excluded_consumed_case=["cq1-a41", "cq1-a42"], replacement_case=[row[0] for row in REPLACEMENTS],
        retained_unattempted_cases=retained)
    write(pool / "manifest.json", manifest)
    pool_sha, plans_sha = digest(pool / "manifest.json"), digest(pool / "plans-v3-explicit-coverage.json")
    write(pool / "plans-v3-coverage-manifest.json", {"plans_file": "plans-v3-explicit-coverage.json",
        "sha256": plans_sha, "original_content_manifest_sha256": pool_sha,
        "note": "Eighteen exact retained cases and two unused questions from familiar source material."})
    write(scope_folder / "manifest.json", {"version": scopes["version"], "pool_manifest_sha256": pool_sha,
        "plans_sha256": plans_sha, "case_ids": order, "cases": revised_scopes})
    write(ROOT / "freeze-audit.json", {"retained_case_ids": retained, "retained_questions_and_plans": 18,
        "retained_scope_sidecars": 18, "replacement_ids": [row[0] for row in REPLACEMENTS],
        "pool_sha256": pool_sha, "plans_sha256": plans_sha,
        "scope_manifest_sha256": digest(scope_folder / "manifest.json"),
        "prior_contract_sha256": read(ACTUAL / "qualification-contract.json")["contract_sha256"], "actual_model_calls": 0})
    print(json.dumps({"retained": 18, "replacements": 2, "actual_model_calls": 0}))


if __name__ == "__main__":
    main()
