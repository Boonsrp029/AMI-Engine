import json

import pytest

from src.evals import run_ragas


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
    monkeypatch.setenv("RAGAS_JUDGE_MODEL", "qwen2.5:14b")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setattr(run_ragas, "OpenAI", lambda **kwargs: kwargs)
    monkeypatch.setattr(run_ragas, "llm_factory", lambda **kwargs: kwargs)

    config = run_ragas._judge_llm()
    assert config["model"] == "qwen2.5:14b"
    assert config["provider"] == "openai"
    assert config["client"]["base_url"] == "http://localhost:11434/v1"
