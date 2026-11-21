"""Immutable admission ledger, not an authorization issuer or inference client.

The caller must establish a real matching user grant outside this module. A
grant-shaped JSON document alone is not evidence of that user authorization.
"""
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_once(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


class DevelopmentLedger:
    case_count = 2
    def __init__(self, output, contract, grant):
        self.output = Path(output)
        self.contract = contract
        self.grant = grant

    def _verify(self):
        c, g = self.contract, self.grant
        encoded = json.dumps({k:v for k,v in c.items() if k != "contract_sha256"}, sort_keys=True, separators=(",", ":")).encode()
        if hashlib.sha256(encoded).hexdigest() != c["contract_sha256"]:
            raise ValueError("Contract identity mismatch")
        if len(c["case_ids"]) != self.case_count:
            raise ValueError("Ledger case count differs from the declared phase")
        if not isinstance(g, dict) or g.get("contract_sha256") != c["contract_sha256"]:
            raise ValueError("No matching execution grant")
        if not isinstance(g.get("authorization_reference"), str) or not g["authorization_reference"].strip():
            raise ValueError("User authorization reference is required")
        if g.get("case_ids") != c["case_ids"] or g.get("limits") != c["limits"]:
            raise ValueError("Grant scope or limits differ")
        if len(c["case_ids"]) != len(set(c["case_ids"])) or not c["case_ids"]:
            raise ValueError("Invalid case roster")
        if any(not isinstance(cid, str) or not cid.replace("-", "").isalnum() for cid in c["case_ids"]):
            raise ValueError("Invalid case identifier")
        if c["limits"] != {"main_calls_per_case": 4, "nemo_per_case": 1,
                            "seconds_per_case": 180, "retries": 0}:
            raise ValueError("Unsupported execution bounds")
        for name, expected in c["input_sha256"].items():
            if digest(name) != expected:
                raise ValueError("Frozen input identity changed")

    def start(self, case_id):
        self._verify()
        if case_id not in self.contract["case_ids"]:
            raise ValueError("Case is not authorized")
        self.output.mkdir(parents=True, exist_ok=True)
        if (self.output / "stopped.json").exists():
            raise ValueError("Batch is closed")
        index = self.contract["case_ids"].index(case_id)
        self._check_prior(index)
        # Exclusive attempt marker makes interrupted/failed starts non-repeatable.
        _write_once(self.output / (case_id + ".started.json"), {
            "case_id": case_id, "contract_sha256": self.contract["contract_sha256"]})

    def _check_prior(self, index):
        for prior in self.contract["case_ids"][:index]:
            path = self.output / (prior + ".assessment.json")
            if not path.exists():
                raise ValueError("Prior source review is pending")
            assessment = json.loads(path.read_text(encoding="utf-8"))
            result_path = self.output / (prior + ".result.json")
            started_path = self.output / (prior + ".started.json")
            if (not result_path.exists() or not started_path.exists()
                    or assessment.get("result_sha256") != digest(result_path)
                    or json.loads(started_path.read_text(encoding="utf-8")).get("contract_sha256") != self.contract["contract_sha256"]):
                raise ValueError("Prior assessment lacks exact attempt/result provenance")
            if assessment["verdict"] != "pass":
                raise ValueError("Development gate failed")

    def finish(self, case_id, result):
        if not (self.output / (case_id + ".started.json")).exists():
            raise ValueError("Case has not started")
        try:
            self._verify()
        except Exception as exc:
            result = {**result, "technical_pass": False, "identity_failure": type(exc).__name__}
        _write_once(self.output / (case_id + ".result.json"), result)
        valid = (result.get("technical_pass") is True
                 and type(result.get("main_calls")) is int and 0 <= result["main_calls"] <= 4
                 and type(result.get("nemo_invocations")) is int and 0 <= result["nemo_invocations"] <= 1
                 and type(result.get("elapsed_seconds")) in (int, float)
                 and 0 <= result["elapsed_seconds"] <= 180)
        if not valid:
            _write_once(self.output / "stopped.json", {"case_id": case_id, "reason": "technical or budget failure"})
            raise ValueError("Attempt failed its execution gate")

    def assess(self, case_id, assessment):
        self._verify()
        result_path = self.output / (case_id + ".result.json")
        if not result_path.exists() or (self.output / "stopped.json").exists():
            raise ValueError("No reviewable successful execution")
        if assessment.get("result_sha256") != digest(result_path):
            raise ValueError("Assessment does not bind exact result")
        if assessment.get("verdict") not in {"pass", "fail"} or not assessment.get("source_findings"):
            raise ValueError("Explicit source adjudication is required")
        _write_once(self.output / (case_id + ".assessment.json"), assessment)
        if assessment["verdict"] == "fail":
            _write_once(self.output / "stopped.json", {"case_id": case_id, "reason": "source gate failure"})
