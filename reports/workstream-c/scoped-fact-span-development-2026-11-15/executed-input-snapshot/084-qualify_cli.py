"""Default offline verification. Actual attempts require externally established grants.

Do not mint grant files from this command. Actual user authorization is an
operator prerequisite; a JSON document alone cannot establish it.
"""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from .qualification import DevelopmentLedger, digest
from .qualification_phase import QualificationLedger


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--mode", choices=["verify", "attempt", "assess"], default="verify")
    parser.add_argument("--grant", type=Path)
    parser.add_argument("--case")
    parser.add_argument("--assessment", type=Path)
    args = parser.parse_args(argv)
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    encoded = json.dumps({k:v for k,v in contract.items() if k != "contract_sha256"},
                         sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != contract["contract_sha256"]:
        raise ValueError("Contract identity mismatch")
    if any(digest(name) != expected for name, expected in contract["input_sha256"].items()):
        raise ValueError("Frozen input identity changed")
    if args.mode == "verify":
        print(json.dumps({"status":"verified inputs only; no inference", "contract_sha256":contract["contract_sha256"],
                          "case_ids":contract["case_ids"], "execution_authorized":False}))
        return 0
    if args.grant is None or args.case is None:
        parser.error("Attempt/assessment requires an applicable grant and explicit case")
    grant = json.loads(args.grant.read_text(encoding="utf-8"))
    cls = DevelopmentLedger if contract["phase"] == "development" else QualificationLedger
    ledger = cls(contract["output_directory"], contract, grant)
    if args.mode == "assess":
        if args.assessment is None:
            parser.error("Source assessment file is required")
        ledger.assess(args.case, json.loads(args.assessment.read_text(encoding="utf-8")))
        return 0
    if contract["as_of"] != datetime.now(ZoneInfo("Asia/Bangkok")).date().isoformat():
        raise ValueError("Attempt date differs from frozen as_of; re-freeze before requesting a new grant")
    from src.pilot._model_identity import verify_model
    from .context_gate import BoundedTransport
    from .generation import OllamaStructuredTransport
    from .qualification_runner import LocalSafety, execute_development
    snapshot = contract["model_snapshot"]
    transport = BoundedTransport(OllamaStructuredTransport(snapshot["model"]), snapshot,
        contract["tokenizer_path"], contract["tokenizer_sha256"])
    safety = LocalSafety(contract["cases"][args.case]["plan"]["query"], snapshot["model"],
        contract["output_directory"], args.case, snapshot)
    execute_development(ledger, args.case, transport, safety, verify_model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
