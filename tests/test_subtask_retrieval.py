import hashlib
import json
import pickle
import threading
import time
from pathlib import Path

import pytest

from src.agents.local_retriever import create_local_retriever
from src.pilot.subtasks.contracts import Identity, Plan, Source, Subtask, digest
from src.pilot.subtasks.retrieval import LocalBM25Adapter
from src.pilot.subtasks.scheduler import Context, run_plan


def _write_corpus(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows():
    return [
        {"feed_id": "a", "title": "Alpha market", "source": "Publisher One",
         "raw_content": "Alpha market growth is steady.", "url": "https://example.test/a",
         "published": "2026-11-01", "doc_name": "report-a.pdf", "page_num": 0},
        {"feed_id": "b", "title": "Alpha market", "source": "Publisher Two",
         "clean_content": "Alpha market growth is steady."},
        {"feed_id": "c", "title": "Beta outlook", "source": "Publisher Three",
         "aggregated_context": "Beta market outlook remains cautious."},
        {"feed_id": "d", "title": "Contrary outlook", "source": "Publisher Four",
         "clean_content": "Alpha market growth declined sharply."},
        {"feed_id": "e", "title": "Additional alpha", "source": "Publisher Five",
         "clean_content": "Alpha demand improved."},
        {"feed_id": "f", "title": "Additional alpha two", "source": "Publisher Six",
         "clean_content": "Alpha supply expanded."},
        {"feed_id": "g", "title": "Additional alpha three", "source": "Publisher Seven",
         "clean_content": "Alpha outlook stable."},
    ]


def _context(path, *, task=None, dependencies=(), child="3" * 32, identity=None):
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if task is None:
        task = Subtask(subtask_id="s01", operation="retrieve", query="alpha market")
    if identity is None and dependencies:
        identity = dependencies[0].identity
    if identity is None:
        plan = Plan(query="Synthetic market request", corpus_sha256=sha, subtasks=(task,))
        identity = Identity(run_id="1" * 32, attempt_id="2" * 32,
                            plan_id=plan.plan_id, corpus_sha256=sha)
    return Context(identity, task, child, tuple(dependencies), time.monotonic() + 30,
                   threading.Event(), threading.Event(), time.monotonic)


def _retrieved(path, query="alpha market", subtask_id="s01"):
    task = Subtask(subtask_id=subtask_id, operation="retrieve", query=query)
    return LocalBM25Adapter(path)(_context(path, task=task))


def test_adapter_is_picklable_and_preserves_rank_metadata_and_exact_content(tmp_path, monkeypatch):
    path = tmp_path / "silver_level" / "corpus.json"
    _write_corpus(path, _rows())
    monkeypatch.setenv("LOCAL_RETRIEVAL_CORPUS", str(path))
    monkeypatch.setenv("LOCAL_RETRIEVER_MODE", "bm25")
    adapter = LocalBM25Adapter(path)
    assert pickle.loads(pickle.dumps(adapter)).corpus_path == str(path)

    result = adapter(_context(path))
    assert result.outcome == "evidence"
    assert len(result.sources) == 5
    expected = [doc.metadata["feed_id"] for doc in create_local_retriever(5).invoke("alpha market")]
    assert [source.source_id for source in result.sources] == expected
    assert result.sources[0].content == _rows()[0]["raw_content"]
    assert result.sources[0].content_sha256 == digest(result.sources[0].content)
    assert result.sources[0].url == "https://example.test/a"
    assert result.sources[0].published == "2026-11-01"
    assert result.sources[0].doc_name == "report-a.pdf"
    assert result.sources[0].page_num == 0
    assert result.sources[1].url == ""  # publisher labels are not URLs
    assert result.sources[1].published is None  # ingestion timestamps are not publication dates
    assert result.identity.corpus_sha256 == result.sources[0].corpus_sha256


def test_equal_rank_order_duplicate_text_and_conflicting_records_are_preserved(tmp_path):
    path = tmp_path / "silver_level" / "corpus.json"
    _write_corpus(path, _rows())
    result = _retrieved(path, "alpha market growth")
    ids = [source.source_id for source in result.sources]
    assert ids.index("a") < ids.index("b")  # equal-content tie follows input order
    assert len(set(ids)) == len(ids)
    assert any("declined sharply" in source.content for source in result.sources)
    assert result.outcome == "evidence"  # multiple records do not imply semantic conflict


def test_checked_in_silver_corpus_matches_existing_local_retriever(monkeypatch):
    corpus = Path(__file__).resolve().parents[1] / "data" / "silver_level" / "silver_market_feeds.json"
    rows = json.loads(corpus.read_text(encoding="utf-8"))
    query = rows[0]["title"]
    monkeypatch.setenv("LOCAL_RETRIEVAL_CORPUS", str(corpus))
    monkeypatch.setenv("LOCAL_RETRIEVER_MODE", "bm25")
    expected = create_local_retriever(5).invoke(query)
    sha = hashlib.sha256(corpus.read_bytes()).hexdigest()
    task = Subtask(subtask_id="s01", operation="retrieve", query=query)
    plan = Plan(query="Checked-in Silver corpus parity", corpus_sha256=sha, subtasks=(task,))
    identity = Identity(run_id="1" * 32, attempt_id="2" * 32,
                        plan_id=plan.plan_id, corpus_sha256=sha)
    context = Context(identity, task, "3" * 32, (), time.monotonic() + 30,
                      threading.Event(), threading.Event(), time.monotonic)
    actual = LocalBM25Adapter(corpus)(context)
    assert [source.source_id for source in actual.sources] == [doc.metadata["feed_id"] for doc in expected]
    assert [source.content for source in actual.sources] == [
        next(row.get("clean_content") or row.get("raw_content") or row.get("aggregated_context")
             for row in rows if str(row["feed_id"]) == str(doc.metadata["feed_id"]))
        for doc in expected
    ]
    assert all(source.corpus_sha256 == sha for source in actual.sources)


def test_empty_search_is_completed_missing_not_a_worker_failure(tmp_path):
    path = tmp_path / "silver_level" / "corpus.json"
    _write_corpus(path, _rows())
    result = _retrieved(path, "unmatched-token-xyz")
    assert result.outcome == "missing"
    assert result.sources == ()
    assert result.diagnostic == "no_matching_evidence"


def test_fallback_ids_are_stable_and_duplicate_ids_fail_closed(tmp_path):
    path = tmp_path / "silver_level" / "corpus.json"
    rows = _rows()[:2]
    for row in rows:
        row.pop("feed_id")
    _write_corpus(path, rows)
    first = _retrieved(path)
    second = _retrieved(path)
    assert [s.source_id for s in first.sources] == [s.source_id for s in second.sources]
    assert first.sources[0].source_id.startswith("silver:")

    rows[0]["feed_id"] = rows[1]["feed_id"] = "duplicate"
    _write_corpus(path, rows)
    with pytest.raises(ValueError, match="unique"):
        _retrieved(path)


def test_malformed_json_and_rows_are_technical_errors(tmp_path):
    path = tmp_path / "corpus.json"
    path.write_text("{bad", encoding="utf-8")
    with pytest.raises(ValueError, match="UTF-8 JSON"):
        _retrieved(path)
    _write_corpus(path, [{"feed_id": "x"}, 3])
    with pytest.raises(ValueError, match="source-record objects"):
        _retrieved(path)
    _write_corpus(path, [{"feed_id": "x", "clean_content": " "}])
    with pytest.raises(ValueError, match="searchable source content"):
        _retrieved(path)


def test_changed_corpus_identity_and_mid_search_mutation_fail_closed(tmp_path, monkeypatch):
    path = tmp_path / "corpus.json"
    _write_corpus(path, _rows())
    task = Subtask(subtask_id="s01", operation="retrieve", query="alpha")
    context = _context(path, task=task, identity=Identity(
        run_id="1" * 32, attempt_id="2" * 32, plan_id="4" * 64, corpus_sha256="5" * 64))
    with pytest.raises(ValueError, match="does not match"):
        LocalBM25Adapter(path)(context)

    import src.pilot.subtasks.retrieval as retrieval
    original = retrieval._bm25_scores

    def mutate_after_scoring(query, documents):
        scores = original(query, documents)
        path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
        return scores

    monkeypatch.setattr(retrieval, "_bm25_scores", mutate_after_scoring)
    with pytest.raises(ValueError, match="changed before"):
        _retrieved(path)


def test_inspection_is_limited_to_declared_dependency_sources_and_exact_snapshot(tmp_path):
    path = tmp_path / "corpus.json"
    _write_corpus(path, _rows())
    retrieved = _retrieved(path, "alpha", "s01")
    source_id = retrieved.sources[0].source_id
    task = Subtask(subtask_id="s02", operation="inspect_sources", source_ids=(source_id,),
                   dependencies=("s01",))
    context = _context(path, task=task, dependencies=(retrieved,), child="6" * 32)
    inspected = LocalBM25Adapter(path)(context)
    assert inspected.sources[0].model_dump() == retrieved.sources[0].model_dump()
    assert inspected.dependencies == context.dependency_refs
    assert inspected.subtask_id == "s02"

    unauthorized = Subtask(subtask_id="s02", operation="inspect_sources", source_ids=("c",),
                           dependencies=("s01",))
    with pytest.raises(ValueError, match="not in a declared dependency"):
        LocalBM25Adapter(path)(_context(path, task=unauthorized, dependencies=(retrieved,)))

    tampered_source = retrieved.sources[0].model_copy(update={"content": "fabricated"})
    # Construct a validly hashed but false dependency record; revalidation against
    # the pinned corpus must reject it even though its source ID is authorized.
    tampered_source = Source(**{**tampered_source.model_dump(), "content_sha256": digest("fabricated")})
    tampered = retrieved.model_copy(update={"sources": (tampered_source,)})
    with pytest.raises(ValueError, match="does not match the pinned corpus"):
        LocalBM25Adapter(path)(_context(path, task=task, dependencies=(tampered,)))


def test_inspection_cannot_upgrade_context_only_source_to_support(tmp_path):
    path = tmp_path / "corpus.json"
    _write_corpus(path, _rows())
    base = _retrieved(path, "alpha", "s01")
    source = base.sources[0].model_copy(update={"role": "context"})
    dependency = base.model_copy(update={"sources": (source,), "outcome": "missing"})
    task = Subtask(subtask_id="s02", operation="inspect_sources", source_ids=(source.source_id,),
                   dependencies=("s01",))
    inspected = LocalBM25Adapter(path)(_context(path, task=task, dependencies=(dependency,)))
    assert inspected.outcome == "missing"
    assert inspected.sources[0].role == "context"


def test_pre_cancelled_or_expired_context_does_not_read_corpus(tmp_path):
    path = tmp_path / "corpus.json"
    _write_corpus(path, _rows())
    task = Subtask(subtask_id="s01", operation="retrieve", query="alpha")
    context = _context(path, task=task)
    context.cancellation.set()
    with pytest.raises(TimeoutError, match="cancelled"):
        LocalBM25Adapter(path)(context)

    context.cancellation.clear()
    expired = Context(context.identity, task, context.child_attempt_id, (), 0,
                      context.cancellation, context.parent_cancellation, lambda: 1)
    with pytest.raises(TimeoutError, match="deadline"):
        LocalBM25Adapter(path)(expired)


def test_operation_runs_through_scheduler_in_plan_order_with_dependent_inspection(tmp_path):
    path = tmp_path / "corpus.json"
    sha = _write_corpus(path, _rows())
    tasks = (
        Subtask(subtask_id="s01", operation="retrieve", query="alpha"),
        Subtask(subtask_id="s02", operation="retrieve", query="alpha"),
        Subtask(subtask_id="s03", operation="inspect_sources", source_ids=("a",),
                dependencies=("s01",)),
    )
    plan = Plan(query="Synthetic market request", corpus_sha256=sha, subtasks=tasks,
                retrieval_concurrency=2, deadline_seconds=10)
    adapter = LocalBM25Adapter(path)
    release_s01 = threading.Event()
    completion_order = []

    def operation(context):
        result = adapter(context)
        if context.task.subtask_id == "s01":
            assert release_s01.wait(3)
        completion_order.append(context.task.subtask_id)
        if context.task.subtask_id == "s02":
            release_s01.set()
        return result

    report = run_plan(plan, "1" * 32, "2" * 32, operation)
    assert report.can_compose
    assert completion_order.index("s02") < completion_order.index("s01")
    assert [result.subtask_id for result in report.results] == ["s01", "s02", "s03"]
    assert report.results[2].dependencies[0].subtask_id == "s01"
    assert report.results[2].sources[0].source_id == "a"
    merged_a = next(item for item in report.sources if item.source.source_id == "a")
    assert merged_a.origins == (("s01", "support"), ("s02", "support"), ("s03", "support"))
