"""Freeze ten unused answerable questions while retaining ten prior CQ1 cases."""
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

PRIOR = ROOT.parent / "cq1-membership-pool-2026-11-15"
ACTUAL = ROOT.parent / "scoped-membership-rendering-2026-11-15"
CONSUMED = ("cq1-a25", "cq1-a26", "cq1-a16", "cq1-a17", "cq1-a18", "cq1-a06", "cq1-a07", "cq1-a08", "cq1-a09", "cq1-a10")
REPLACEMENTS = (
    ("cq1-a27", "What were municipal solid waste (biogenic) generation and its share of US utility-scale generation in 2023?",
     ["6 billion kWh", "0.1% of total U.S. utility-scale generation in 2023"],
     "eia-generation-2023", "Municipal solid waste (biogenic)\n6\n0.1%"),
    ("cq1-a28", "What were geothermal generation and its share of US utility-scale generation in 2023?",
     ["16 billion kWh", "0.4% of total U.S. utility-scale generation in 2023"],
     "eia-generation-2023", "Geothermal\n16\n0.4%"),
    ("cq1-a29", "How many watts are equivalent to one gigawatt in the EIA measurement guide?",
     ["1,000,000,000 watts"], "eia-measurement", "Gigawatts (GW): One GW is 1,000 MW, or 1,000,000,000 Watts."),
    ("cq1-a30", "Who is the watt named after in the EIA measurement guide?",
     ["James Watt"], "eia-measurement", "Watts, named after James Watt"),
    ("cq1-a31", "Where does electricity for pumping water typically come from in pumped storage systems?",
     ["Most systems use electricity from an electric power grid to pump water"],
     "eia-generation-2023", "Most pumped storage systems use electricity from an\nelectric power grid\nfor pumping water to the storage component of the system."),
    ("cq1-a32", "Where does EIA say smaller solar PV systems are usually installed?",
     ["On building rooftops"], "eia-generation-2023", "Smaller PV systems are usually installed on building rooftops."),
    ("cq1-a33", "What does EIA say about the siting and net metering of small-scale solar PV systems?",
     ["Most are at or near the location where electricity is consumed", "Many are net metered, without claiming all or most are net metered"],
     "eia-generation-2023", "Most small-scale PV systems are at or near the location where the electricity is consumed and many are\nnet metered systems\n."),
    ("cq1-a34", "Which four fuel categories does EIA include in the fossil-fuel share of U.S. electricity generation in its 2023 summary?",
     ["coal", "natural gas", "petroleum", "other gases"],
     "eia-generation-2023", "About 60% of this electricity generation was from fossil fuels—coal, natural gas, petroleum, and other gases."),
    ("cq1-a35", "Does the EIA other utility-scale sources category include batteries and purchased steam?",
     ["Yes, both batteries and purchased steam are included"],
     "eia-generation-2023", "Other (utility-scale) sources includes non-biogenic municipal solid waste, batteries, hydrogen, purchased steam"),
    ("cq1-a36", "Does the EIA utility-scale generation table report net or gross electricity generation?",
     ["Net electricity generation"], "eia-generation-2023", "Data are for\nnet electricity generation\n."),
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
    assert batch["attempted"] == list(CONSUMED)
    retained = batch["unattempted"]
    assert len(retained) == 10 and manifest["case_order"] == [*CONSUMED, *retained]
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

    corpus_sha = digest(corpus)
    new_cases, new_plans, new_scopes, provenance = [], {}, {}, []
    for cid, question, required, source_id, quote in REPLACEMENTS:
        source = sources[source_id]
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
    proof = "coverage-replacement-provenance.json"
    write(pool / proof, {"prior_contract_sha256": batch["contract_sha256"], "retained_case_ids": retained,
                         "excluded_consumed_case_ids": list(CONSUMED), "replacement_sources": provenance,
                         "corpus_sha256": corpus_sha})
    manifest["sha256"]["cases.json"] = digest(pool / "cases.json")
    manifest["sha256"][proof] = digest(pool / proof)
    manifest.update(revision="request-coverage-development", case_order=order,
                    supersedes_manifest_sha256=old_audit["pool_sha256"],
                    excluded_consumed_case=list(CONSUMED), replacement_case=list(new_plans),
                    retained_unattempted_cases=retained)
    replace_json(pool / "manifest.json", manifest)
    pool_sha = digest(pool / "manifest.json")
    plans_sha = digest(pool / "plans-v3-explicit-coverage.json")
    replace_json(pool / "plans-v3-coverage-manifest.json", {
        "plans_file": "plans-v3-explicit-coverage.json", "sha256": plans_sha,
        "original_content_manifest_sha256": pool_sha, "note": "Ten retained cases and ten fresh answerable replacements."})
    write(scope / "manifest.json", {"version": scopes["version"], "pool_manifest_sha256": pool_sha,
                                   "plans_sha256": plans_sha, "case_ids": order,
                                   "cases": {**new_scopes, **{cid: scopes["cases"][cid] for cid in retained}}})
    write(ROOT / "freeze-audit.json", {
        "retained_case_ids": retained, "retained_questions_and_plans": 10, "retained_scope_sidecars": 10,
        "replacement_ids": list(new_plans), "pool_sha256": pool_sha, "plans_sha256": plans_sha,
        "scope_manifest_sha256": digest(scope / "manifest.json"), "prior_contract_sha256": batch["contract_sha256"],
        "prior_result_sha256": {cid: digest(ACTUAL / "actual-cq1" / (cid + ".result.json")) for cid in CONSUMED},
        "actual_model_calls": 0,
    })


if __name__ == "__main__":
    main()



