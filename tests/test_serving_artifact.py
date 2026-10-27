"""Actual local MLflow artifact portability, with networking forbidden."""
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
from types import SimpleNamespace

import mlflow
import pandas as pd
from mlflow.models.signature import infer_signature
from packaging.requirements import Requirement

from src.models.register_model import LangGraphAgentPyFunc, _serving_requirements


def test_saved_artifact_embeds_constraints_and_loads_after_relocation(monkeypatch, tmp_path):
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    monkeypatch.setenv("MLFLOW_LOCK_MODEL_DEPENDENCIES", "false")
    monkeypatch.setenv("NEMO_GUARDRAILS_NO_USAGE_STATS", "1")
    def no_network(*args, **kwargs):
        raise AssertionError("Local artifact verification attempted network access")
    monkeypatch.setattr(socket.socket, "connect", no_network)
    original = tmp_path / "original"
    signature = infer_signature(pd.DataFrame({"query": ["fixed query"]}), pd.DataFrame({"response": ["fixed output"]}))
    mlflow.pyfunc.save_model(path=str(original), python_model=LangGraphAgentPyFunc(),
                            code_paths=["src", "config"], signature=signature, pip_requirements=_serving_requirements())
    relocated = tmp_path / "relocated"
    shutil.copytree(original, relocated)
    requirements = (relocated / "requirements.txt").read_text(encoding="utf-8")
    assert (relocated / "code/src/agents/graph.py").is_file()
    assert (relocated / "code/config/guardrails/prompts.yml").is_file()
    assert "-c constraints.txt" in requirements
    assert str(Path.cwd()) not in requirements
    root = Path(__file__).resolve().parents[1]
    normalize = lambda text: {str(Requirement(line.split(" #", 1)[0].strip())) for line in text.splitlines()
                              if line.strip() and not line.lstrip().startswith("#")}
    assert normalize((relocated / "constraints.txt").read_text(encoding="utf-8")) == normalize((root / "constraints-pilot.txt").read_text(encoding="utf-8"))
    loaded = mlflow.pyfunc.load_model(str(relocated))
    loaded.unwrap_python_model().app = SimpleNamespace(invoke=lambda state: {"response": "fixed output"})
    result = loaded.predict(pd.DataFrame({"query": ["fixed query"]}))
    assert result.to_dict("list") == {"response": ["fixed output"]}
    program = '''
import sys,socket
def no_network(*args, **kwargs):
    raise AssertionError("Network access from relocated model")
socket.socket.connect=no_network
import mlflow,pandas as pd
from types import SimpleNamespace
model=mlflow.pyfunc.load_model(sys.argv[1])
model.unwrap_python_model().app=SimpleNamespace(invoke=lambda state:{"response":"fixed output"})
assert model.predict(pd.DataFrame({"query":["fixed query"]})).to_dict("list")=={"response":["fixed output"]}
print("Relocated artifact loaded without repository imports or network access.")
'''
    child = subprocess.run([sys.executable, "-I", "-c", program, str(relocated)], cwd=tmp_path,
                           capture_output=True, text=True, timeout=120)
    assert child.returncode == 0, child.stderr
    assert "Relocated artifact loaded" in child.stdout
