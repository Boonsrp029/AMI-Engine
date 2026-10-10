from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document

from src.agents import graph


def test_empty_query_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        graph.query_agent("  ")


def test_no_retrieved_context_short_circuits_generation(monkeypatch):
    monkeypatch.setattr(
        graph,
        "retrieve_market_context_node",
        lambda _: {"context": "", "retrieved_docs": []},
    )
    monkeypatch.setattr(graph, "_chat_model", lambda: pytest.fail("generation must be skipped"))
    result = graph.query_agent("What changed in the market?")
    assert result["status"] == "no_context"
    assert result["response"] == ""
    assert result["retrieved_contexts"] == []


def test_retrieval_returns_shared_schema(monkeypatch):
    monkeypatch.setattr(
        graph,
        "retrieve_market_context_node",
        lambda _: {
            "context": "evidence text",
            "retrieved_docs": [Document(page_content="evidence text", metadata={"feed_id": "f1"})],
        },
    )
    result = graph.retrieval_node({"query": "Q"})
    assert result["context"] == "evidence text"
    assert result["retrieved_contexts"] == ["evidence text"]
    assert result["citations"] == [{"feed_id": "f1"}]
    assert result["status"] == "ok"


def test_analysis_uses_structured_output(monkeypatch):
    analysis = graph.Analysis(findings=["Supported fact"], confidence=0.8, response="Brief")
    structured_model = MagicMock()
    structured_model.invoke.return_value = analysis
    model = MagicMock()
    model.with_structured_output.return_value = structured_model
    monkeypatch.setattr(graph, "_chat_model", lambda: model)
    output = graph.analysis_and_synthesis_node({
        "query": "Q", "context": "Evidence", "retrieved_contexts": ["Evidence"]
    })
    assert output == {"findings": ["Supported fact"], "confidence": 0.8, "response": "Brief", "status": "ok"}


def test_analysis_skips_without_context():
    assert graph.analysis_and_synthesis_node({"query": "Q"}) == {"status": "no_context"}


def test_guardrail_fails_closed(monkeypatch):
    class BrokenGuardrails:
        def validate_output(self, **_):
            raise RuntimeError("not shown to callers")

    monkeypatch.setattr(graph, "GuardrailsRunner", BrokenGuardrails)
    output = graph.guardrail_node({"response": "private text", "context": "source"})
    assert output["response"] == ""
    assert output["status"] == "failed"
    assert "RuntimeError" in output["error"]


def test_guardrail_rejects_flagged_output(monkeypatch):
    class RejectingGuardrails:
        def validate_output(self, **_):
            return {"passed_guardrails": False, "validated_report": "blocked"}

    monkeypatch.setattr(graph, "GuardrailsRunner", RejectingGuardrails)
    output = graph.guardrail_node({"response": "bad", "context": "source"})
    assert output["response"] == ""
    assert output["status"] == "failed"
