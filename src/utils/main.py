"""
Autonomous Market Intelligence Engine - Multi-Agent LangGraph Pipeline

This script implements a production-grade multi-agent loop using LangGraph with:
1. Sub-Agent State Isolation: Sub-agents operate on isolated Pydantic state schemas
   to prevent context bloat and compounding errors across execution nodes.
2. Deterministic Verification: Pydantic structured output validation at state boundaries.
3. Step-Level Observability: Native MLflow span tracing (@mlflow.trace + autolog)
   to log inputs, outputs, token metrics, and execution latency.
"""

import os
import sys
from typing import Annotated, Dict, List, Literal, Optional, TypedDict
from typing_extensions import NotRequired
from pydantic import BaseModel, Field

import mlflow
from mlflow.entities import SpanType

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

# =====================================================================
# 1. MLFLOW OBSERVABILITY & TRACING SETUP
# =====================================================================
# Enable automatic tracing for LangChain / LangGraph calls
mlflow.langchain.autolog(
    log_traces=True,
    run_tracer_inline=True,  # Ensures child spans align in async/sync loops
    silent=True,
)

mlflow.set_experiment("/Market_Intelligence_Agent_Tracing")


# =====================================================================
# 2. SUB-AGENT ISOLATED SCHEMAS & GLOBAL STATE
# =====================================================================
# Sub-Agent 1 Isolated Schema: Retrieval Node
class RetrievalQueryInput(BaseModel):
    sector: str = Field(description="Target market sector for analysis.")
    search_keywords: List[str] = Field(description="Extracted target search keywords.")

class RetrievalOutput(BaseModel):
    retrieved_chunks: List[str] = Field(description="List of relevant raw text context chunks.")
    source_count: int = Field(description="Total distinct sources retrieved.")


# Sub-Agent 2 Isolated Schema: Analysis Node
class AnalysisInput(BaseModel):
    sector: str
    contexts: List[str]

class AnalysisOutput(BaseModel):
    key_findings: List[str] = Field(description="Synthesized market growth drivers.")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence score of analysis.")
    hallucination_flag: bool = Field(description="True if context lacks sufficient backing.")


# Global LangGraph State
class GlobalMarketState(TypedDict):
    """
    Global graph state passed between supervisor and sub-agent nodes.
    Sub-agents receive slices of this state to enforce strict scope boundary.
    """
    user_query: str
    target_sector: str
    retrieved_context: Optional[List[str]]
    analysis_findings: Optional[List[str]]
    confidence_score: Optional[float]
    iteration_count: int
    final_report: Optional[str]
    status: Literal["RUNNING", "NEEDS_RETRY", "COMPLETED", "FAILED"]


# =====================================================================
# 3. SUB-AGENT NODE IMPLEMENTATIONS WITH MLFLOW SPAN TRACING
# =====================================================================

# Initialize default LLM (Configurable via environment variables)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)


@mlflow.trace(name="subagent_retrieval_node", span_type=SpanType.RETRIEVER)
def retrieval_node(state: GlobalMarketState) -> Dict[str, Any]:
    """
    Sub-agent 1: Handles data retrieval.
    Operates ONLY on 'target_sector' input to keep prompt context clean.
    """
    sector = state["target_sector"]
    
    # 1. Structured query generation using isolated input schema
    structured_llm = llm.with_structured_output(RetrievalQueryInput)
    query_params: RetrievalQueryInput = structured_llm.invoke([
        SystemMessage(content="Extract target search keywords for the market sector."),
        HumanMessage(content=f"Sector: {sector}")
    ])
    
    # 2. Simulated vector search / database query execution
    # (Replace mock data with Databricks Vector Search SDK call)
    mock_chunks = [
        f"Subsidies and policy incentives driven by local regulators accelerated {sector} adoption in APAC.",
        f"Enterprise infrastructure spend in {sector} grew 28% year-over-year according to Q2 2026 reports.",
        f"Supply chain bottlenecks in APAC for {sector} remain a moderate risk factor."
    ]
    
    retrieval_result = RetrievalOutput(
        retrieved_chunks=mock_chunks,
        source_count=len(mock_chunks)
    )
    
    # Return slice update to Global State
    return {
        "retrieved_context": retrieval_result.retrieved_chunks,
        "status": "RUNNING"
    }


