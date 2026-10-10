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

        def register_action(self, action):
            self.registered = action

    monkeypatch.setattr(guardrails_runner.RailsConfig, "from_path", lambda _: rails_config)
    monkeypatch.setattr(guardrails_runner, "LLMRails", FakeRails)
    monkeypatch.setenv("AGENT_LLM_PROVIDER", "ollama")
    monkeypatch.setenv("AGENT_LLM_MODEL", "qwen2.5:14b")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/")

    runner = guardrails_runner.GuardrailsRunner("config/guardrails")
    assert model.engine == "ollama"
    assert model.model == "qwen2.5:14b"
    assert model.parameters["base_url"] == "http://localhost:11434"
    assert runner.rails.registered is not None
