"""Freeze a prospective development contract without inference or execution grant."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
PREVIOUS = ROOT.parent / "scoped-table-boundary-development-2026-11-18"


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    contract = read(PREVIOUS / "development-contract.json")
    qualification = read(PREVIOUS / "qualification-contract.json")
    ids = ["cq1-a38", "cq1-a37"]
    script = (PREVIOUS / "run_case.py").read_text(encoding="utf-8")
    script = script.replace("cq1-a28", "__FIRST__").replace("cq1-a27", "cq1-a37").replace("__FIRST__", "cq1-a38")
    with (ROOT / "run_case.py").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(script)
    inputs = {str(Path(path).resolve()): digest(path) for path in contract["input_sha256"]}
    for path in (PROJECT / "src").rglob("*.py"):
        inputs[str(path.resolve())] = digest(path)
    for cid in ids:
        case = qualification["cases"][cid]
        for path in (case["corpus_path"], case["requested_scopes"],
                     PREVIOUS / "actual-cq1" / f"{cid}.result.json"):
            inputs[str(Path(path).resolve())] = digest(path)
    for name in ("run_case.py", "freeze-development.py", "offline-replay.py", "offline-replay.json",
                 "offline-repair-contract.md", "source-review-protocol.md"):
        inputs[str(ROOT / name)] = digest(ROOT / name)
    contract.update(case_ids=ids, cases={cid: qualification["cases"][cid] for cid in ids},
        as_of="2026-11-18", output_directory=str(ROOT / "actual-development-v1"),
        mapping_version="cq-fact-span-selection-v1-signed-table-rows",
        purpose="Consumed signed-table development followed by existing-row regression; no qualification.",
        authorization_reply="Authorize scoped signed-table development diagnostics",
        source_review_protocol=str(ROOT / "source-review-protocol.md"),
        source_review_protocol_sha256=digest(ROOT / "source-review-protocol.md"),
        input_sha256=dict(sorted(inputs.items())))
    contract["pipeline_identity"] = canonical({"runtime": {path: sha for path, sha in inputs.items()
        if Path(path).is_relative_to(PROJECT / "src")}, "model": contract["model_snapshot"],
        "settings": contract["settings"], "composition_contract": contract["composition_contract"],
        "mapping_version": contract["mapping_version"]})
    contract["pipeline_identity_method"] = "canonical runtime Python hashes, model, settings and private composition/mapping versions"
    contract.pop("contract_sha256", None)
    contract["contract_sha256"] = canonical(contract)
    with (ROOT / "development-contract.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(contract, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"contract_sha256": contract["contract_sha256"], "frozen_inputs": len(inputs),
                      "execution_authorized": False}))


if __name__ == "__main__":
    main()
