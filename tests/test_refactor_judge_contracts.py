import os
from unittest.mock import patch

import pytest
from ragas.metrics.collections.answer_relevancy.util import AnswerRelevanceInput

from src.evals import run_ragas


@pytest.mark.parametrize("provider,model,client", [
    ("ollama", "ami-llama3.1:8b-4k", {"api_key": "ollama", "base_url": "http://localhost:11434/v1"}),
    ("groq", "llama-3.3-70b-versatile", {"api_key": "synthetic", "base_url": "https://api.groq.com/openai/v1"}),
    ("openai", "gpt-4o-mini", {"api_key": "synthetic"}),
])
def test_provider_defaults_and_client_arguments(monkeypatch, provider, model, client):
    with patch.dict(os.environ, clear=True):
        monkeypatch.setenv("RAGAS_JUDGE_PROVIDER", provider)
        monkeypatch.setenv("GROQ_API_KEY", "synthetic")
        monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
        monkeypatch.setattr(run_ragas, "AsyncOpenAI", lambda **kwargs: kwargs)
        monkeypatch.setattr(run_ragas, "llm_factory", lambda **kwargs: kwargs)
        assert run_ragas._judge_llm() == {"model": model, "provider": "openai",
            "client": {**client, "timeout": 90., "max_retries": 0}, "max_retries": 2,
            "max_tokens": 3072 if provider == "ollama" else 1024}
        monkeypatch.setenv("RAGAS_JUDGE_MODEL", "overridden-model")
        monkeypatch.setenv("RAGAS_MAX_TOKENS", "123")
        monkeypatch.setenv("RAGAS_TIMEOUT_SECONDS", "4")
        monkeypatch.setenv("RAGAS_MAX_RETRIES", "3")
        actual = run_ragas._judge_llm()
        assert (actual["model"], actual["max_tokens"], actual["max_retries"], actual["client"]["timeout"]) == (
            "overridden-model", 123, 3, 4.)


@pytest.mark.parametrize("provider,message", [
    ("groq", "GROQ_API_KEY is required for the Ragas judge"),
    ("openai", "OPENAI_API_KEY is required for the Ragas judge"),
    ("unknown", "Unsupported RAGAS_JUDGE_PROVIDER: 'unknown'"),
])
def test_judge_validation_order(provider, message):
    with patch.dict(os.environ, {"RAGAS_JUDGE_PROVIDER": provider, "RAGAS_MAX_TOKENS": "invalid"}, clear=True):
        with pytest.raises(ValueError) as error:
            run_ragas._judge_llm()
        assert str(error.value) == message


def test_local_prompt_bytes_remain_stable():
    assert run_ragas.LocalAnswerRelevancePrompt().to_string(AnswerRelevanceInput(response='Fact "A"')) == (
        "Generate one question that the answer below would answer. "
        "Set noncommittal to 1 only if the answer is evasive or says it does not know; "
        "otherwise set it to 0. Return only a JSON object with exactly two fields: "
        '{"question":"your question","noncommittal":0}. '
        "Do not return a schema, description, explanation, or markdown.\n"
        'Answer: "Fact \\"A\\""\nJSON:')
