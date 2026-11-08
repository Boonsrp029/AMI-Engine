"""Concurrent title metadata coverage; no model or semantic-judge calls."""
import copy
import hashlib
import time

import pytest
from test_subtask_request_coverage import fixture as retrieval_fixture, CoverageTransport

from src.pilot._evidence import EvidenceMap
from src.pilot.subtasks._title_scope import qualify_title
from src.pilot.subtasks.generation import ConcurrentComposer
from src.pilot.subtasks.runner import ModelAccess


def records(second="In Finland, output is projected to grow 3.8% through 2043.", same_document=False):
    content={"past":"In Peru, observed output grew 6.2% in 2011.","other":second}
    return {sid:{"source_id":sid,"content":text,"content_sha256":hashlib.sha256(text.encode()).hexdigest(),
        "corpus_sha256":"a"*64,"doc_name":"shared.pdf" if same_document else sid+".pdf",
        "url":"https://example.test/shared.pdf" if same_document else "https://example.test/"+sid,
        "published":"2025-01-01"} for sid,text in content.items()}


def values(sources,period=""):
    mapping=EvidenceMap.model_validate({"geography":"Peru","period":period,"components":[{
        "component_id":"r1","question_anchor":"Compare output","status":"supported",
        "short_answer":" ".join(s["content"] for s in sources.values()),
        "evidence":[{"source_id":sid,"quote":s["content"]} for sid,s in sources.items()]}]})
    suffix=", "+period if period else ""
    draft={"title":"Analyst research brief (Peru"+suffix+")",
        "claims":[{"text":s["content"],"source_ids":[sid]} for sid,s in sources.items()],"warnings":[]}
    return mapping,draft


def test_partial_geography_is_removed_without_changing_claims_or_mapping():
    sources=records();mapping,draft=values(sources);original=copy.deepcopy(draft)
    projected,diag=qualify_title(draft,"Analyst research brief",mapping,sources)
    assert projected["title"]=="Analyst research brief"
    assert projected["claims"]==original["claims"] and projected["warnings"]==[]
    assert draft==original and mapping.geography=="Peru"
    assert diag["status"]=="suppressed_partial_geography"
    assert diag["semantic_applicability_proven"] is False


def test_common_literal_geography_keeps_title():
    sources=records("In Peru, output is projected to grow 3.8% through 2043.")
    mapping,draft=values(sources)
    result,diag=qualify_title(draft,"Analyst research brief",mapping,sources)
    assert result==draft and diag["status"]=="retained_literal_common_geography"


def test_same_pinned_document_context_is_disclosed_not_entailment():
    sources=records("Output is projected to grow 3.8% through 2043.",True)
    mapping,draft=values(sources)
    result,diag=qualify_title(draft,"Analyst research brief",mapping,sources)
    assert result["title"]==draft["title"] and len(result["warnings"])==1
    assert "verify its applicability" in result["warnings"][0]
    assert diag["status"]=="retained_document_context_requires_review"


def test_same_document_cannot_override_an_explicit_other_location():
    sources=records(same_document=True);mapping,draft=values(sources)
    result,diag=qualify_title(draft,"Analyst research brief",mapping,sources)
    assert result["title"]=="Analyst research brief" and result["warnings"]==[]
    assert diag["evidence_coverage"][1]["basis"]=="different_explicit_locative"


def test_unrelated_document_does_not_inherit_geography():
    sources=records("Output is projected to grow 3.8% through 2043.")
    mapping,draft=values(sources)
    result,_=qualify_title(draft,"Analyst research brief",mapping,sources)
    assert result["title"]=="Analyst research brief"


def test_removing_geography_preserves_the_existing_period_suffix():
    sources=records("In Finland, observed output grew 3.8% in 2011.")
    mapping,draft=values(sources,"2011")
    result,_=qualify_title(draft,"Analyst research brief",mapping,sources)
    assert result["title"]=="Analyst research brief (2011)"


