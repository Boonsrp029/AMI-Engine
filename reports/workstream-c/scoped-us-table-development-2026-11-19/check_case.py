import hashlib,json,re,sys
from pathlib import Path
from src.pilot.store import Store
root=Path("reports/workstream-c/scoped-us-table-development-2026-11-19")
out=root/"actual-development-v1"
cid=sys.argv[1]
def read(s): return json.loads((out/f"{cid}.{s}.json").read_bytes())
def sha(s): return hashlib.sha256(s).hexdigest()
r=read("result"); row=r["stored_run"]; diag=row["metrics"]["composition_diagnostics"]
trace,=diag["application_rendered_table_rows"]; scope=trace["geographic_evidence"]; source=row["sources"][trace["source_id"]]
assert scope["source_id"]==trace["source_id"] and sha(source["content"].encode())==trace["content_sha256"]==scope["content_sha256"]
assert source["content"][scope["start"]:scope["end"]]==scope["text"]=="U.S. utility-scale electricity generation by source, amount, and share of total in 2023"
assert source["url"]=="https://www.eia.gov/tools/faqs/faq.php?id=427&t=3"
label,values={"cq1-a41":("Pumped storage hydropower","-6 -0.1%"),"cq1-a42":("Photovoltaic","162 3.9%")}[cid]
excerpt=" ".join(source["content"][trace["start"]:trace["end"]].split())
assert re.search(re.escape(label)+r" (?:4 )?"+re.escape(values),excerpt)
assert "U.S. "+label in trace["text"] and "total U.S. utility-scale electricity generation" in trace["text"]
assert json.loads(read("composition.raw")["raw"])["claims"]==[{k:trace[k] for k in ("unit_id","component_id")}]
assert json.loads(read("mapping.raw")["raw"])["facts"][0]["alternatives"][0][0]["span_id"]==trace["span_id"]
assert row["draft"]["claims"]==[{"text":trace["text"],"source_ids":[trace["source_id"]]}]
assert not diag["fallback_unit_ids"] and not diag["editorial_correction"]
safe=read("safety")
assert safe["passed_guardrails"] and safe["validated_report"]==trace["text"] and safe["leading_excerpt"] is None
assert r["technical_pass"] and row["status"]=="needs_review" and row["revision"]==1
assert Store(out/f"{cid}.sqlite3").get(row["id"])["draft"]==row["draft"]
a={"author":"assistant","verdict":"pass","result_sha256":sha((out/f"{cid}.result.json").read_bytes()),"source_findings":[
 f"Source {source['url']} table row at offsets {trace['start']} to {trace['end']} contains {label}, {values} in billion kWh and percent of total U.S. utility-scale generation for 2023. The attached heading at offsets {scope['start']} to {scope['end']} establishes explicit U.S. scope for the same table.",
 "Raw selection chose the bound row. The application retained sign, year, unit, geography and denominator without a fallback or editorial change. Final NeMo passed with standard full evidence, and SQLite retained exact revision 1 for review."]}
with (root/f"assessment-{cid}.json").open("x",encoding="utf-8") as stream: json.dump(a,stream,indent=2)
print(trace["text"])
