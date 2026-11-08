"""Category-gated CQ1 admission after exact, source-reviewed development results."""
import json
from pathlib import Path
from .qualification import DevelopmentLedger, digest, _write_once
from .quality_review import SourceReview, summarize


class QualificationLedger(DevelopmentLedger):
    case_count = 20

    def _verify(self):
        super()._verify()
        c = self.contract
        if [r["case_id"] for r in c["roster"]] != c["case_ids"]:
            raise ValueError("Qualification order differs from frozen roster")
        summarize(c["roster"], {}, {})  # Validate exact category denominators.
        gate = c["development_gate"]
        if gate["pipeline_identity"] != c["pipeline_identity"] or len(gate["cases"]) != 2:
            raise ValueError("Development gate does not match current pipeline")
        if [r["case_id"] for r in gate["cases"]] != c["development_case_ids"]:
            raise ValueError("Development diagnostic roster differs")
        for case in gate["cases"]:
            rp, ap = Path(case["result_path"]), Path(case["assessment_path"])
            if digest(rp) != case["result_sha256"] or digest(ap) != case["assessment_sha256"]:
                raise ValueError("Development evidence identity changed")
            r, a = json.loads(rp.read_text(encoding="utf-8")), json.loads(ap.read_text(encoding="utf-8"))
            if (r.get("technical_pass") is not True or a.get("verdict") != "pass"
                    or not a.get("source_findings") or a.get("result_sha256") != digest(rp)):
                raise ValueError("Development source gate has not passed")

    def _records(self, ids):
        attempts, reviews = {}, {}
        for cid in ids:
            rp, ap = self.output / (cid + ".result.json"), self.output / (cid + ".assessment.json")
            sp = self.output / (cid + ".started.json")
            if not rp.exists() or not ap.exists() or not sp.exists():
                raise ValueError("Prior exact-result source review is pending")
            if json.loads(sp.read_text(encoding="utf-8")).get("contract_sha256") != self.contract["contract_sha256"]:
                raise ValueError("Prior attempt belongs to a different contract")
            attempts[cid] = {**json.loads(rp.read_text(encoding="utf-8")), "result_sha256": digest(rp)}
            reviews[cid] = json.loads(ap.read_text(encoding="utf-8"))
        return attempts, reviews

    def _check_prior(self, index):
        a, r = self._records(self.contract["case_ids"][:index])
        result = summarize(self.contract["roster"], a, r)
        if result["stop"]:
            raise ValueError("Qualification source/category gate failed")

    def assess(self, case_id, assessment):
        self._verify()
        rp = self.output / (case_id + ".result.json")
        if not rp.exists() or (self.output / "stopped.json").exists():
            raise ValueError("No reviewable qualification result")
        review = SourceReview.model_validate(assessment)
        if review.result_sha256 != digest(rp):
            raise ValueError("Source review differs from exact result")
        _write_once(self.output / (case_id + ".assessment.json"), review.model_dump())
        index = self.contract["case_ids"].index(case_id)
        a, r = self._records(self.contract["case_ids"][:index+1])
        summary = summarize(self.contract["roster"], a, r)
        _write_once(self.output / (case_id + ".summary.json"), summary)
        if summary["stop"]:
            _write_once(self.output / "stopped.json", summary["stop"])
