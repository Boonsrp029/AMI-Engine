"""Prepare a fresh two-case contract after offline repairs; never mint a grant."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from src.pilot.subtasks._development_lineage import runtime_inputs


ROOT=Path(__file__).resolve().parent
EVIDENCE=ROOT.parent
AS_OF="2026-11-07"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",", ":"),allow_nan=False).encode()


def write(path,value):
    with path.open("x",encoding="utf-8") as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write("\n")


def main():
    base=json.loads((EVIDENCE/"development-contract-v6.json").read_text(encoding="utf-8"))
    protocol=json.loads((EVIDENCE/"diagnostic-protocol-v5-decoder.json").read_text(encoding="utf-8"))
    protocol.update(protocol_id="concurrent-development-v7-title-lineage",status="prepared; new explicit grant required",
        as_of=AS_OF,composition_version="cq-composer-v2-unit-local",title_scope_version="cq-title-scope-v1",
        purpose="Actual integrated local two-case generation, final title scope, safety and persisted draft after the retained raw composer pass and offline repairs",
        source_review="Preserve original development criteria. Record raw and final support/completeness separately, fallback use, final title scope, source/unit lineage, missing evidence and safety/publication. No editorial rescue or retrospective regrade.",
        changes=["Concurrent title label needs selected-quote coverage or disclosed pinned-document context; partial geographic suffix is suppressed before safety.",
                 "Qualification admission binds retained development contract/start/result/source records and current runtime/model/settings; no CQ1 admission is authorized.",
                 "As-of date is newly captured as2026-11-07. Questions/corpus bytes remain unchanged; dated absence is assessed relative to this captured date."],
        prior_failure_sha256=sha(EVIDENCE/"unit-local-composer-v2/result-assessment.json"),
        freshness="Consumed synthetic development evidence; both two-case protocol and original20case quality gates remain required. The composer-only pass does not replace workflow qualification.")
    protocol["case_acceptance"]["cq-p01"].append("Final title does not apply a single-country label to the two-country brief; per-claim geography remains explicit.")
    protocol_path=ROOT/"diagnostic-protocol-v7.json";write(protocol_path,protocol)
    inputs={name:sha(name) for name in base["input_sha256"]}
    inputs.update(runtime_inputs())
    for name in ("scripts/_concurrent_composer_capture.py","scripts/concurrent_composer_check.py",
                 "scripts/_mapper_transport.py","scripts/_llama_token_count.py",
                 "tests/_qualification_fixtures.py","tests/test_subtask_development_lineage.py",
                 "tests/test_subtask_title_scope.py","tests/test_concurrent_composer_check.py",
                 "tests/test_concurrent_composer_capture.py","tests/test_subtask_composition_instruction.py"):
        inputs[str(Path(name).resolve())]=sha(name)
    for path in (protocol_path,ROOT/"offline-retained-response-replay.json",ROOT/"engineering-report.md"):
        inputs[str(path)]=sha(path)
    runtime=runtime_inputs()
    identity={"runtime_inputs":runtime,"model_snapshot":base["model_snapshot"],"settings":base["settings"]}
    contract={**base,"as_of":AS_OF,"input_sha256":dict(sorted(inputs.items())),
        "pipeline_identity":hashlib.sha256(canonical(identity)).hexdigest(),
        "pipeline_identity_method":"sha256(canonical(runtime_inputs,model_snapshot,settings)); case/corpus identity remains separately pinned",
        "composition_version":"cq-composer-v2-unit-local","title_scope_version":"cq-title-scope-v1",
        "output_directory":str(ROOT/"actual-development-v7"),"protocol_path":str(protocol_path),
        "protocol_sha256":sha(protocol_path),"purpose":protocol["purpose"]}
    assert not Path(contract["output_directory"]).exists()
    for case in contract["cases"].values():
        assert sha(case["corpus_path"])==case["plan"]["corpus_sha256"]
    contract.pop("contract_sha256")
    contract["contract_sha256"]=hashlib.sha256(canonical(contract)).hexdigest()
    write(ROOT/"development-contract-v7.json",contract)
    write(ROOT/"runtime-identity-v7.json",identity)
    print(json.dumps({"contract_sha256":contract["contract_sha256"],"input_files":len(inputs),
        "runtime_files":len(runtime),"as_of":AS_OF,"execution_authorized":False}))


if __name__=="__main__":main()
