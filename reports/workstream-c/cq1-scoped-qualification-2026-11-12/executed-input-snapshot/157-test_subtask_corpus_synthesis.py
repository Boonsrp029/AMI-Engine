"""C contract tests using B's real corpus adapter; no inference or services."""
from dataclasses import dataclass
import hashlib
import json
import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from src.pilot.schemas import ResearchRequest, ReviewRequest
from src.pilot.store import Store, Conflict
from src.pilot.subtasks.contracts import Plan, Subtask
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.runner import run_stored_plan
from src.pilot.subtasks.synthesis import project_report


OBSERVED = "In Canada, observed electricity demand grew 6.4% in 2017."
FORECAST = "In Japan, electricity demand is projected to grow 3.2% annually through 2034."
QUESTION = "Compare observed electricity demand in Canada in 2017 with projected electricity demand in Japan through 2034."


@dataclass
class FixedCorpusComposer:
    plan: Plan
    mode: str = "valid"

    def __call__(self, report, access):
        # These are fixed model responses. Evidence still must come from the
        # actual adapter report and pass C's normal validators.
        components, claims, bindings = [], [], {}
        for index, result in enumerate(report.results):
            cid = f"r{index + 1}"
            bindings[cid] = (result.subtask_id,)
            if result.outcome == "missing":
                components.append(dict(component_id=cid, question_anchor=QUESTION,
                    status="missing", short_answer="", evidence=[], gap_anchor="projected electricity demand"))
                continue
            source = result.sources[0]
            components.append(dict(component_id=cid, question_anchor=QUESTION, status="supported",
                short_answer=source.content, evidence=[dict(source_id=source.source_id, quote=source.content)]))
            claims.append(dict(component_id=cid, unit_id=f"u{index + 1}", text=source.content))
        mapping = access.main(lambda: {"components": components})
        if self.mode == "fallback":
            claims = claims[:1]
        elif self.mode == "denominator":
            claims[1]["text"] = claims[1]["text"].replace("total electricity generation", "total energy consumption")
        elif self.mode == "geography":
            claims[1]["text"] = FORECAST.replace("Japan", "Canada")
        elif self.mode == "invalid_source":
            components[1]["evidence"][0]["source_id"] = "not-in-corpus"
        elif self.mode == "quantity":
            claims[1]["text"] = FORECAST.replace("3.2%", "6.4%")
        elif self.mode == "period":
            claims[1]["text"] = FORECAST.replace("2034", "2017")
        elif self.mode == "measure":
            claims[1]["text"] = FORECAST.replace("demand", "generation")
        elif self.mode == "basis":
            claims[1]["text"] = FORECAST.replace("is projected to grow", "grew")
        composed = access.main(lambda: {"title": "Analyst research brief", "claims": claims})
        result = project_report(self.plan, report, mapping, composed, bindings,
            as_of="2026-11-06", is_current=lambda: True)
        if self.mode == "lost_provenance":
            from dataclasses import replace
            result = replace(result, provenance=())
        return result


def allow(draft, sources):
    return True


def deny(draft, sources):
    return False


def setup_corpus(tmp_path, missing=False):
    path = tmp_path / "corpus.json"
    rows = [{"feed_id": "observed", "title": "Observed", "clean_content": OBSERVED},
            {"feed_id": "forecast", "title": "Forecast", "clean_content": FORECAST}]
    path.write_text(json.dumps(rows), encoding="utf-8")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    plan = Plan(query=QUESTION, corpus_sha256=sha, subtasks=(
        Subtask(subtask_id="s01", operation="retrieve", query="observed"),
        Subtask(subtask_id="s02", operation="retrieve", query="nonexistentquartz" if missing else "projected")))
    store = Store(tmp_path / "history.sqlite3")
    rid, _ = store.create(ResearchRequest(query=QUESTION, request_key="corpus-c-case"), sha)
    return path, plan, store, rid


