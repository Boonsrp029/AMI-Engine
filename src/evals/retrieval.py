"""Offline document-level evaluation of the bounded analyst retrieval adapter."""

import argparse
import hashlib
import json
import threading
import time
from pathlib import Path
from statistics import mean

from src.pilot.subtasks.contracts import Identity, Plan, Subtask
from src.pilot.subtasks.retrieval import LocalBM25Adapter, _read_snapshot
from src.pilot.subtasks.scheduler import Context


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LABELS = ROOT / "data/retrieval_eval/market_multilabel.json"
DEFAULT_CORPUS = ROOT / "data/silver_level/silver_market_feeds.json"
DEPTHS = (1, 3, 5)


def _validated_queries(payload, corpus_ids):
    if not isinstance(payload, dict) or not isinstance(payload.get("queries"), list) or not payload["queries"]:
        raise ValueError("Evaluation labels must contain a nonempty queries list")
    queries = {}
    for row in payload["queries"]:
        if not isinstance(row, dict):
            raise ValueError("Each evaluation query must be an object")
        query, labels = row.get("query"), row.get("relevant_docs")
        if not isinstance(query, str) or not query.strip() or query.strip() in queries:
            raise ValueError("Evaluation queries must be nonblank and unique")
        if not isinstance(labels, list) or not labels or any(
            not isinstance(label, str) or not label.strip() for label in labels
        ):
            raise ValueError("Each query must have nonempty string relevance labels")
        if len(set(labels)) != len(labels):
            raise ValueError(f"Duplicate relevance labels for query: {query}")
        unknown = set(labels) - corpus_ids
        if unknown:
            raise ValueError(f"Gold IDs missing from corpus for query {query!r}: {sorted(unknown)}")
        queries[query.strip()] = set(labels)
    return queries


def _score(gold, ranked):
    first_hit = next((rank for rank, source_id in enumerate(ranked, 1) if source_id in gold), None)
    metrics = {"mrr": 1 / first_hit if first_hit else 0.0}
    for k in DEPTHS:
        hits = len(gold.intersection(ranked[:k]))
        metrics[f"precision_at_{k}"] = hits / k
        metrics[f"recall_at_{k}"] = hits / len(gold)
        metrics[f"precision_ceiling_at_{k}"] = min(k, len(gold)) / k
    return metrics


def evaluate(corpus_path: Path, labels_path: Path) -> dict:
    label_bytes = labels_path.read_bytes()
    payload = json.loads(label_bytes)
    corpus_sha, sources, _ = _read_snapshot(corpus_path)
    queries = _validated_queries(payload, sources.keys())
    adapter = LocalBM25Adapter(corpus_path)
    rows = []
    for query, gold in queries.items():
        task = Subtask(subtask_id="s01", operation="retrieve", query=query)
        plan = Plan(query=query, corpus_sha256=corpus_sha, subtasks=(task,))
        # The standalone evaluation has no stored runs. These IDs satisfy the
        # adapter contract without creating reviews, attempts, or revisions.
        identity = Identity(run_id="1" * 32, attempt_id="2" * 32,
                            plan_id=plan.plan_id, corpus_sha256=corpus_sha)
        context = Context(identity, task, "3" * 32, (), time.monotonic() + plan.deadline_seconds,
                          threading.Event(), threading.Event(), time.monotonic)
        result = adapter(context)
        ranked = [source.source_id for source in result.sources]
        rows.append({
            "query": query,
            "relevant_docs": sorted(gold),
            "retrieved_docs": ranked,
            "unretrieved_relevant_docs": sorted(gold.difference(ranked)),
            "metrics": _score(gold, ranked),
        })
    return {
        "evaluation": "document_retrieval_multilabel_v1",
        "strategy": "subtask_local_bm25",
        "corpus_sha256": corpus_sha,
        "corpus_documents": len(sources),
        "labels_sha256": hashlib.sha256(label_bytes).hexdigest(),
        "query_count": len(rows),
        "multi_label_query_count": sum(len(gold) > 1 for gold in queries.values()),
        "depths": list(DEPTHS),
        "aggregate": {key: mean(row["metrics"][key] for row in rows) for key in rows[0]["metrics"]},
        "per_query": rows,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    args = parser.parse_args(argv)
    try:
        report = evaluate(args.corpus, args.labels)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Retrieval evaluation failed: {exc}\n")
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
