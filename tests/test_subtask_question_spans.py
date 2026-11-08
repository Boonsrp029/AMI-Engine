"""Private question-range prototype: structural coverage, never missingness proof."""
import copy

import pytest
from src.pilot._evidence import GeographySelection
from src.pilot.subtasks._question_spans import (
    QUESTION_WIRE_VERSION,question_selection_schema,question_span_context,resolve_question_selection,
)


Q="Report output and net profit in 2042."


def schema(question=Q,catalog=None,requests=None):
    requests=requests or [{"component_id":"r1","question_anchor":question}]
    return question_selection_schema({"s1":{},"s2":{}} if catalog is None else catalog,
        question,requests,GeographySelection),requests


def wire(status="partial",gap=None,evidence=None):
    return {"wire_version":QUESTION_WIRE_VERSION,"components":[{
        "component_id":"r1","status":status,"gap":gap,
        "evidence":evidence if evidence is not None else ([] if status=="missing" else ["s1"])}],
        "geography":{"status":"unresolved","value":"","evidence":[],"reason":"Not stated."}}


def test_selected_request_fragment_resolves_exactly_without_mutating_raw():
    cls,requests=schema();start=Q.index("net profit")
    raw=wire(gap={"start":start,"end":start+len("net profit")});before=copy.deepcopy(raw)
    resolved,trace=resolve_question_selection(cls,raw,Q,requests)
    assert raw==before and resolved["components"][0]["gap_anchor"]=="net profit"
    assert resolved["wire_version"]=="source-selection-v1"
    assert "gap" not in resolved["components"][0]
    assert trace[0]["membership_proven"] is True and trace[0]["semantic_missingness_proven"] is False


@pytest.mark.parametrize("question",["sales, profit?","ราคาเมื่อวาน","🛰️ café\né"])
def test_every_nonblank_character_fragment_remains_representable(question):
    cls,requests=schema(question)
    for start in range(len(question)):
        for end in range(start+1,len(question)+1):
            if not question[start:end].strip():continue
            resolved,_=resolve_question_selection(cls,wire(gap={"start":start,"end":end}),question,requests)
            assert resolved["components"][0]["gap_anchor"]==question[start:end]


@pytest.mark.parametrize("gap",[
    {"start":-1,"end":2},{"start":0,"end":999},{"start":3,"end":2},{"start":2,"end":2},
    {"start":True,"end":4},{"start":1.0,"end":4},{"start":"0","end":4},
    {"start":0},{"end":3},"A source quotation is not a question range",
])
def test_invalid_or_missing_boundaries_fail_without_repair(gap):
    cls,requests=schema()
    with pytest.raises(ValueError):resolve_question_selection(cls,wire(gap=gap),Q,requests)


def test_whitespace_only_selection_is_not_a_valid_gap():
    cls,requests=schema("one  two")
    with pytest.raises(ValueError,match="whitespace"):
        resolve_question_selection(cls,wire(gap={"start":3,"end":5}),"one  two",requests)


def test_null_states_preserve_supported_missing_and_conflict_semantics():
    cls,requests=schema()
    supported,_=resolve_question_selection(cls,wire("supported",None),Q,requests)
    missing,_=resolve_question_selection(cls,wire("missing",None),Q,requests)
    conflict,_=resolve_question_selection(cls,wire("conflicting",None,["s1","s2"]),Q,requests)
    assert supported["components"][0]["gap_anchor"]==conflict["components"][0]["gap_anchor"]==""
    assert missing["components"][0]["gap_anchor"]==Q and missing["components"][0]["evidence"]==[]
    with pytest.raises(ValueError):resolve_question_selection(cls,wire("partial",None),Q,requests)


@pytest.mark.parametrize("damage",["unknown_source","duplicate_source","unknown_component","old_anchor","missing_gap","extra_action"])
def test_identity_and_required_wire_fields_are_not_silently_fixed(damage):
    cls,requests=schema();raw=wire(gap={"start":0,"end":6});component=raw["components"][0]
    if damage=="unknown_source":component["evidence"]=["unknown"]
    elif damage=="duplicate_source":component["evidence"]=["s1","s1"]
    elif damage=="unknown_component":component["component_id"]="r9"
    elif damage=="old_anchor":component["gap_anchor"]="Invented source quote"
    elif damage=="missing_gap":component.pop("gap")
    else:raw["approve_export"]=True
    with pytest.raises(ValueError):resolve_question_selection(cls,raw,Q,requests)


