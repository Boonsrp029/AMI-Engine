"""Async judge connections must never migrate between per-metric event loops."""

import asyncio
import json
from types import SimpleNamespace

import pytest

from src.evals import run_ragas


@pytest.mark.parametrize("fail_at", [None, 2])
def test_all_metric_calls_and_client_close_share_one_loop(tmp_path, monkeypatch, fail_at):
    dataset = tmp_path / "cases.json"
    dataset.write_text(json.dumps([{"case_id": str(i), "query": "Question", "reference": "Fact"}
                                   for i in range(2)]), encoding="utf-8")
    loops, closed, published = [], [], []

    async def close():
        closed.append(asyncio.get_running_loop())

    class Metric:
        async def ascore(self, **kwargs):
            loops.append(asyncio.get_running_loop())
            if len(loops) == fail_at:
                raise RuntimeError("synthetic judge failure")
            return SimpleNamespace(value=0.5)

        def score(self, **kwargs):
            raise AssertionError("A per-metric asyncio.run would close the pooled client's loop")

    monkeypatch.setattr(run_ragas, "_judge_llm", lambda **_: (object(), SimpleNamespace(close=close)))
    monkeypatch.setattr(run_ragas, "RagasHuggingFaceEmbeddings", lambda **_: object())
    monkeypatch.setattr(run_ragas, "_metrics", lambda *_: {name: Metric() for name in
        ("faithfulness", "answer_relevancy", "context_precision", "context_recall")})
    monkeypatch.setattr(run_ragas, "query_agent", lambda _: {"response": "Fact", "retrieved_contexts": ["Fact"]})

    def publish(frame, path, **kwargs):
        published.append(frame)
        return "synthetic-run", path / "eval_report_latest.csv"

    monkeypatch.setattr(run_ragas, "publish_report", publish)
    if fail_at:
        with pytest.raises(RuntimeError, match="synthetic judge failure"):
            run_ragas.run_evaluation(str(dataset), str(tmp_path / "results"), judge_repeats=2)
        assert not published
    else:
        run_ragas.run_evaluation(str(dataset), str(tmp_path / "results"), judge_repeats=2)
        assert len(loops) == 16 and len(published[0]) == 4
    assert len(closed) == 1
    assert all(loop is closed[0] for loop in loops)
    assert closed[0].is_closed()
