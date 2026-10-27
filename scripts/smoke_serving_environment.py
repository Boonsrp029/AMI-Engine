"""No-inference legacy serving imports and fixed-response wrapper contract."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
from types import SimpleNamespace


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("Use a new evidence filename")
    from src.pilot.launch import configure_event_loop
    configure_event_loop()
    from src.models.register_model import LangGraphAgentPyFunc
    from src.agents.graph import app
    from src.agents import retriever_node
    from src.indexers import vector_search_sync
    from src.utils.guardrails_runner import GuardrailsRunner
    # No SDK client, registry call, retriever or real graph invocation is made.
    wrapper = LangGraphAgentPyFunc()
    wrapper.app = SimpleNamespace(invoke=lambda state: {"response": "synthetic fixed response for " + state["query"]})
    result = wrapper.predict(None, {"query": "offline contract check"})
    if result.to_dict("list") != {"response": ["synthetic fixed response for offline contract check"]}:
        raise ValueError("Legacy serving response contract changed")
    record = {"status": "passed", "python": platform.python_version(),
              "packages": {d.metadata["Name"].lower().replace("_", "-"): d.version for d in importlib.metadata.distributions()},
              "imports": ["legacy graph", "registry wrapper", "Databricks retrieval adapter", "indexer", "NeMo runner"],
              "external_calls": 0, "prediction": "fixed graph response only; no inference or registration",
              "qualification": "Isolated imports/wrapper contract only; no Databricks runtime qualification"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print("Serving imports and fixed-response wrapper contract passed; zero inference/registration calls.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