@mlflow.trace(name="subagent_analysis_node", span_type=SpanType.LLM)
def analysis_node(state: GlobalMarketState) -> Dict[str, Any]:
    """
    Sub-agent 2: Analyzes retrieved context and computes confidence score.
    Isolated from global conversation history—only receives retrieved_context.
    """
    contexts = state.get("retrieved_context", [])
    sector = state["target_sector"]
    current_iterations = state.get("iteration_count", 0) + 1
    
    if not contexts:
        return {
            "status": "NEEDS_RETRY",
            "iteration_count": current_iterations
        }
        
    formatted_context = "\n- ".join(contexts)
    prompt = f"Analyze the following context for sector '{sector}':\n- {formatted_context}"
    
    structured_llm = llm.with_structured_output(AnalysisOutput)
    analysis_res: AnalysisOutput = structured_llm.invoke([
        SystemMessage(content="Synthesize facts strictly from context. Flag hallucinations if context is insufficient."),
        HumanMessage(content=prompt)
    ])
    
    # Deterministic State Boundary Check: If hallucination detected or low confidence
    if analysis_res.hallucination_flag or analysis_res.confidence_score < 0.70:
        next_status = "NEEDS_RETRY" if current_iterations < 3 else "FAILED"
    else:
        next_status = "RUNNING"
        
    return {
        "analysis_findings": analysis_res.key_findings,
        "confidence_score": analysis_res.confidence_score,
        "iteration_count": current_iterations,
        "status": next_status
    }


@mlflow.trace(name="synthesis_formatting_node", span_type=SpanType.CHAIN)
def synthesis_node(state: GlobalMarketState) -> Dict[str, Any]:
    """
    Sub-agent 3: Formats verified analysis findings into final client deliverable.
    """
    sector = state["target_sector"]
    findings = state.get("analysis_findings", [])
    confidence = state.get("confidence_score", 0.0)
    
    formatted_findings = "\n".join([f"• {f}" for f in findings])
    report = (
        f"# Market Intelligence Brief: {sector}\n\n"
        f"**Synthesis Confidence Score:** {confidence * 100:.1f}%\n\n"
        f"### Key Market Drivers:\n{formatted_findings}\n"
    )
    
    return {
        "final_report": report,
        "status": "COMPLETED"
    }


# =====================================================================
# 4. CONDITIONAL ROUTING LOGIC
# =====================================================================
def route_after_analysis(state: GlobalMarketState) -> str:
    """Deterministic routing function based on state status."""
    status = state.get("status")
    if status == "RUNNING":
        return "synthesize"
    elif status == "NEEDS_RETRY":
        return "retrieve"  # Loop back for refined retrieval
    else:
        return "fail_exit"


# =====================================================================
# 5. GRAPH BUILD & ASSEMBLY
# =====================================================================
def build_market_intelligence_graph() -> StateGraph:
    builder = StateGraph(GlobalMarketState)
    
    # Register Nodes
    builder.add_node("retrieve", retrieval_node)
    builder.add_node("analyze", analysis_node)
    builder.add_node("synthesize", synthesis_node)
    
    # Define Edges
    builder.add_edge(START, "retrieve")
    builder.add_edge("retrieve", "analyze")
    
    # Conditional Loop: Reflection & Retry path
    builder.add_conditional_edges(
        "analyze",
        route_after_analysis,
        {
            "synthesize": "synthesize",
            "retrieve": "retrieve",
            "fail_exit": END
        }
    )
    builder.add_edge("synthesize", END)
    
    return builder.compile()


# =====================================================================
# 6. EXECUTION ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    graph = build_market_intelligence_graph()
    
    initial_input: GlobalMarketState = {
        "user_query": "Analyze APAC Green Energy market drivers for Q3 2026",
        "target_sector": "Green Energy",
        "retrieved_context": None,
        "analysis_findings": None,
        "confidence_score": None,
        "iteration_count": 0,
        "final_report": None,
        "status": "RUNNING"
    }
    
    print("\nExecuting LangGraph Multi-Agent Engine...")
    
    # Trace root execution in MLflow
    with mlflow.start_run(run_name="LangGraph_Market_Intelligence_Loop") as run:
        # Set session metadata for MLflow Trace UI
        config = {"configurable": {"thread_id": "session_apac_green_energy_001"}}
        
        final_state = graph.invoke(initial_input, config=config)
        
        print("\n==================================================")
        print("EXECUTION SUMMARY")
        print("==================================================")
        print(f"Status           : {final_state['status']}")
        print(f"Iterations Taken : {final_state['iteration_count']}")
        print(f"Confidence Score : {final_state.get('confidence_score', 'N/A')}")
        print("\nGenerated Final Report:\n")
        print(final_state.get("final_report", "Execution Failed or Terminated Early."))
        print("==================================================")
        print(f"MLflow Run ID    : {run.info.run_id}")
        print("Trace captured in active MLflow experiment server.")