import json
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pandas as pd

import pytest

from src.evals import run_ragas
from ragas.metrics.collections.answer_relevancy.util import AnswerRelevanceInput


def test_dataset_requires_non_empty_cases(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty"):
        run_ragas._load_cases(str(path), None)


def test_dataset_requires_question_and_reference(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps([{"query": "question only"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="query and reference"):
        run_ragas._load_cases(str(path), None)


def test_live_evaluation_aborts_without_retrieved_context(tmp_path, monkeypatch):
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps([{"query": "q", "ground_truth": "reference"}]), encoding="utf-8")
    monkeypatch.setattr(run_ragas, "query_agent", lambda _: {
        "response": "", "retrieved_contexts": [], "status": "no_context"
    })
    with pytest.raises(RuntimeError, match="no answer"):
        run_ragas.run_evaluation(str(path), str(tmp_path / "reports"), limit=1)
    assert not (tmp_path / "reports" / "eval_report_latest.csv").exists()


def test_judge_uses_ragas_modern_factory_for_local_ollama(monkeypatch):
    monkeypatch.setenv("RAGAS_JUDGE_PROVIDER", "ollama")
    monkeypatch.setenv("RAGAS_JUDGE_MODEL", "ami-llama3.1:8b-4k")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setattr(run_ragas, "AsyncOpenAI", lambda **kwargs: kwargs)
    monkeypatch.setattr(run_ragas, "llm_factory", lambda **kwargs: kwargs)

    config = run_ragas._judge_llm()
    assert config["model"] == "ami-llama3.1:8b-4k"
    assert config["provider"] == "openai"
    assert config["client"]["base_url"] == "http://localhost:11434/v1"


def test_local_answer_relevance_prompt_requests_values_without_schema():
    prompt = run_ragas.LocalAnswerRelevancePrompt().to_string(
        AnswerRelevanceInput(response='A substantive answer with "quotes".')
    )
    assert '"question":"your question"' in prompt
    assert '"noncommittal":0' in prompt
    assert 'A substantive answer with \\"quotes\\".' in prompt
    assert '"properties"' not in prompt


def test_collection_metrics_score_and_record_a_real_agent_row(tmp_path, monkeypatch):
    dataset = tmp_path / "dataset.json"
    dataset.write_text(json.dumps([{"query": "nickel question", "reference": "nickel reference"}]), encoding="utf-8")
    monkeypatch.setattr(run_ragas, "query_agent", lambda _: {
        "response": "nickel answer", "retrieved_contexts": ["nickel source"], "status": "ok"
    })
    monkeypatch.setattr(run_ragas, "_judge_llm", lambda **_: (object(), SimpleNamespace(close=AsyncMock())))
    monkeypatch.setattr(run_ragas, "RagasHuggingFaceEmbeddings", lambda **kwargs: object())

    values = {
        "faithfulness": 0.5,
        "answer_relevancy": 0.6,
        "context_precision": 0.7,
        "context_recall": 0.8,
    }
    calls = []

    def fake_metric(name):
        class Metric:
            def __init__(self, **kwargs):
                pass

            def score(self, **kwargs):
                calls.append((name, kwargs))
                return SimpleNamespace(value=values[name])

        return Metric

    for name, class_name in (
        ("faithfulness", "Faithfulness"),
        ("answer_relevancy", "AnswerRelevancy"),
        ("context_precision", "ContextPrecisionWithReference"),
        ("context_recall", "ContextRecall"),
    ):
        monkeypatch.setattr(run_ragas, class_name, fake_metric(name))

    logged = {}

    @contextmanager
    def fake_run(**kwargs):
        yield SimpleNamespace(info=SimpleNamespace(run_id="local-run"))

    monkeypatch.setattr(run_ragas.mlflow, "set_experiment", lambda name: None)
    monkeypatch.setattr(run_ragas.mlflow, "start_run", fake_run)
    monkeypatch.setattr(run_ragas.mlflow, "log_params", lambda values: logged.update(values))
    monkeypatch.setattr(run_ragas.mlflow, "log_metrics", lambda values: logged.update(values))
    monkeypatch.setattr(run_ragas.mlflow, "log_metric", lambda name, value: None)
    monkeypatch.setattr(run_ragas.mlflow, "log_artifact", lambda path, **kwargs: None)

    result = run_ragas.run_evaluation(str(dataset), str(tmp_path / "reports"), limit=1)
    assert result["run_id"] == "local-run"
    assert [name for name, _ in calls] == list(values)
    assert {name: logged[name] for name in values} == values
    report = pd.read_csv(result["report_path"])
    assert report.loc[0, "response"] == "nickel answer"
    assert report.loc[0, "faithfulness"] == 0.5
