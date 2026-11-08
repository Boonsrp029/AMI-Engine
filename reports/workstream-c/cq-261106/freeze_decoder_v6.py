"""Prepare a new bounded contract, never an execution grant."""
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_once(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def main():
    protocol = json.loads((ROOT / "diagnostic-protocol-v4.json").read_text())
    protocol.update(protocol_id="concurrent-development-v6-decoder-coverage",
        status="prepared only; execution grant absent",
        mapping_version="cq-mapper-v5-decoder-coverage",
        prior_failure_sha256=sha(ROOT / "v5-diagnostic-findings.json"),
        repair="Supported-state provenance cover prefix; every eligible span remains a choice. Partial/missing/conflict alternatives and application guard remain.",
        changes=["Private supported wire now uses a deterministic coverage prefix with optional distinct extra spans.",
                 "Shared/overlapping origins use minimal covers without duplicate forced citations.",
                 "Grammar size is separate from message context; real compatibility and latency are unverified."],
        development_freshness="Both cases are development evidence. cq-p01 has retained failed/interrupted attempts and was used for diagnosis; never count it as unseen.")
    protocol_path = ROOT / "diagnostic-protocol-v5-decoder.json"
    write_once(protocol_path, protocol)
    contract = json.loads((ROOT / "development-contract-v5.json").read_text())
    contract.update(mapping_version=protocol["mapping_version"],
        protocol_path=str(protocol_path), protocol_sha256=sha(protocol_path),
        output_directory=str(ROOT / "actual-development-v5"))
    assert not Path(contract["output_directory"]).exists()
    names = set(contract["input_sha256"])
    names.update(str(Path(name).resolve()) for name in [
        "src/pilot/subtasks/_coverage_decoder.py", "tests/test_subtask_coverage_decoder.py",
        "tests/test_subtask_request_coverage.py", "scripts/audit_concurrent_context.py"])
    names.add(str(protocol_path))
    # Bind the measured grammar resources and preservation result as well.
    names.update(str(ROOT / name) for name in ["decoder-coverage-contract.md",
        "token-budget-decoder-coverage-v5.json", "decoder-preservation-audit.json"])
    contract["input_sha256"] = {name: sha(name) for name in sorted(names)}
    identity = json.dumps(contract["input_sha256"], sort_keys=True, separators=(",", ":")).encode()
    contract["pipeline_identity"] = hashlib.sha256(identity).hexdigest()
    contract.pop("contract_sha256")
    encoded = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    contract["contract_sha256"] = hashlib.sha256(encoded).hexdigest()
    write_once(ROOT / "development-contract-v6.json", contract)
    print(json.dumps({"contract_sha256":contract["contract_sha256"],
        "input_count":len(names), "execution_authorized":False}))


if __name__ == "__main__":
    main()
