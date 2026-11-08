"""Offline-only future CQ1 compiler. Does not issue grants or start attempts."""
import argparse
import json
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[4]))

from src.pilot.subtasks._development_lineage import canonical_hash, verify_lineage
from src.pilot.subtasks.contracts import Plan
from src.pilot.subtasks.qualification import digest
from src.pilot.subtasks.quality_review import COUNTS, THRESHOLDS, summarize


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def inside(root,name):
    path=(Path(root)/name).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError("Pool locator leaves its frozen root")
    return path


def build(development_path,expected_identity,pool,destination,output_directory,as_of,*,expected_pool_sha256,expected_plans_sha256):
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
        entry={"case_id":cid,"development_contract_path":str(development_path),
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
        corpus=inside(pool,entry["corpus_path"])
        if digest(corpus)!=plan.corpus_sha256:
            raise ValueError("Qualification corpus changed")
        cases[row["case_id"]]={k:entry[k] for k in ("plan","bindings","corpus_path","complete_required_branches") if k in entry}
        inputs[str(corpus)]=digest(corpus)
    for path in [Path(__file__).resolve(),development_path,manifest_path,plan_manifest_path,plans_path,pool/"cases.json",
                 *[inside(pool,name) for name in manifest["sha256"]],
                 *[Path(entry[k]) for entry in entries for k in ("started_path","result_path","assessment_path")]]:
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
    args=p.parse_args(argv)
    contract=build(args.development_contract,args.expected_identity,args.pool,args.destination,args.output_directory,args.as_of,
        expected_pool_sha256=args.expected_pool_sha256,expected_plans_sha256=args.expected_plans_sha256)
    print(json.dumps({"contract_sha256":contract["contract_sha256"],"execution_authorized":False,"actual_model_calls":0}))
    return 0


if __name__=="__main__":raise SystemExit(main())
