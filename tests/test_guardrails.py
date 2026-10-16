from pathlib import Path
from types import SimpleNamespace

import yaml

from src.utils import guardrails_runner


def test_guardrail_configuration_and_flow_are_present():
    config_path = Path("config/guardrails/config.yml")
    flow_path = Path("config/guardrails/rails.co")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    flow_text = flow_path.read_text(encoding="utf-8")

    assert config["rails"]["output"]["flows"]
    assert "verify market topic alignment" in flow_text


def test_runner_registers_action_and_aligns_neMo_model(monkeypatch):
    model = SimpleNamespace(engine="ollama", model="old", parameters={})
    rails_config = SimpleNamespace(models=[model])

    class FakeRails:
        def __init__(self, _config):
            self.registered = None
            self.status = guardrails_runner.RailStatus.PASSED
            self.checked_types = None

        def register_action(self, action):
            self.registered = action

        def check(self, messages, rail_types):
            self.checked_types = rail_types
            return SimpleNamespace(status=self.status, content=messages[-1]["content"], rail=None)

    monkeypatch.setattr(guardrails_runner.RailsConfig, "from_path", lambda _: rails_config)
    monkeypatch.setattr(guardrails_runner, "LLMRails", FakeRails)
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("AGENT_LLM_MODEL", "ami-llama3.1:8b-4k")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/")

    runner = guardrails_runner.GuardrailsRunner("config/guardrails")
    assert model.engine == "ollama"
    assert model.model == "ami-llama3.1:8b-4k"
    assert model.parameters["base_url"] == "http://localhost:11434/v1"
    assert runner.rails.registered is not None

    accepted = runner.validate_output("Supported market report.", "Market source context.")
    assert accepted["passed_guardrails"] is True
    assert runner.rails.checked_types == [guardrails_runner.RailType.OUTPUT]

    runner.rails.status = guardrails_runner.RailStatus.BLOCKED
    blocked = runner.validate_output("Unsupported report.", "Market source context.")
    assert blocked["passed_guardrails"] is False
    assert blocked["validated_report"] == ""
