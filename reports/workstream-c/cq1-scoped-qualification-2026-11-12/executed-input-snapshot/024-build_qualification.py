"""Offline-only future CQ1 compiler. Does not issue grants or start attempts."""
import argparse
import json
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[3]))

from src.pilot.subtasks._development_lineage import canonical_hash, verify_lineage
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.quality_review import COUNTS, THRESHOLDS, summarize
from src.pilot.subtasks._disclosures import DisclosureScopes, validate_scopes
from src.pilot.subtasks._scoped_activation import CONTRACT_VERSION


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def inside(root,name):
    path=(Path(root)/name).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("Pool locator leaves its frozen root")
    return path


def scoped_cases(cases, manifest_path, expected_sha256, pool_sha256, plans_sha256):
    """Caller-declared task scopes only; no source facts, inference or grants."""
    manifest_path=Path(manifest_path).resolve()
    if digest(manifest_path)!=expected_sha256:
        raise ValueError("Requested-scope manifest identity differs")
    bundle=read(manifest_path)
    if (bundle.get("version")!="cq1-requested-scopes-v1"
            or bundle.get("pool_manifest_sha256")!=pool_sha256
            or bundle.get("plans_sha256")!=plans_sha256
            or bundle.get("case_ids")!=list(cases) or set(bundle.get("cases",{}))!=set(cases)):
        raise ValueError("Requested-scope manifest differs from exact pool/plans/roster")
    output={};inputs={str(manifest_path):expected_sha256}
    for cid,case in cases.items():
        entry=bundle["cases"][cid]
        path=inside(manifest_path.parent,entry["path"])
        if digest(path)!=entry["sha256"]:
            raise ValueError("Frozen requested scope changed")
        scope=DisclosureScopes.model_validate_json(path.read_text(encoding="utf-8"))
        plan=Plan.model_validate_json(json.dumps(case["plan"]))
        validate_scopes(plan,case["bindings"],scope)
        output[cid]={**case,"requested_scopes":str(path),"requested_scopes_sha256":entry["sha256"]}
        inputs[str(path)]=entry["sha256"]
    return output,inputs


