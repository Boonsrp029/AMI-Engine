import os
import asyncio
import warnings
from typing import Dict, Any
from nemoguardrails import RailsConfig, LLMRails

# Suppress NeMo deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


class GuardrailsRunner:
    def __init__(self, config_path: str = "config/guardrails"):
        """Initializes NeMo Guardrails configuration."""
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self.config = RailsConfig.from_path(config_path)
        self.rails = LLMRails(self.config)

    def validate_output(self, raw_report: str, context: str) -> Dict[str, Any]:
        """Runs output rails against the raw synthesized report."""
        messages = [
            {
                "role": "context",
                "content": {
                    "context": context,
                    "response": raw_report,
                    "user_input": "Verify market report"
                }
            },
            {
                "role": "user", 
                "content": "Verify market report"
            },
            {
                "role": "assistant",
                "content": raw_report
            }
        ]
        
        response = self.rails.generate(messages=messages)
        
        if isinstance(response, dict):
            output_text = response.get("content", "")
        elif hasattr(response, "content"):
            output_text = response.content
        else:
            output_text = str(response)
            
        # Detect if guardrail triggered a block message
        is_blocked = (
            "outside the authorized financial" in output_text or 
            "flagged for review" in output_text or
            "violates safety guidelines" in output_text
        )
        
        # Return blocked message if flagged, otherwise preserve exact raw report
        final_report = output_text if is_blocked else raw_report
        
        return {
            "validated_report": final_report,
            "passed_guardrails": not is_blocked,
            "raw_output": raw_report
        }


if __name__ == "__main__":
    runner = GuardrailsRunner()
    
    test_context = "APAC Green Energy subsidies grew 28% in H1 2026."
    test_report = "APAC Green Energy subsidies grew 28% in H1 2026."
    
    result = runner.validate_output(raw_report=test_report, context=test_context)
    
    print("\nGuardrail Check Result:")
    print(result)