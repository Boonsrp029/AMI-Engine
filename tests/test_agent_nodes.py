"""
Unit Test Suite for LangGraph Sub-Agent Nodes

Key Requirements Verified:
1. Zero live API calls (100% mocked via unittest.mock).
2. Independent testing of Retrieval, Analysis, and Synthesis nodes.
3. State mutation verification and deterministic routing checks.
"""

from unittest.mock import MagicMock, patch
import pytest

# Import schema types and node logic from main application module
from main import (
    GlobalMarketState,
    RetrievalQueryInput,
    AnalysisOutput,
    retrieval_node,
    analysis_node,
    synthesis_node,
    route_after_analysis,
)


# =====================================================================
# 1. RETRIEVAL SUB-AGENT NODE TESTS
# =====================================================================
@patch("main.llm")
def test_retrieval_node_success(mock_llm):
    """
    Verifies that retrieval_node extracts search parameters via structured LLM output
    and populates the retrieved_context list in state.
    """
    # Mock LLM structured output response
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = RetrievalQueryInput(
        sector="Green Energy",
        search_keywords=["subsidies", "solar", "grid modernization"]
    )
    mock_llm.with_structured_output.return_value = mock_structured

    initial_state: GlobalMarketState = {
        "user_query": "Analyze APAC Green Energy drivers for Q3 2026",
        "target_sector": "Green Energy",
        "retrieved_context": None,
        "analysis_findings": None,
        "confidence_score": None,
        "iteration_count": 0,
        "final_report": None,
        "status": "RUNNING"
    }

    # Execute Node
    output = retrieval_node(initial_state)

    # Assertions
    assert "retrieved_context" in output
    assert len(output["retrieved_context"]) > 0
    assert output["status"] == "RUNNING"
    
    # Ensure LLM was called with expected Pydantic schema
    mock_llm.with_structured_output.assert_called_once_with(RetrievalQueryInput)


# =====================================================================
# 2. ANALYSIS SUB-AGENT NODE TESTS
# =====================================================================
@patch("main.llm")
def test_analysis_node_high_confidence_pass(mock_llm):
    """
    Verifies that analysis_node approves findings when confidence >= 0.70 
    and hallucination_flag is False.
    """
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = AnalysisOutput(
        key_findings=["Grid modernization spending up 28% in APAC", "Policy subsidies confirmed"],
        confidence_score=0.88,
        hallucination_flag=False
    )
    mock_llm.with_structured_output.return_value = mock_structured

    state: GlobalMarketState = {
        "user_query": "Analyze APAC Green Energy",
        "target_sector": "Green Energy",
        "retrieved_context": ["Subsidies increased solar adoption in APAC."],
        "analysis_findings": None,
        "confidence_score": None,
        "iteration_count": 0,
        "final_report": None,
        "status": "RUNNING"
    }

    output = analysis_node(state)

    assert output["confidence_score"] == 0.88
    assert len(output["analysis_findings"]) == 2
    assert output["status"] == "RUNNING"
    assert output["iteration_count"] == 1


@patch("main.llm")
def test_analysis_node_triggers_retry_on_low_confidence(mock_llm):
    """
    Verifies that analysis_node sets status to NEEDS_RETRY when 
    confidence score is below threshold or hallucination is flagged.
    """
    mock_structured = MagicMock()
    mock_structured.invoke.return_value = AnalysisOutput(
        key_findings=["Vague statement"],
        confidence_score=0.45,  # Below 0.70 threshold
        hallucination_flag=True
    )
    mock_llm.with_structured_output.return_value = mock_structured

    state: GlobalMarketState = {
        "user_query": "Analyze APAC Green Energy",
        "target_sector": "Green Energy",
        "retrieved_context": ["Vague unverified text"],
        "analysis_findings": None,
        "confidence_score": None,
        "iteration_count": 1,
        "final_report": None,
        "status": "RUNNING"
    }

    output = analysis_node(state)

    assert output["status"] == "NEEDS_RETRY"
    assert output["iteration_count"] == 2


# =====================================================================
# 3. SYNTHESIS SUB-AGENT NODE TESTS
# =====================================================================
def test_synthesis_node_report_generation():
    """
    Verifies that synthesis_node formats validated analysis findings into 
    the final Markdown report string without requiring LLM calls.
    """
    state: GlobalMarketState = {
        "user_query": "Analyze APAC Green Energy",
        "target_sector": "Green Energy",
        "retrieved_context": ["Context 1"],
        "analysis_findings": [
            "Subsidies driven by local regulators accelerated adoption.",
            "Infrastructure spend grew 28% year-over-year."
        ],
        "confidence_score": 0.92,
        "iteration_count": 1,
        "final_report": None,
        "status": "RUNNING"
    }

    output = synthesis_node(state)

    assert output["status"] == "COMPLETED"
    assert "# Market Intelligence Brief: Green Energy" in output["final_report"]
    assert "92.0%" in output["final_report"]
    assert "• Subsidies driven by local regulators" in output["final_report"]


# =====================================================================
# 4. CONDITIONAL ROUTING LOGIC TESTS
# =====================================================================
@pytest.mark.parametrize(
    "status_input, expected_route",
    [
        ("RUNNING", "synthesize"),
        ("NEEDS_RETRY", "retrieve"),
        ("FAILED", "fail_exit"),
    ],
)
def test_route_after_analysis(status_input, expected_route):
    """
    Parameterized test validating deterministic graph routing choices 
    based on state status.
    """
    state: GlobalMarketState = {
        "user_query": "Query",
        "target_sector": "Green Energy",
        "retrieved_context": None,
        "analysis_findings": None,
        "confidence_score": None,
        "iteration_count": 1,
        "final_report": None,
        "status": status_input
    }

    actual_route = route_after_analysis(state)
    assert actual_route == expected_route