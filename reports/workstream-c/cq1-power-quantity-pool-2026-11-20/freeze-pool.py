"""Freeze three unused source questions and retain seventeen unattempted CQ1 cases."""
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

PRIOR = ROOT.parent / "cq1-publication-pool-2026-11-20"
ACTUAL = ROOT.parent / "scoped-publication-development-2026-11-20"
REPLACEMENTS = (
    ("cq1-a46", "Which invention does the EIA measurement guide attribute to James Watt?",
     ["The steam engine"], "eia-measurement", "James Watt, the inventor of the steam engine."),
    ("cq1-a47", "How does the EIA measurement guide define one watthour?",
     ["The energy of one watt used for one hour"], "eia-measurement",
     "One Watthour is the energy of one Watt used for one hour."),
    ("cq1-a48", "Does the EIA other utility-scale sources category include sulfur and tire-derived fuel?",
     ["Yes, both sulfur and tire-derived fuel are included"], "eia-generation-2023",
     "Other (utility-scale) sources includes non-biogenic municipal solid waste, batteries, hydrogen, purchased steam, sulfur, tire-derived fuel, and other miscellaneous energy sources."),
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
    prior_batch = read(ACTUAL / "cq1-stop-analysis.json")
    retained = prior_batch["unattempted"]
    assert len(retained) == 17 and not set(prior_batch["attempted"]).intersection(retained)
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
        row = {**cases["cq1-a45"], "case_id": cid, "query": query, "required_findings": required}
        entry = deepcopy(plans["cq1-a45"])
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
    proof = "power-quantity-replacement-provenance.json"
    write(pool / proof, {"retained_case_ids": retained, "excluded_consumed_ids": prior_batch["attempted"],
        "replacement_sources": provenance, "corpus_sha256": corpus_sha,
        "prior_case_manifest_sha256": inspected, "question_holdout_only": True})
    manifest["sha256"].update({"cases.json": digest(pool / "cases.json"), proof: digest(pool / proof)})
    order = [row["case_id"] for row in revised_cases]
    manifest.update(revision="power-quantity-development", case_order=order,
        supersedes_manifest_sha256=digest(old_pool / "manifest.json"),
        excluded_consumed_case=prior_batch["attempted"], replacement_case=[row[0] for row in REPLACEMENTS],
        retained_unattempted_cases=retained)
    write(pool / "manifest.json", manifest)
    pool_sha, plans_sha = digest(pool / "manifest.json"), digest(pool / "plans-v3-explicit-coverage.json")
    write(pool / "plans-v3-coverage-manifest.json", {"plans_file": "plans-v3-explicit-coverage.json",
        "sha256": plans_sha, "original_content_manifest_sha256": pool_sha,
        "note": "Seventeen exact retained cases and three unused questions from familiar source material."})
    write(scope_folder / "manifest.json", {"version": scopes["version"], "pool_manifest_sha256": pool_sha,
        "plans_sha256": plans_sha, "case_ids": order, "cases": revised_scopes})
    write(ROOT / "freeze-audit.json", {"retained_case_ids": retained, "retained_questions_and_plans": 17,
        "retained_scope_sidecars": 17, "replacement_ids": [row[0] for row in REPLACEMENTS],
        "pool_sha256": pool_sha, "plans_sha256": plans_sha,
        "scope_manifest_sha256": digest(scope_folder / "manifest.json"),
        "prior_contract_sha256": read(ACTUAL / "qualification-contract.json")["contract_sha256"], "actual_model_calls": 0})
    print(json.dumps({"retained": 17, "replacements": 3, "actual_model_calls": 0}))


if __name__ == "__main__":
    main()