@pytest.mark.parametrize("mode", ["valid", "fallback"])
def test_corpus_to_typed_safety_persistence_and_exact_review(tmp_path, mode):
    path, plan, store, rid = setup_corpus(tmp_path)
    run_stored_plan(store, rid, plan, path, LocalBM25Adapter(path), FixedCorpusComposer(plan, mode), allow)
    row = store.get(rid)
    assert row["status"] == "needs_review"
    assert row["metrics"]["guardrail_invocations"] == 1
    assert row["metrics"]["model_calls"] == 2
    assert {c["text"] for c in row["draft"]["claims"]} == {OBSERVED, FORECAST}
    origins = [o for c in row["metrics"]["composition_provenance"] for o in c["origins"]]
    assert {o["subtask_id"] for o in origins} == {"s01", "s02"}
    assert all(o["corpus_sha256"] == plan.corpus_sha256 for o in origins)
    diagnostics = row["metrics"]["composition_diagnostics"]
    assert bool(diagnostics["fallback_unit_ids"]) == (mode == "fallback")
    assert diagnostics["editorial_correction"] is False
    assert len(diagnostics["raw_composer_output"]["claims"]) == (1 if mode == "fallback" else 2)
    with pytest.raises(Conflict):
        store.export(rid)
    store.review(rid, ReviewRequest(revision=1, decision="approve", reviewer="synthetic-C", support_confirmed=True))
    exported = store.export(rid)
    assert store.export(rid) == exported
    store.save_draft(rid, row["draft"], row["sources"], {}, expected_revision=1)
    with pytest.raises(Conflict):
        store.export(rid)


@pytest.mark.parametrize("mode", ["quantity", "period", "measure", "basis", "geography", "invalid_source", "lost_provenance"])
def test_corpus_relationship_substitution_cannot_publish(tmp_path, mode):
    path, plan, store, rid = setup_corpus(tmp_path)
    with pytest.raises(ValueError):
        run_stored_plan(store, rid, plan, path, LocalBM25Adapter(path), FixedCorpusComposer(plan, mode), allow)
    row = store.get(rid)
    assert row["revision"] == 0
    assert not any(e["kind"] == "composition_candidate" for e in row["events"])


def test_corpus_missing_required_evidence_retains_supported_answer(tmp_path):
    path, plan, store, rid = setup_corpus(tmp_path, missing=True)
    run_stored_plan(store, rid, plan, path, LocalBM25Adapter(path), FixedCorpusComposer(plan), allow)
    row = store.get(rid)
    assert [c["text"] for c in row["draft"]["claims"]] == [OBSERVED]
    assert any("s02 returned missing" in w for w in row["draft"]["warnings"])


def test_corpus_safety_rejection_cannot_publish(tmp_path):
    path, plan, store, rid = setup_corpus(tmp_path)
    with pytest.raises(ValueError):
        run_stored_plan(store, rid, plan, path, LocalBM25Adapter(path), FixedCorpusComposer(plan), deny)
    assert store.get(rid)["revision"] == 0


@dataclass
class ControlledAdapter:
    path: str
    entered: object = None
    release: object = None
    corrupt: bool = False

    def __call__(self, context):
        result = LocalBM25Adapter(self.path)(context)
        if self.corrupt:
            source = result.sources[0].model_copy(update={"content_sha256": "f" * 64})
            return result.model_copy(update={"sources": (source,)})
        self.entered.set()
        self.release.acquire(timeout=30)
        return result


def test_corpus_invalid_content_identity_fails_required_branch(tmp_path):
    path, plan, store, rid = setup_corpus(tmp_path)
    with pytest.raises((ValueError, RuntimeError)):
        run_stored_plan(store, rid, plan, path, ControlledAdapter(str(path), corrupt=True),
            FixedCorpusComposer(plan), allow)
    row = store.get(rid)
    assert row["revision"] == 0 and row["status"] == "failed"
    assert any(e["kind"] == "subtask_progress" and e["payload"].get("status") == "failed"
               for e in row["events"])