def test_whole_question_offsets_preserve_shared_scope_outside_component_anchor():
    question="Report profit and revenue in 2042."
    requests=[{"component_id":"r1","question_anchor":"profit"},{"component_id":"r2","question_anchor":"revenue"}]
    cls,_=schema(question,requests=requests)
    gap={"start":question.index("2042"),"end":question.index("2042")+4}
    raw=wire(gap=gap);raw["components"].append({**raw["components"][0],"component_id":"r2"})
    resolved,_=resolve_question_selection(cls,raw,question,requests)
    assert [c["gap_anchor"] for c in resolved["components"]]==["2042","2042"]


def test_empty_catalog_and_bounded_sparse_hints_do_not_drop_offset_coverage():
    cls,requests=schema(catalog={})
    resolved,_=resolve_question_selection(cls,wire("missing",None),Q,requests)
    assert resolved["components"][0]["gap_anchor"]==Q
    question="x "*600
    context=question_span_context(question)
    assert context["length"]==1200 and len(context["hints"])==32 and context["hints_sampled"] is True
    cls,requests=schema(question)
    resolved,_=resolve_question_selection(cls,wire(gap={"start":1100,"end":1101}),question,requests)
    assert resolved["components"][0]["gap_anchor"]=="x"
    with pytest.raises(ValueError):question_span_context(question+"x")


def test_current_private_wire_does_not_silently_upgrade_legacy_selection():
    cls,requests=schema();raw=wire("supported",None)
    raw["wire_version"]="source-selection-v1"
    raw["components"][0].pop("gap");raw["components"][0]["gap_anchor"]=""
    with pytest.raises(ValueError):resolve_question_selection(cls,raw,Q,requests)


@pytest.mark.parametrize("missing_all",[False,True])
def test_callback_retains_partial_fact_or_valid_abstention_without_extra_calls(tmp_path,missing_all):
    import hashlib
    import json
    import time
    from test_subtask_generation import FixedTransport
    from src.pilot.subtasks.contracts import Plan,Subtask
    from src.pilot.subtasks.retrieval import LocalBM25Adapter
    from src.pilot.subtasks.scheduler import run_plan
    from src.pilot.subtasks.runner import ModelAccess
    from src.pilot.subtasks.generation import ConcurrentComposer
    question="Describe solar output in Peru in 2011 and provide retail gas tariffs yesterday."
    text="In Peru, solar supplied 18% of total electricity generation in 2011."
    path=tmp_path/"corpus.json";path.write_text(json.dumps([{"feed_id":"solar","clean_content":text}]),encoding="utf-8")
    plan=Plan(query=question,corpus_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),subtasks=(
        Subtask(subtask_id="s01",operation="retrieve",query="unknownalpha" if missing_all else "solar"),
        Subtask(subtask_id="s02",operation="retrieve",query="unknownbeta")))
    report=run_plan(plan,"a"*32,"b"*32,LocalBM25Adapter(path))
    class PartialTransport(FixedTransport):
        def __call__(self,stage,schema,instruction,inputs):
            result=super().__call__(stage,schema,instruction,inputs)
            if stage=="mapping" and not missing_all:
                start=question.index("retail gas tariffs yesterday")
                result["parsed"]["components"][0].update(status="partial",gap={"start":start,"end":start+len("retail gas tariffs yesterday")})
                result["raw"]=json.dumps(result["parsed"])
            return result
    transport=PartialTransport(mode="missing" if missing_all else "supported")
    access=ModelAccess(time.monotonic()+30)
    result=ConcurrentComposer(plan,{"r1":("s01","s02")},"2026-11-07",transport,
        complete_required_branches={"r1":["s01","s02"]})(report,access)
    assert access.guards==0 and not result.safety_passed
    if missing_all:
        assert result.draft["claims"]==[] and access.calls==1
        assert result.diagnostics["question_span_resolution"][0]["basis"]=="canonical_missing_request"
    else:
        assert result.draft["claims"][0]["text"]==text and access.calls==2
        assert any("retail gas tariffs yesterday" in warning for warning in result.draft["warnings"])
        assert result.diagnostics["question_span_resolution"][0]["resolved_gap_anchor"]=="retail gas tariffs yesterday"