def build(development_path,expected_identity,pool,destination,output_directory,as_of,*,expected_pool_sha256,expected_plans_sha256,
          scope_manifest_path=None,expected_scopes_sha256=None):
    development_path=Path(development_path).resolve()
    pool=Path(pool).resolve();destination=Path(destination).resolve();output_directory=Path(output_directory).resolve()
    dev=read(development_path)
    date.fromisoformat(as_of)
    if dev.get("contract_sha256")!=expected_identity or canonical_hash(dev)!=expected_identity or dev.get("phase")!="development":
        raise ValueError("Development contract identity/phase differs")
    if len(dev.get("case_ids",[]))!=2 or len(set(dev["case_ids"]))!=2:
        raise ValueError("Exactly two current development cases are required")
    if any(digest(name)!=value for name,value in dev["input_sha256"].items()):
        raise ValueError("Current development inputs drifted")
    development_output=Path(dev["output_directory"]).resolve()
    if (development_output/"stopped.json").exists():
        raise ValueError("Failed development batch cannot qualify")
    entries=[]
    for cid in dev["case_ids"]:
        if not isinstance(cid,str) or not cid.replace("-","").isalnum():
            raise ValueError("Invalid development case ID")
        paths={"result":development_output/(cid+".result.json"),
               "assessment":development_output/(cid+".assessment.json"),
               "started":development_output/(cid+".started.json")}
        if not all(path.is_file() for path in paths.values()):
            raise ValueError("Two passing current development results/assessments are missing")
        original = paths["assessment"]
        adapted = destination.parent / (cid + ".lineage-assessment.json")
        before, after = read(original), read(adapted)
        expected_findings = [
            key + " = " + json.dumps(value, ensure_ascii=False)
            for key, value in before["source_findings"].items()
        ]
        if (after["original_assessment_sha256"] != digest(original)
                or Path(after["original_assessment_path"]) != original
                or after["verdict"] != before["verdict"]
                or after["result_sha256"] != before["result_sha256"]
                or after["source_findings"] != expected_findings):
            raise ValueError("Development assessment format adaptation differs")
        paths["assessment"] = adapted
        entry={"case_id":cid,"development_contract_path":str(development_path),
               "original_assessment_path":str(original),
               "development_contract_file_sha256":digest(development_path)}
        for kind,path in paths.items():
            entry[kind+"_path"]=str(path);entry[kind+"_sha256"]=digest(path)
        entries.append(entry)
    manifest_path=pool/"manifest.json";manifest=read(manifest_path)
    if digest(manifest_path)!=expected_pool_sha256 or manifest.get("pool_id")!="CQ1":
        raise ValueError("Pool differs from predeclared content identity")
    if (manifest["categories"]!=COUNTS or json.dumps(manifest["thresholds"],sort_keys=True)
            !=json.dumps({**THRESHOLDS,"critical_errors":0},sort_keys=True)):
        raise ValueError("Frozen qualification thresholds differ")
    for name,value in manifest["sha256"].items():
        if digest(inside(pool,name))!=value:
            raise ValueError("Frozen pool content changed")
    plan_manifest_path=pool/"plans-v3-coverage-manifest.json";plan_manifest=read(plan_manifest_path)
    plans_path=inside(pool,plan_manifest["plans_file"])
    if (digest(plans_path)!=expected_plans_sha256 or digest(plans_path)!=plan_manifest["sha256"]
            or digest(manifest_path)!=plan_manifest["original_content_manifest_sha256"]):
        raise ValueError("Reviewed plan/content identity changed")
    original=read(pool/"cases.json")
    roster=[{"case_id":row["case_id"],"category":row["category"]} for row in original]
    summarize(roster,{},{})
    plans=read(plans_path)
    if set(plans)!={row["case_id"] for row in roster}:
        raise ValueError("Qualification plans differ from exact roster")
    if destination.exists() or output_directory.exists() or output_directory.parent!=destination.parent:
        raise ValueError("Use fresh contract and sibling execution-output locations")
    cases={}
    inputs=dict(dev["input_sha256"])
    for row in roster:
        entry=plans[row["case_id"]]
        if entry.get("category")!=row["category"]:
            raise ValueError("Case category differs from plan")
        plan=Plan.model_validate_json(json.dumps(entry["plan"]))
        recorded = Path(entry["corpus_path"])
        if recorded.is_absolute() and not recorded.is_relative_to(pool):
            # The original Windows report directory was renamed. Resolve only
            # its exact old root and require the unchanged manifest entry.
            old_pool = pool.parent.parent / "concurrent-qualification-2026-11-06" / "cq1"
            recorded = recorded.relative_to(old_pool)
            if recorded.as_posix() not in manifest["sha256"]:
                raise ValueError("Relocated corpus is absent from the frozen manifest")
        corpus=inside(pool,recorded)
        if digest(corpus)!=plan.corpus_sha256:
            raise ValueError("Qualification corpus changed")
        cases[row["case_id"]]={k:entry[k] for k in ("plan","bindings","corpus_path","complete_required_branches") if k in entry}
        cases[row["case_id"]]["corpus_path"]=str(corpus)
        inputs[str(corpus)]=digest(corpus)
    scoped=dev.get("composition_contract")
    if scoped is not None and scoped!=CONTRACT_VERSION:
        raise ValueError("Unknown development composition contract")
    if scoped==CONTRACT_VERSION:
        if scope_manifest_path is None or expected_scopes_sha256 is None:
            raise ValueError("Scoped qualification requires a frozen scope manifest")
        for entry in dev["cases"].values():
            path=Path(entry["requested_scopes"]).resolve()
            if (dev["input_sha256"].get(str(path))!=entry["requested_scopes_sha256"]
                    or digest(path)!=entry["requested_scopes_sha256"]):
                raise ValueError("Development requested-scope input is not pinned")
            validate_scopes(Plan.model_validate_json(json.dumps(entry["plan"])),entry["bindings"],
                DisclosureScopes.model_validate_json(path.read_text(encoding="utf-8")))
        cases,scope_inputs=scoped_cases(cases,scope_manifest_path,expected_scopes_sha256,
            expected_pool_sha256,expected_plans_sha256)
        inputs.update(scope_inputs)
    elif scope_manifest_path is not None or expected_scopes_sha256 is not None:
        raise ValueError("Legacy development cannot silently adopt scoped composition")
    for path in [Path(__file__).resolve(),development_path,manifest_path,plan_manifest_path,plans_path,pool/"cases.json",
                 *[inside(pool,name) for name in manifest["sha256"]],
                 *[Path(entry[k]) for entry in entries for k in ("started_path","result_path","assessment_path","original_assessment_path")]]:
        inputs[str(path)]=digest(path)
    inherited={k:v for k,v in dev.items() if k not in {"protocol_path","protocol_sha256","prior_interruption_result_sha256"}}
    contract={**inherited,"phase":"qualification","case_ids":[row["case_id"] for row in roster],
        "cases":cases,"roster":roster,"input_sha256":dict(sorted(inputs.items())),"as_of":as_of,
        "development_case_ids":dev["case_ids"],"development_gate":{"pipeline_identity":dev["pipeline_identity"],"cases":entries},
        "output_directory":str(output_directory),"status":"prepared only; separate explicit user grant required",
        "execution_authorized":False,"purpose":"Actual twenty-case CQ1 qualification after linked current development passes",
        "category_thresholds":manifest["thresholds"],"reference_answers_sent_to_models":False,
        "qualification_protocol":{"case_attempts":20,"main_calls_total_max":80,"nemo_invocations_total_max":20,
            "seconds_per_case":180,"retries":0,"warmups":0,
            "stop":"Technical/critical/full-pass-category failure or second noncritical answerable miss closes the batch.",
            "source_review":"Exact-source support/completeness and raw/fallback/editorial distinctions before next case; final owner adjudication and bundle acceptance required."}}
    contract.pop("contract_sha256")
    if scoped==CONTRACT_VERSION:
        contract.update(requested_scope_manifest_path=str(Path(scope_manifest_path).resolve()),
            requested_scope_manifest_sha256=expected_scopes_sha256,
            authorization_reply="Authorize CQ1 scoped twenty-case qualification")
    contract["contract_sha256"]=canonical_hash(contract)
    verify_lineage(contract)  # No grant-shaped object is created for validation.
    if any(digest(name)!=value for name,value in contract["input_sha256"].items()):
        raise ValueError("Input identity changed during preparation")
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open("x",encoding="utf-8") as stream:
        json.dump(contract,stream,ensure_ascii=False,indent=2);stream.write("\n")
    return contract


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("development-contract","expected-identity","pool","destination","output-directory","as-of",
                 "expected-pool-sha256","expected-plans-sha256"):
        p.add_argument("--"+name,required=True)
    p.add_argument("--scope-manifest-path")
    p.add_argument("--expected-scopes-sha256")
    args=p.parse_args(argv)
    contract=build(args.development_contract,args.expected_identity,args.pool,args.destination,args.output_directory,args.as_of,
        expected_pool_sha256=args.expected_pool_sha256,expected_plans_sha256=args.expected_plans_sha256,
        scope_manifest_path=args.scope_manifest_path,expected_scopes_sha256=args.expected_scopes_sha256)
    print(json.dumps({"contract_sha256":contract["contract_sha256"],"execution_authorized":False,"actual_model_calls":0}))
    return 0


if __name__=="__main__":raise SystemExit(main())
