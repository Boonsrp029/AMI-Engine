"""Prepare the capacity diagnostic contract from the closed predecessor."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
PRIOR = ROOT.parent / "scoped-context-role-development-2026-11-18"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(value):
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main():
    contract = json.loads((PRIOR / "development-contract.json").read_bytes())
    assert datetime.now(ZoneInfo("Asia/Bangkok")).date().isoformat() == "2026-11-18"
    assert contract.pop("contract_sha256") == identity(contract)
    prior_output = Path(contract["output_directory"])
    assert json.loads((prior_output / "stopped.json").read_bytes())["case_id"] == "cq1-a40"
    assert not (prior_output / "cq1-a39.started.json").exists()
    suite = ElementTree.parse(ROOT / "offline-windows.xml").find("./testsuite")
    assert suite is not None
    assert int(suite.attrib["tests"]) > 0
    assert suite.attrib["failures"] == suite.attrib["errors"] == "0"
    changeable = {PROJECT / "src/pilot/subtasks" / name for name in
                  ("_fact_selection.py", "_request_focus.py", "_scoped_generation.py")}
    inputs = {}
    for name, old_hash in contract["input_sha256"].items():
        path = Path(name)
        current_hash = digest(path)
        if path not in changeable and current_hash != old_hash:
            raise ValueError(f"Unexpected drift in retained input {path}")
        inputs[str(path)] = current_hash
    with (ROOT / "run_case.py").open("xb") as handle:
        handle.write((PRIOR / "run_case.py").read_bytes())
    table_output = ROOT.parent / "scoped-signed-table-development-2026-11-18" / "actual-cq1"
    for path in (*prior_output.glob("cq1-a40.*.json"), prior_output / "stopped.json",
                 *table_output.glob("cq1-a39.*.raw.json"),
                 PRIOR / "development-contract.json", PRIOR / "wall-clock-cq1-a40.json",
                 ROOT / "run_case.py", ROOT / "offline-replay.py", ROOT / "offline-replay.json",
                 ROOT / "offline-windows.xml", ROOT / "pool-admission.json",
                 ROOT / "source-review-protocol.md", Path(__file__),
                 PROJECT / "tests/test_scoped_request_focus.py"):
        inputs[str(path)] = digest(path)
    contract.update(output_directory=str(ROOT / "actual-development-v1"),
        mapping_version="cq-fact-span-selection-v1-capacity-context",
        composition_version="cq-composer-v12-capacity-threshold",
        purpose="Verify complete capacity thresholds and the unchanged signed table behavior.",
        authorization_reply="Authorize scoped capacity development diagnostics",
        source_review_protocol=str(ROOT / "source-review-protocol.md"),
        source_review_protocol_sha256=digest(ROOT / "source-review-protocol.md"),
        input_sha256=dict(sorted(inputs.items())))
    contract["pipeline_identity"] = identity({
        "runtime": {name: sha for name, sha in inputs.items() if Path(name).is_relative_to(PROJECT / "src")},
        "model": contract["model_snapshot"], "settings": contract["settings"],
        "composition_contract": contract["composition_contract"], "mapping_version": contract["mapping_version"],
        "composition_version": contract["composition_version"],
    })
    contract["contract_sha256"] = identity(contract)
    with (ROOT / "development-contract.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(contract, handle, indent=2)
        handle.write("\n")
    print(contract["contract_sha256"])


if __name__ == "__main__":
    main()
