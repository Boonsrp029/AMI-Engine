import os
import pytest
import yaml
from src.agents.supervisor import GlobalMarketState, supervisor_node, should_continue


def test_agent_config_integrity():
    """Verify agent_config.yaml loads with essential routing parameters."""
    config_path = "config/agent_config.yaml"
    assert os.path.exists(config_path), f"Configuration file missing at {config_path}"
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    assert "supervisor" in config
    assert "max_iterations" in config["supervisor"]
    assert "analyzer" in config
    assert "confidence_threshold" in config["analyzer"]


def test_supervisor_initial_routing():
    """Verify supervisor routes to retriever when context is missing."""
    initial_state: GlobalMarketState = {
        "user_query": "Analyze APAC Green Energy Q3 2026",
        "target_sector": "Energy",
        "messages": [],
        "next_agent": None,
        "iteration_count": 0,
        "confidence_score": 0.0,
        "status": "RUNNING",
        "retrieved_contexts": [],
        "analysis_findings": None,
        "synthesis": None,
        "final_report": None,
        "citations": None,
        "guardrail_passed": None,
        "guardrail_feedback": None,
        "error_log": []
    }
    
    update = supervisor_node(initial_state)
    assert update["next_agent"] == "retriever"
    assert update["iteration_count"] == 1


def test_supervisor_max_iteration_gate():
    """Verify supervisor enforces loop termination when iteration limit is hit."""
    maxed_state: GlobalMarketState = {
        "user_query": "Analyze APAC Green Energy Q3 2026",
        "target_sector": "Energy",
        "messages": [],
        "next_agent": "retriever",
        "iteration_count": 3,
        "confidence_score": 0.5,
        "status": "RUNNING",
        "retrieved_contexts": ["Some context"],
        "analysis_findings": None,
        "synthesis": None,
        "final_report": None,
        "citations": None,
        "guardrail_passed": None,
        "guardrail_feedback": None,
        "error_log": []
    }
    
    update = supervisor_node(maxed_state)
    assert update["next_agent"] == "__end__"
    assert update["status"] == "FAILED"


def test_should_continue_router():
    """Verify conditional edge helper returns target node string."""
    state = {"next_agent": "synthesizer"}
    assert should_continue(state) == "synthesizer"
    
    empty_state = {}
    assert should_continue(empty_state) == "__end__"