def test_corpus_cancellation_fences_computed_but_late_results(tmp_path):
    path, plan, store, rid = setup_corpus(tmp_path)
    ctx = multiprocessing.get_context("spawn")
    entered, release, cancel = ctx.Event(), ctx.Semaphore(0), threading.Event()
    with ThreadPoolExecutor(1) as caller:
        future = caller.submit(run_stored_plan, store, rid, plan, path,
            ControlledAdapter(str(path), entered, release), FixedCorpusComposer(plan), allow,
            cancellation=cancel)
        try:
            assert entered.wait(30), "Actual adapter must produce a result before cancellation"
            cancel.set()
            with pytest.raises((ValueError, RuntimeError, Conflict)):
                future.result(timeout=20)
        finally:
            cancel.set()
            release.release()
            release.release()
    row = store.get(rid)
    assert row["status"] == "interrupted" and row["revision"] == 0
    attempt = next(e["payload"]["attempt_id"] for e in row["events"] if e["kind"] == "attempt_started")
    assert not store.attempt_event(rid, attempt, "late-composition", {})
    assert not any(e["kind"] == "composition_candidate" for e in row["events"])


@pytest.mark.parametrize("text,valid", [
    ("In Denmark, wind supplied 27% of total electricity generation.", True),
    ("In Denmark, wind supplied 27% of total energy consumption.", False),
    ("In Sweden, wind supplied 27% of total electricity generation.", False),
    ("Wind supplied 27% of total electricity generation.", False),
    ("In Denmark, wind supplied 27%.", False),
])
def test_unit_local_explicit_scope_and_denominator_contract(text, valid):
    from src.pilot._evidence import EvidenceQuote
    from src.pilot.subtasks._relationships import validate_relationships
    evidence = [EvidenceQuote(source_id="wind", quote="In Denmark, wind supplied 27% of total electricity generation.")]
    if valid:
        validate_relationships(text, evidence)
    else:
        with pytest.raises(ValueError):
            validate_relationships(text, evidence)


@pytest.mark.parametrize(("text", "valid"), [
    ("In 2018, rail carried 36% of total domestic freight in Peru.", True),
    ("In 2019, rail carried 36% of total domestic freight in Peru.", False),
    ("In 2018, rail carried 36% of total domestic freight in Chile.", False),
    ("In 2018, rail carried 63% of total domestic freight in Peru.", False),
    ("In 2018, rail carried 36% of total freight in Peru.", False),
    ("In 2018, rail carried 36% of total domestic freight tonnes in Peru.", False),
    ("In 2018, rail was projected to carry 36% of total domestic freight in Peru.", False),
    ("In 2018, trucks carried 36% of total domestic freight in Peru.", False),
    ("In 2018, rail carried 36% of total domestic freight in Peru and Chile.", False),
])
def test_relocated_percentage_scope_requires_the_same_fact(text, valid):
    from src.pilot._evidence import EvidenceQuote
    from src.pilot.subtasks._relationships import validate_relationships

    quote = EvidenceQuote(source_id="rail", quote="In Peru, rail carried 36% of total domestic freight in 2018.")
    if valid:
        validate_relationships(text, [quote])
        validate_relationships(quote.quote, [quote.model_copy(update={"quote": text})])
        with pytest.raises(ValueError, match="denominator"):
            validate_relationships(text, [quote, quote.model_copy(update={"source_id": "second"})])
    else:
        with pytest.raises(ValueError):
            validate_relationships(text, [quote])


def test_corpus_denominator_substitution_cannot_publish(tmp_path):
    path, _, _, _ = setup_corpus(tmp_path)
    rows = json.loads(path.read_text())
    rows[1]["clean_content"] = "In Japan, projected wind output supplies 23% of total electricity generation."
    path.write_text(json.dumps(rows), encoding="utf-8")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    plan = Plan(query=QUESTION, corpus_sha256=sha, subtasks=(
        Subtask(subtask_id="s01", operation="retrieve", query="observed"),
        Subtask(subtask_id="s02", operation="retrieve", query="projected")))
    store = Store(tmp_path / "denominator.sqlite3")
    rid, _ = store.create(ResearchRequest(query=QUESTION, request_key="denominator-c"), sha)
    with pytest.raises(ValueError):
        run_stored_plan(store, rid, plan, path, LocalBM25Adapter(path), FixedCorpusComposer(plan, "denominator"), allow)
    assert store.get(rid)["revision"] == 0
