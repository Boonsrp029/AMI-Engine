"""Different development facts; fixed responses do not prove semantic quality."""
import hashlib
import json
import time
import pytest
from test_subtask_generation import FixedTransport
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.scheduler import run_plan
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.generation import ConcurrentComposer
from src.pilot.subtasks.runner import ModelAccess


def fixture(tmp_path, question=None):
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps([
        {"feed_id":"portugal", "clean_content":"In Portugal, observed electricity demand grew 9.1% in 2013."},
        {"feed_id":"sweden", "clean_content":"In Sweden, electricity demand is projected to grow 4.8% through 2041."},
    ]))
    p = Plan(query=question or "Compare observed electricity demand in Portugal in 2013 with projected electricity demand in Sweden through 2041.",
        corpus_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), subtasks=(
        Subtask(subtask_id="s01",operation="retrieve",query="observed"),
        Subtask(subtask_id="s02",operation="retrieve",query="projected")))
    return p, run_plan(p,"a"*32,"b"*32,LocalBM25Adapter(path))


class CoverageTransport(FixedTransport):
    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.coverage_input = None

    def __call__(self, stage, schema, instruction, inputs):
        r = super().__call__(stage,schema,instruction,inputs)
        if stage == "mapping":
            self.coverage_input = inputs.get("complete_required_branches")
            if self.mode != "full":
                c = r["parsed"]["components"][0]
                c["evidence"] = c["evidence"][:1]
                if self.mode == "partial":
                    c.update(status="partial",gap_anchor="projected electricity demand in Sweden through 2041")
        return r


def execute(tmp_path, mode, requirements):
    p,r = fixture(tmp_path)
    transport = CoverageTransport(mode)
    access = ModelAccess(time.monotonic()+30)
    composer = ConcurrentComposer(p,{"r1":("s01","s02")},"2026-11-06",transport,
                                  complete_required_branches=requirements)
    return composer, r, transport, access


def test_supported_comparison_cannot_omit_declared_branch(tmp_path):
    c,r,t,a = execute(tmp_path,"omit",{"r1":["s01","s02"]})
    # The decoder now rejects this incomplete supported wire before resolution.
    with pytest.raises(ValueError,match="CoveredSourceSelection"):c(r,a)
    assert t.stages == ["mapping"] and a.calls == 1 and a.guards == 0


def test_full_selection_retains_both_branch_origins(tmp_path):
    c,r,t,a = execute(tmp_path,"full",{"r1":["s01","s02"]})
    result = c(r,a)
    assert t.coverage_input == {"r1":["s01","s02"]}
    assert {o["subtask_id"] for p in result.provenance for o in p["origins"]} == {"s01","s02"}
    assert result.diagnostics["requested_branch_coverage"]["r1"]["unselected_branches"] == []


def test_partial_retains_supported_fact_and_unselected_coverage_disclosure(tmp_path):
    c,r,t,a = execute(tmp_path,"partial",{"r1":["s01","s02"]})
    result = c(r,a)
    assert len(result.draft["claims"]) == 1 and "Portugal" in result.draft["claims"][0]["text"]
    assert any("s02" in warning and "does not establish absence" in warning for warning in result.draft["warnings"])
    assert result.diagnostics["requested_branch_coverage"]["r1"]["status"] == "partial"


@pytest.mark.parametrize("requirements", [{"unknown":["s01"]},{"r1":["s05"]},{"r1":[]},{"r1":["s01","s01"]}])
def test_invalid_coverage_contract_never_calls_model(tmp_path,requirements):
    c,r,t,a = execute(tmp_path,"full",requirements)
    with pytest.raises(ValueError):c(r,a)
    assert t.stages == [] and a.calls == 0


def test_legacy_unspecified_policy_remains_opt_in(tmp_path):
    c,r,t,a = execute(tmp_path,"omit",None)
    result = c(r,a)
    assert len(result.draft["claims"]) == 1 and result.diagnostics["requested_branch_coverage"] == {}


def test_context_branch_is_not_forced_into_answer_citations(tmp_path):
    p,r = fixture(tmp_path,"What was observed electricity demand growth in Portugal in 2013?")
    transport = CoverageTransport("omit")
    result = ConcurrentComposer(p,{"r1":("s01","s02")},"2026-11-06",transport,
        complete_required_branches={"r1":["s01"]})(r,ModelAccess(time.monotonic()+30))
    assert result.draft["claims"][0]["source_ids"] == ["portugal"]
    assert result.diagnostics["requested_branch_coverage"]["r1"]["unselected_branches"] == []


def test_shared_source_keeps_both_origins_without_claiming_independence(tmp_path):
    from dataclasses import replace
    from src.pilot.subtasks.scheduler import aggregate
    p,r = fixture(tmp_path,"What was observed electricity demand growth in Portugal in 2013?")
    results = (r.results[0], r.results[1].model_copy(update={"sources": r.results[0].sources}))
    r = replace(r,results=results,sources=aggregate(results))
    result = ConcurrentComposer(p,{"r1":("s01","s02")},"2026-11-06",CoverageTransport("full"),
        complete_required_branches={"r1":["s01","s02"]})(r,ModelAccess(time.monotonic()+30))
    assert {o["subtask_id"] for o in result.provenance[0]["origins"]} == {"s01","s02"}
    assert result.diagnostics["requested_branch_coverage"]["r1"]["semantic_support_proven"] is False


@pytest.mark.parametrize("claim_index", [0, 1])
def test_full_mapping_cannot_authorize_cross_unit_relative_comparison(tmp_path, claim_index):
    """Different facts from v6: full retrieval/mapping is not factual composition."""
    class RelativeComparisonTransport(CoverageTransport):
        def __call__(self, stage, schema, instruction, inputs):
            response = super().__call__(stage, schema, instruction, inputs)
            if stage == "composition":
                response["parsed"]["claims"][claim_index]["text"] = (
                    "Portugal had 9.1% more observed electricity demand in 2013 "
                    "than Sweden had projected electricity demand through 2041.")
            return response

    plan, report = fixture(tmp_path)
    transport = RelativeComparisonTransport("full")
    access = ModelAccess(time.monotonic()+30)
    composer = ConcurrentComposer(plan, {"r1": ("s01", "s02")}, "2026-11-06", transport,
        complete_required_branches={"r1": ["s01", "s02"]})
    with pytest.raises(ValueError, match="numeric value absent"):
        composer(report, access)
    assert transport.stages == ["mapping", "composition"]
    assert access.calls == 2 and access.guards == 0
