"""Canonical LangGraph workflow for market research queries."""

from __future__ import annotations

import os
from typing import Any, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from src.agents.retriever_node import retrieve_market_context_node
from src.utils.guardrails_runner import GuardrailsRunner


class MarketState(TypedDict, total=False):
    """Single state schema shared by graph nodes, evaluation and serving."""

    query: str
    context: str
    retrieved_contexts: list[str]
    citations: list[dict[str, Any]]
    findings: list[str]
    confidence: float
    response: str
    status: Literal["ok", "no_context", "failed"]
    error: str


class Analysis(BaseModel):
    findings: list[str] = Field(description="Evidence-based findings from retrieved context")
    confidence: float = Field(ge=0, le=1)
    response: str = Field(description="Concise market research brief with source references")


def _chat_model() -> BaseChatModel:
    """Build an OpenAI-compatible model client from environment configuration."""
    provider = os.getenv("AGENT_LLM_PROVIDER", os.getenv("LLM_PROVIDER", "ollama")).lower()
    default_models = {
        "ollama": os.getenv("OLLAMA_MODEL", "qwen2.5:14b"),
        "groq": "llama-3.3-70b-versatile",
        "openai": "gpt-4o-mini",
    }
    model = os.getenv("AGENT_LLM_MODEL", default_models.get(provider, ""))
    if provider == "ollama":
        return ChatOllama(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/"),
            model=model,
            temperature=0,
            num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "8192")),
            num_predict=int(os.getenv("OLLAMA_NUM_PREDICT", "1200")),
        )
    if provider == "groq":
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
        return ChatOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=key,
            model=model,
            temperature=0,
            max_retries=2,
            timeout=60,
        )
    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return ChatOpenAI(
            api_key=key, model=model,
            temperature=0, max_retries=2, timeout=60,
        )
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider!r}; use ollama, groq or openai")


def retrieval_node(state: MarketState) -> dict[str, Any]:
    result = retrieve_market_context_node({"query": state.get("query", "")})
    if result.get("error"):
        return {
            "context": "",
            "retrieved_contexts": [],
            "citations": [],
            "status": "failed",
            "error": result["error"],
        }
    docs = result.get("retrieved_docs", [])
    contexts = [doc.page_content for doc in docs if getattr(doc, "page_content", "").strip()]
    citations = [dict(getattr(doc, "metadata", {}) or {}) for doc in docs]
    if not contexts:
        return {
            "context": "",
            "retrieved_contexts": [],
            "citations": [],
            "status": "no_context",
            "error": "No documents were retrieved; generation was skipped.",
        }
    return {
        "context": "\n\n---\n\n".join(contexts),
        "retrieved_contexts": contexts,
        "citations": citations,
        "status": "ok",
        "error": "",
    }


def analysis_and_synthesis_node(state: MarketState) -> dict[str, Any]:
    if not state.get("retrieved_contexts"):
        return {"status": "no_context"}
    model = _chat_model().with_structured_output(Analysis)
    result = model.invoke([
        SystemMessage(content=(
            "You are a careful market research analyst. Use only the supplied evidence. "
            "Separate supported findings from uncertainty, do not invent facts or citations, "
            "and produce a concise answer. If evidence is insufficient, say so."
        )),
        HumanMessage(content=f"Question:\n{state['query']}\n\nRetrieved evidence:\n{state['context']}"),
    ])
    return {
        "findings": result.findings,
        "confidence": result.confidence,
        "response": result.response,
        "status": "ok",
    }


def guardrail_node(state: MarketState) -> dict[str, Any]:
    try:
        checked = GuardrailsRunner().validate_output(
            raw_report=state.get("response", ""),
            context=state.get("context", ""),
            user_input=state.get("query", ""),
        )
    except Exception as exc:
        # Fail closed: never return unvalidated content when a configured rail fails.
        return {"response": "", "status": "failed", "error": f"Guardrail check failed: {type(exc).__name__}"}
    if not checked.get("passed_guardrails"):
        return {"response": "", "status": "failed", "error": "Output did not pass configured guardrails."}
    return {"response": checked["validated_report"], "status": "ok", "error": ""}


def _after_retrieval(state: MarketState) -> Literal["analyze", "finish"]:
    return "analyze" if state.get("retrieved_contexts") else "finish"


workflow = StateGraph(MarketState)
workflow.add_node("retrieve", retrieval_node)
workflow.add_node("analyze", analysis_and_synthesis_node)
workflow.add_node("guardrails", guardrail_node)
workflow.add_edge(START, "retrieve")
workflow.add_conditional_edges("retrieve", _after_retrieval, {"analyze": "analyze", "finish": END})
workflow.add_edge("analyze", "guardrails")
workflow.add_edge("guardrails", END)
app = workflow.compile()


def query_agent(query_text: str) -> dict[str, Any]:
    query = query_text.strip()
    if not query:
        raise ValueError("query_text must not be empty")
    return app.invoke({
        "query": query,
        "context": "",
        "retrieved_contexts": [],
        "citations": [],
        "findings": [],
        "confidence": 0.0,
        "response": "",
        "status": "failed",
        "error": "",
    })
