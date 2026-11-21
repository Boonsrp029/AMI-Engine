import json

import pytest

from src.evals.retrieval import evaluate


@pytest.fixture
def benchmark(tmp_path):
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps([
        {"feed_id": "a", "clean_content": "canal water"},
        {"feed_id": "b", "clean_content": "canal flow"},
        {"feed_id": "c", "clean_content": "reservoir storage"},
    ]), encoding="utf-8")
    return corpus, tmp_path / "labels.json"


def test_actual_adapter_scores_multiple_labels_and_keeps_empty_retrieval(benchmark):
    corpus, labels = benchmark
    labels.write_text(json.dumps({"queries": [
        {"query": "canal", "relevant_docs": ["b", "c"]},
        {"query": "unmatched", "relevant_docs": ["a"]},
    ]}), encoding="utf-8")

    report = evaluate(corpus, labels)
    assert report["query_count"] == 2
    assert report["multi_label_query_count"] == 1
    first, second = report["per_query"]
    assert first["retrieved_docs"] == ["a", "b"]
    assert first["unretrieved_relevant_docs"] == ["c"]
    assert first["metrics"]["precision_at_3"] == pytest.approx(1 / 3)
    assert first["metrics"]["recall_at_3"] == 0.5
    assert first["metrics"]["precision_ceiling_at_3"] == pytest.approx(2 / 3)
    assert second["retrieved_docs"] == []
    assert report["aggregate"]["recall_at_5"] == 0.25
    assert report["aggregate"]["mrr"] == 0.25


@pytest.mark.parametrize(("gold", "error"), [
    ([], "nonempty string relevance labels"),
    (["a", "a"], "Duplicate relevance labels"),
    (["different-corpus-id"], "Gold IDs missing from corpus"),
])
def test_invalid_judgments_fail_before_scoring(benchmark, gold, error):
    corpus, labels = benchmark
    labels.write_text(json.dumps({"queries": [{"query": "canal", "relevant_docs": gold}]}),
                      encoding="utf-8")
    with pytest.raises(ValueError, match=error):
        evaluate(corpus, labels)
