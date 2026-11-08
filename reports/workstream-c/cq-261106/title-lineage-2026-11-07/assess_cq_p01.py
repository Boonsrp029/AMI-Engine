"""Retain the assistant's reviewed first-case findings and read-only DB evidence."""
import hashlib
import json
from pathlib import Path
import sqlite3


ROOT=Path(__file__).resolve().parent


def main():
    folder=ROOT/"actual-development-v7"
    path=folder/"cq-p01.result.json"
    result=json.loads(path.read_text(encoding="utf-8"));row=result["stored_run"]
    assert result["technical_pass"] is True and row["status"]=="needs_review" and row["revision"]==1
    assert result["main_calls"]==2 and result["nemo_invocations"]==1
    assert row["draft"]["title"]=="Analyst research brief" and row["draft"]["warnings"]==[]
    expected=[("cq-observed","In Canada, observed electricity demand grew 5.7% in 2016."),
              ("cq-projected","In Japan, electricity demand is projected to grow 2.6% annually through 2036.")]
    assert [(c["source_ids"][0],c["text"]) for c in row["draft"]["claims"]]==expected
    assert all(row["sources"][sid]["content"]==text for sid,text in expected)
    diag=row["metrics"]["composition_diagnostics"]
    assert diag["fallback_unit_ids"]==[] and diag["editorial_correction"] is False
    assert len(row["metrics"]["composition_provenance"])==2
    safety=json.loads((folder/"cq-p01.safety.json").read_text(encoding="utf-8"))
    assert safety["passed_guardrails"] is True
    wall=json.loads((ROOT/"wall-clock-cq-p01.json").read_text(encoding="utf-8"))
    assert wall["timed_out"] is False and wall["elapsed_seconds"]<=180
    db=sqlite3.connect((folder/"cq-p01.sqlite3").resolve().as_uri()+"?mode=ro",uri=True)
    stored=db.execute("SELECT status,revision,draft FROM runs WHERE id=?",(row["id"],)).fetchone()
    assert stored[:2]==("needs_review",1) and json.loads(stored[2])==row["draft"]
    counts={name:db.execute("SELECT COUNT(*) FROM "+name).fetchone()[0] for name in ("reviews","exports")}
    db.close();assert counts=={"reviews":0,"exports":0}
    review={"result_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"verdict":"pass",
        "assessor":"assistant; awaiting owner source/wording adjudication",
        "source_findings":[
            "cq-observed exact quotation supports Canada, observed demand growth5.7percent and2016; no relative comparison introduced.",
            "cq-projected exact quotation supports Japan, projected demand growth2.6percentannually through2036; observation/projection and unit identities retained.",
            "Both raw/final claims are complete for the supplied synthetic question, no fallback/editorial correction, neutral two-country title and no misleading warning.",
            "One actual NeMo invocation passed; reopened SQLite contains revision1 needs_review, exact draft/sources/lineage, zero reviews/exports."
        ],"raw_supported":True,"raw_complete":True,"final_supported":True,"final_complete":True,
        "title_scope_pass":True,"safety_pass":True,"persistence_pass":True,"fallback_used":False,
        "owner_verdict":"pending","owner_reference":"","synthetic_development_only":True,
        "wall_elapsed_seconds":wall["elapsed_seconds"],"application_elapsed_seconds":result["elapsed_seconds"],
        "read_only_database_check":counts}
    with (ROOT/"source-review-cq-p01.json").open("x",encoding="utf-8") as stream:
        json.dump(review,stream,indent=2);stream.write("\n")
    print(json.dumps({"case":"cq-p01","assistant_source_verdict":"pass","persistence_reopened":True,
                      "owner_verdict":"pending","reviews_exports":counts}))


if __name__=="__main__":main()
