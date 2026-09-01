import os
import yaml
from typing import TypedDict, List, Optional, Literal, Dict, Any, Union
from typing_extensions import Annotated
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages


class GlobalMarketState(TypedDict):
    """
    Global graph state passed between supervisor and sub-agent nodes.
    Sub-agents receive slices of this state to enforce strict scope boundaries.
    """
    # Core User Input & Goal Configuration
    user_query: str
    target_sector: str
    
    # LangGraph Message Stream (Enables conversation tracking & tool calling across nodes)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Supervisor Control & Loop Mechanics
    next_agent: Optional[str]          # Target node selected by supervisor for conditional routing
    iteration_count: int               # Evaluated against max_iterations in agent_config.yaml
    confidence_score: Optional[float]  # Evaluated against confidence_threshold in agent_config.yaml
    status: Literal["RUNNING", "NEEDS_RETRY", "COMPLETED", "FAILED"]
    
    # Agent Artifacts & Deliverables
    retrieved_contexts: Optional[List[Union[str, Dict[str, Any]]]]  # Databricks Vector Search chunks
    analysis_findings: Optional[List[str]]                          # Key insights from Market Analysis Agent
    synthesis: Optional[str]                                        # Final research brief (Synthesis Agent)
    final_report: Optional[str]                                     # Alias for synthesis / Gold Delta payload
    citations: Optional[List[Dict[str, Any]]]                       # Provenance metadata (SEC filings, web feeds)
    
    # Guardrails, Observability & Error Traces
    guardrail_passed: Optional[bool]   # Boolean flag from NeMo Guardrails check node
    guardrail_feedback: Optional[str]  # Policy violation notes if guardrail flags output
    error_log: Optional[List[str]]     # Exception traces to assist supervisor in retry logic


def load_agent_config(config_path: str = "config/agent_config.yaml") -> dict:
    """Loads runtime parameters and routing thresholds."""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {
        "supervisor": {"max_iterations": 3},
        "analyzer": {"confidence_threshold": 0.85}
    }


def supervisor_node(state: GlobalMarketState) -> Dict[str, Any]:
    """
    Supervisor Router Node: Decides the next agent destination based on
    current graph state, confidence score, and maximum iteration bounds.
    """
    config = load_agent_config()
    max_iterations = config.get("supervisor", {}).get("max_iterations", 3)
    confidence_threshold = config.get("analyzer", {}).get("confidence_threshold", 0.85)
    
    current_iteration = state.get("iteration_count", 0) + 1
    retrieved_contexts = state.get("retrieved_contexts") or []
    analysis_findings = state.get("analysis_findings") or []
    confidence_score = state.get("confidence_score") or 0.0
    guardrail_passed = state.get("guardrail_passed")
    
    # 1. Check max iteration breach
    if current_iteration > max_iterations:
        return {
            "next_agent": "__end__",
            "iteration_count": current_iteration,
            "status": "FAILED",
            "error_log": (state.get("error_log") or []) + ["Exceeded maximum supervisor iteration loop."]
        }
    
    # 2. Stage 1: Route to Retriever if context is missing
    if not retrieved_contexts:
        return {
            "next_agent": "retriever",
            "iteration_count": current_iteration,
            "status": "RUNNING"
        }
    
    # 3. Stage 2: Route to Analyzer if context exists but findings are incomplete
    if not analysis_findings or confidence_score < confidence_threshold:
        return {
            "next_agent": "analyzer",
            "iteration_count": current_iteration,
            "status": "RUNNING"
        }
    
    # 4. Stage 3: Route to Synthesizer if findings meet confidence threshold
    if not state.get("synthesis") and not state.get("final_report"):
        return {
            "next_agent": "synthesizer",
            "iteration_count": current_iteration,
            "status": "RUNNING"
        }
    
    # 5. Stage 4: Route to NeMo Guardrails check
    if guardrail_passed is None:
        return {
            "next_agent": "guardrails",
            "iteration_count": current_iteration,
            "status": "RUNNING"
        }
    
    # 6. Stage 5: If guardrail failed, retry or terminate
    if guardrail_passed is False:
        return {
            "next_agent": "analyzer",
            "iteration_count": current_iteration,
            "status": "NEEDS_RETRY"
        }
    
    # 7. Completed successfully
    return {
        "next_agent": "__end__",
        "iteration_count": current_iteration,
        "status": "COMPLETED"
    }


def should_continue(state: GlobalMarketState) -> str:
    """Conditional edge logic used by LangGraph graph builder."""
    return state.get("next_agent", "__end__")