@pytest.mark.parametrize("damage",["hash","offset","quote","value"])
def test_invalid_resolved_geography_is_not_silently_used(tmp_path,damage):
    sources=records();mapping,draft=values(sources)
    source=sources["past"]
    span={"source_id":"past","content_sha256":source["content_sha256"],
          "start":0,"end":len(source["content"]),"quote":source["content"]}
    resolution={"status":"known","value":"Peru","evidence":[span]}
    if damage=="hash":span["content_sha256"]="f"*64
    elif damage=="offset":span["end"]-=1
    elif damage=="quote":span["quote"]="Invented context"
    else:resolution["value"]="Finland"
    with pytest.raises(ValueError):
        qualify_title(draft,"Analyst research brief",mapping,sources,resolution)


def test_actual_callback_scope_correction_is_before_safety_and_keeps_raw_resolution(tmp_path):
    plan,report=retrieval_fixture(tmp_path)
    class KnownFirstCountry(CoverageTransport):
        def __call__(self,stage,schema,instruction,inputs):
            response=super().__call__(stage,schema,instruction,inputs)
            if stage=="mapping":
                response["parsed"]["geography"]={"status":"known","value":"Portugal",
                    "evidence":[inputs["evidence"][0]["spans"][0]["span_id"]],"reason":""}
            return response
    access=ModelAccess(time.monotonic()+30)
    result=ConcurrentComposer(plan,{"r1":("s01","s02")},"2026-11-07",KnownFirstCountry("full"),
        complete_required_branches={"r1":["s01","s02"]})(report,access)
    assert result.draft["title"]=="Analyst research brief"
    assert "Portugal" in result.draft["claims"][0]["text"] and "Sweden" in result.draft["claims"][1]["text"]
    assert result.diagnostics["geography_resolution"]["value"]=="Portugal"
    assert result.diagnostics["title_geography"]["status"]=="suppressed_partial_geography"
    assert access.calls==2 and access.guards==0 and result.safety_passed is False


def test_external_exact_document_context_can_qualify_title_with_review_warning():
    sources=records("Output is projected to grow 3.8% through 2043.",True)
    sources["past"]["content"]="Observed output grew 6.2% in 2011."
    sources["past"]["content_sha256"]=hashlib.sha256(sources["past"]["content"].encode()).hexdigest()
    mapping,draft=values(sources)
    text="In Peru, this report describes public regional output."
    context={**sources["past"],"source_id":"context","content":text,"content_sha256":hashlib.sha256(text.encode()).hexdigest()}
    sources["context"]=context
    resolution={"status":"known","value":"Peru","evidence":[{"source_id":"context",
        "content_sha256":context["content_sha256"],"start":0,"end":len(text),"quote":text}]}
    result,diag=qualify_title(draft,"Analyst research brief",mapping,sources,resolution)
    assert result["title"]=="Analyst research brief (Peru)"
    assert len(result["warnings"])==1 and "verify its applicability" in result["warnings"][0]
    assert all(row["basis"]=="same_pinned_document_context" for row in diag["evidence_coverage"])
    assert diag["semantic_applicability_proven"] is False


def test_two_countries_in_one_source_still_prevent_single_country_title():
    sources=records();mapping,draft=values(sources)
    first=sources["past"]["content"];second=sources["other"]["content"]
    joined=first+" "+second
    sources={"past":{**sources["past"],"content":joined,"content_sha256":hashlib.sha256(joined.encode()).hexdigest()}}
    mapping.components[0].evidence[1].source_id="past"
    result,diag=qualify_title(draft,"Analyst research brief",mapping,sources)
    assert result["title"]=="Analyst research brief"
    assert diag["evidence_coverage"][1]["basis"]=="different_explicit_locative"


def test_unexpected_title_format_is_not_silently_rewritten():
    sources=records();mapping,draft=values(sources)
    draft["title"]="Unexpected title outside the projection contract"
    with pytest.raises(ValueError,match="Unexpected title projection"):
        qualify_title(draft,"Analyst research brief",mapping,sources)
