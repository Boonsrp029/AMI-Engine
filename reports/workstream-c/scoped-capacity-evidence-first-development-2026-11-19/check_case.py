import hashlib,json,sys
from pathlib import Path
from src.pilot.store import Store
d=Path(__file__).resolve().parent
cid=sys.argv[1]
def read(p): return json.loads(p.read_bytes())
def sha(b): return hashlib.sha256(b).hexdigest()
o=d/"actual-development-v1"
def artifact(s): return read(o/f"{cid}.{s}.json")
r=artifact("result")
row=r["stored_run"]
diag=row["metrics"]["composition_diagnostics"]
safe=artifact("safety")
cap=cid=="cq1-a40"
trace,=diag["application_rendered_capacity_thresholds" if cap else "application_rendered_table_rows"]
source=row["sources"][trace["source_id"]]
assert sha(source["content"].encode())==trace["content_sha256"]
assert source["url"]=="https://www.eia.gov/tools/faqs/faq.php?id=427&t=3"
excerpt=source["content"][trace["start"]:trace["end"]]
composer=json.loads(artifact("composition.raw")["raw"])
mapper=json.loads(artifact("mapping.raw")["raw"])
assert composer["claims"]==[{k:trace[k] for k in ("unit_id","component_id")}]
assert mapper["facts"][0]["alternatives"][0][0]["span_id"]==trace["span_id"]
assert row["draft"]["claims"]==[{"text":trace["text"],"source_ids":[trace["source_id"]]}]
assert safe["passed_guardrails"] and safe["validated_report"]==safe["raw_output"]==trace["text"]
assert not diag["fallback_unit_ids"] and not diag["editorial_correction"]
assert r["technical_pass"] and row["status"]=="needs_review" and row["revision"]==1
assert Store(o/f"{cid}.sqlite3").get(row["id"])["draft"]==row["draft"]
assert safe["context_sha256"]==read(d/f"offline-{cid}.safety.json")["context_sha256"]
if cap:
    assert mapper["facts"][0]["alternatives"][0][0]["context"]==[]
    assert "at least one megawatt (or 1,000 kilowatts) of total electricity generating capacity" in excerpt
    assert safe["leading_excerpt"]["text"]==excerpt
    assert all(safe["leading_excerpt"][k]==trace[k] for k in ("span_id","content_sha256","start","end","source_id"))
    expected=read(d.parent/"scoped-capacity-selection-development-2026-11-19/evidence-first/contract.json")["cases"][0]
    assert safe["context_sha256"]==sha(expected["context"].encode()) and trace["text"]==expected["report"]
    finding="EIA footnote 1 states a minimum of one megawatt or 1,000 kilowatts of total electricity generating capacity. Both units, the measure and the minimum are retained. The leading safety excerpt and full context digest match the verified standalone input."
else:
    assert "Solar thermal 3 0.1%" in " ".join(excerpt.split())
    assert safe["leading_excerpt"] is None
    assert trace["text"]=="In 2023, the table gives Solar thermal generation in Billion kWh as 3 and its share of total utility-scale electricity generation as 0.1%."
    finding="The EIA 2023 U.S. utility-scale generation table gives Solar thermal as 3 billion kWh and 0.1% of the total. Both requested fields are bound to the same row. Safety retained full evidence without a leading excerpt."
assessment={"author":"assistant","verdict":"pass","result_sha256":sha((o/f"{cid}.result.json").read_bytes()),"source_findings":[finding,f"Verified {source['url']} at offsets {trace['start']} to {trace['end']} in {trace['source_id']}.","Raw composer selected the bound unit, application rendered its cited sentence, no fallback or editorial change, NeMo passed and SQLite retained reviewable revision 1."]}
with (d/f"assessment-{cid}.json").open("x",encoding="utf-8") as f: json.dump(assessment,f,indent=2)
print(finding)
