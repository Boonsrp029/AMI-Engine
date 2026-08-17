"""
Offline Pytest Suite for NeMo Guardrails using FakeLLMModel
"""

import pytest
from nemoguardrails import RailsConfig, LLMRails
from nemoguardrails.testing import FakeLLMModel


def test_guardrails_offline():
    # 1. Load guardrails configuration
    config = RailsConfig.from_path("config/guardrails")
    
    # 2. Mock canned LLM responses ("YES" for safety check, "NO" for hallucination)
    fake_llm = FakeLLMModel(responses=["NO", "YES"])
    
    # 3. Pass mock LLM to LLMRails app
    rails = LLMRails(config, llm=fake_llm)
    
    messages = [
        {
            "role": "context",
            "content": {
                "context": "APAC Green Energy subsidies grew 28% in H1 2026.",
                "response": "APAC Green Energy subsidies grew 28% in H1 2026.",
                "user_input": "Verify market report"
            }
        },
        {
            "role": "user", 
            "content": "Verify market report"
        }
    ]
    
    response = rails.generate(messages=messages)
    assert response is not None