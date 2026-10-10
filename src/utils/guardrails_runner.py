import os
import warnings
from pathlib import Path
from typing import Dict, Any
from nemoguardrails import RailsConfig, LLMRails
from config.guardrails.actions import check_topic_safety

# Suppress NeMo deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


class GuardrailsRunner:
    def __init__(self, config_path: str | None = None):
        """Initializes NeMo Guardrails configuration."""
        if config_path is None:
            project_root = Path(__file__).resolve().parents[2]
            config_path = str(project_root / "config" / "guardrails")
        if not Path(config_path).exists():
            raise FileNotFoundError(f"NeMo Guardrails config not found: {config_path}")
        self.config = RailsConfig.from_path(config_path)
        self._configure_model()
        self.rails = LLMRails(self.config)
        self.rails.register_action(check_topic_safety)

    def _configure_model(self) -> None:
        """Keep NeMo's judge aligned with the graph's configured provider/model."""
        provider = os.getenv("AGENT_LLM_PROVIDER", os.getenv("LLM_PROVIDER", "ollama")).lower()
        model_name = os.getenv("AGENT_LLM_MODEL") or os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
        if not self.config.models:
            raise ValueError("NeMo Guardrails config must declare one main model")
        model = self.config.models[0]
        parameters = dict(getattr(model, "parameters", None) or {})
        if provider == "ollama":
            model.engine = "ollama"
            model.model = model_name
            parameters["base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        elif provider in {"groq", "openai"}:
            api_key_name = "GROQ_API_KEY" if provider == "groq" else "OPENAI_API_KEY"
            api_key = os.getenv(api_key_name)
            if not api_key:
                raise ValueError(f"{api_key_name} is required for NeMo Guardrails")
            model.engine = "openai"
            model.model = model_name
            parameters["openai_api_key"] = api_key
            if provider == "groq":
                parameters["base_url"] = "https://api.groq.com/openai/v1"
        else:
            raise ValueError(f"Unsupported guardrail model provider: {provider!r}")
        model.parameters = parameters

    def validate_output(self, raw_report: str, context: str, user_input: str = "Verify market report") -> Dict[str, Any]:
        """Runs output rails against the raw synthesized report."""
        messages = [
            {
                "role": "context",
                "content": {
                    "context": context,
                    "response": raw_report,
                    "user_input": user_input
                }
            },
            {
                "role": "user", 
                "content": user_input
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
            
        # The output must be present and unchanged. A rail block, model rewrite,
        # or unrecognized response fails closed instead of being accepted.
        passed = bool(raw_report.strip()) and output_text.strip() == raw_report.strip()
        final_report = raw_report if passed else ""
        
        return {
            "validated_report": final_report,
            "passed_guardrails": passed,
            "raw_output": raw_report
        }


if __name__ == "__main__":
    runner = GuardrailsRunner()
    
    test_context = "APAC Green Energy subsidies grew 28% in H1 2026."
    test_report = "APAC Green Energy subsidies grew 28% in H1 2026."
    
    result = runner.validate_output(raw_report=test_report, context=test_context)
    
    print("\nGuardrail Check Result:")
    print(result)
