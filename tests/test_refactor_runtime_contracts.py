"""Offline contracts around the refactor's unchanged runtime boundaries."""

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
import yaml
from langchain_core.documents import Document

import main
from src.agents import graph, local_retriever, retriever_node
from src.evals import run_ragas
from src.models import deploy_endpoint, register_model
from src.utils import env


@pytest.fixture(autouse=True)
def isolate_environment():
    with patch.dict(os.environ):
        yield


def test_environment_precedence(tmp_path, monkeypatch):
    monkeypatch.setattr(env, "PROJECT_ROOT", tmp_path)
    (tmp_path / ".databricks").mkdir()
    (tmp_path / ".databricks/.databricks.env").write_text(
        "AMI_TEST_PROCESS=workspace\nAMI_TEST_WORKSPACE=workspace\n", encoding="utf-8")
    (tmp_path / ".env").write_text(
        "AMI_TEST_PROCESS=general\nAMI_TEST_WORKSPACE=general\nAMI_TEST_GENERAL=general\n", encoding="utf-8")
    monkeypatch.setenv("AMI_TEST_PROCESS", "process")
    monkeypatch.delenv("AMI_TEST_WORKSPACE", raising=False)
    monkeypatch.delenv("AMI_TEST_GENERAL", raising=False)
    env.load_project_environment()
    assert [os.getenv(k) for k in ("AMI_TEST_PROCESS", "AMI_TEST_WORKSPACE", "AMI_TEST_GENERAL")] == [
        "process", "workspace", "general"]
    # dotenv writes are not tracked by monkeypatch itself.
    monkeypatch.delenv("AMI_TEST_WORKSPACE")
    monkeypatch.delenv("AMI_TEST_GENERAL")


@pytest.mark.parametrize("backend,dataset,tracking", [
    ("local", "data/local_eval_dataset.json", "sqlite:///reports/mlflow.db"),
    ("databricks", "data/gold_eval_dataset.json", "existing-tracking"),
])
def test_cli_defaults_and_compatibility_entrypoint(monkeypatch, backend, dataset, tracking):
    import src.evals.evaluate_run as compatibility
    assert compatibility._evaluation_main is main.main
    monkeypatch.setattr(sys, "argv", ["main", "--retriever-backend", backend])
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "existing-tracking")
    evaluate = MagicMock()
    monkeypatch.setattr(run_ragas, "run_evaluation", evaluate)
    main.main()
    evaluate.assert_called_once_with(dataset, "reports", limit=None, judge_repeats=1,
                                     frozen_inputs_path=None, fresh_judge=False)
    assert os.environ["RETRIEVER_BACKEND"] == backend
    assert os.environ["MLFLOW_TRACKING_URI"] == tracking


def test_cli_explicit_options(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["main", "--dataset", "cases.json", "--output-dir", "scratch",
        "--tracking-uri", "sqlite:///scratch.db", "--limit", "2", "--judge-repeats", "3",
        "--local-corpus", "corpus.json", "--local-retriever-mode", "dense", "--retriever-backend", "local",
        "--frozen-inputs", "frozen.json", "--fresh-judge"])
    evaluate = MagicMock()
    monkeypatch.setattr(run_ragas, "run_evaluation", evaluate)
    main.main()
    evaluate.assert_called_once_with("cases.json", "scratch", limit=2, judge_repeats=3,
                                     frozen_inputs_path="frozen.json", fresh_judge=True)
    assert os.environ["LOCAL_RETRIEVAL_CORPUS"] == "corpus.json"
    assert os.environ["LOCAL_RETRIEVER_MODE"] == "dense"
    assert os.environ["MLFLOW_TRACKING_URI"] == "sqlite:///scratch.db"


def test_context_formats_and_successful_graph(monkeypatch):
    docs = [Document(page_content="Evidence A", metadata={"feed_id": "a"}),
            Document(page_content="Evidence B", metadata={"chunk_id": "b"})]
    monkeypatch.setattr(retriever_node, "get_market_intelligence_retriever",
                        lambda **_: SimpleNamespace(invoke=lambda _: docs))
    raw = retriever_node.retrieve_market_context_node({"query": "Q"})
    assert raw["context"] == "Source Chunk ID: a\nContent: Evidence A\n\n---\n\nSource Chunk ID: b\nContent: Evidence B"
    monkeypatch.setattr(graph, "retrieve_market_context_node", lambda _: raw)
    structured = MagicMock()
    structured.invoke.return_value = graph.Analysis(findings=["Fact"], confidence=0.8, response="Brief")
    model = MagicMock()
    model.with_structured_output.return_value = structured
    monkeypatch.setattr(graph, "_chat_model", lambda: model)
    monkeypatch.setattr(graph, "GuardrailsRunner", lambda: SimpleNamespace(validate_output=lambda **_: {
        "passed_guardrails": True, "validated_report": "Brief"}))
    result = graph.query_agent(" Q ")
    assert result == {"query": "Q", "context": "Evidence A\n\n---\n\nEvidence B",
        "retrieved_contexts": ["Evidence A", "Evidence B"], "citations": [{"feed_id": "a"}, {"chunk_id": "b"}],
        "findings": ["Fact"], "confidence": 0.8, "response": "Brief", "status": "ok", "error": ""}
    messages = structured.invoke.call_args.args[0]
    assert messages[0].content == (
        "You are a careful market research analyst. Use only the supplied evidence. "
        "Separate supported findings from uncertainty, do not invent facts or citations, "
        "and produce a concise answer. If evidence is insufficient, say so. "
        "Set confidence to a decimal from 0.0 to 1.0 inclusive.The output must be in English language only.")
    assert messages[1].content == "Question:\nQ\n\nRetrieved evidence:\nEvidence A\n\n---\n\nEvidence B"


def test_local_bm25_and_dense_ranking_contract(tmp_path, monkeypatch):
    directory = tmp_path / "silver_level"
    directory.mkdir()
    corpus = directory / "corpus.json"
    corpus.write_text(json.dumps([
        {"feed_id": "a", "title": "A", "clean_content": "nickel"},
        {"feed_id": "b", "title": "B", "clean_content": "nickel"},
        {"feed_id": "c", "title": "C", "clean_content": "grids"},
    ]), encoding="utf-8")
    monkeypatch.setenv("LOCAL_RETRIEVAL_CORPUS", str(corpus))
    monkeypatch.setenv("LOCAL_RETRIEVER_MODE", "bm25")
    retriever = local_retriever.create_local_retriever(3)
    docs = retriever.invoke("nickel")
    assert [d.metadata["feed_id"] for d in docs] == ["a", "b"]
    assert docs[0].metadata == {"feed_id": "a", "title": "A", "medallion_layer": "silver"}
    assert docs[0].page_content == "A nickel"
    assert retriever.invoke("unmatched") == []
    monkeypatch.setenv("LOCAL_RETRIEVER_MODE", "dense")
    model = MagicMock()
    model.encode.side_effect = [np.array([[1., 0.], [1., 0.], [0., 1.]]), np.array([1., 0.])]
    factory = MagicMock(return_value=model)
    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=factory))
    local_retriever._dense_index.cache_clear()
    try:
        dense = local_retriever.create_local_retriever(3)
        assert [d.metadata["feed_id"] for d in dense.invoke("nickel")] == ["a", "b", "c"]
        assert factory.call_args.kwargs == {"local_files_only": True}
    finally:
        local_retriever._dense_index.cache_clear()


@pytest.mark.parametrize("shape", ["dataframe", "fallback_column", "dict", "sequence"])
def test_pyfunc_input_and_response_contract(shape):
    model = register_model.LangGraphAgentPyFunc()
    model.app = MagicMock()
    model.app.invoke.side_effect = lambda state: {"response": f"Brief {state['query']}"}
    inputs = {"dataframe": pd.DataFrame({"query": ["a", "b"]}),
              "fallback_column": pd.DataFrame({"text": ["a", "b"]}),
              "dict": {"query": "a"}, "sequence": ["a", "b"]}
    result = model.predict(None, inputs[shape])
    assert list(result.columns) == ["response"]
    assert result.response.tolist() == (["Brief a"] if shape == "dict" else ["Brief a", "Brief b"])


def test_registration_calls_and_output(monkeypatch, capsys):
    events = []
    @contextmanager
    def start_run(**kwargs):
        events.append(("start", kwargs))
        yield SimpleNamespace(info=SimpleNamespace(run_id="fixed"))
        events.append(("end",))
    monkeypatch.setattr(register_model.mlflow, "start_run", start_run)
    monkeypatch.setattr(register_model.mlflow, "set_registry_uri", lambda x: events.append(("registry", x)))
    monkeypatch.setattr(register_model.mlflow, "set_experiment", lambda x: events.append(("experiment", x)))
    monkeypatch.setattr(register_model, "infer_signature", lambda *args: "signature")
    log_model = MagicMock(return_value=SimpleNamespace(model_uri="models:/fixed"))
    monkeypatch.setattr(register_model.mlflow.pyfunc, "log_model", log_model)
    register_model.register_agent_model()
    assert events == [("registry", "databricks-uc"), ("experiment", "/Shared/Market_Intelligence_Evaluation"),
                      ("start", {"run_name": "Register_LangGraph_Model"}), ("end",)]
    kwargs = log_model.call_args.kwargs
    assert kwargs["name"] == "langgraph_agent"
    assert kwargs["registered_model_name"] == "main.market_intelligence.market_agent_model"
    assert kwargs["code_paths"] == ["src", "config"]
    assert kwargs["signature"] == "signature"
    assert isinstance(kwargs["python_model"], register_model.LangGraphAgentPyFunc)
    assert kwargs["input_example"].to_dict("list") == {"query": ["What are the latest clean energy trends in APAC?"]}
    requirements = Path(register_model.__file__).resolve().parents[2] / "requirements-serving.txt"
    assert kwargs["pip_requirements"] == [line.strip() for line in requirements.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")]
    assert capsys.readouterr().out == (
        "Logging MLflow model with explicit pip requirements to Unity Catalog path: main.market_intelligence.market_agent_model...\n"
        + "=" * 50 + "\nMODEL REGISTRATION COMPLETED\n" + "=" * 50
        + "\nModel URI: models:/fixed\nRegistered Version in UC: main.market_intelligence.market_agent_model\n")


@pytest.mark.parametrize("exists", [True, False])
def test_deployment_preserves_sdk_requests(monkeypatch, capsys, exists):
    for key, value in {"DATABRICKS_HOST": "https://example.invalid", "DATABRICKS_MODEL_VERSION": "2",
        "DATABRICKS_SERVING_ENDPOINT": "test-endpoint", "DATABRICKS_VECTOR_SEARCH_INDEX": "cat.schema.idx",
        "DATABRICKS_VECTOR_SEARCH_ENDPOINT": "vector-endpoint", "AGENT_LLM_PROVIDER": "openai",
        "AGENT_LLM_MODEL": "test-model", "LLM_API_KEY_SECRET_SCOPE": "scope", "LLM_API_KEY_SECRET_KEY": "llm",
        "DATABRICKS_AUTH_SECRET_SCOPE": "scope", "DATABRICKS_CLIENT_ID_SECRET_KEY": "id",
        "DATABRICKS_CLIENT_SECRET_SECRET_KEY": "secret"}.items():
        monkeypatch.setenv(key, value)
    workspace = MagicMock()
    if not exists:
        workspace.serving_endpoints.get.side_effect = deploy_endpoint.NotFound("missing")
    factory = MagicMock(return_value=workspace)
    monkeypatch.setattr(deploy_endpoint, "WorkspaceClient", factory)
    deploy_endpoint.deploy_serving_endpoint()
    factory.assert_called_once_with(host="https://example.invalid")
    workspace.serving_endpoints.get.assert_called_once_with(name="test-endpoint")
    if exists:
        request = workspace.serving_endpoints.update_config_and_wait.call_args.kwargs
        entities = request["served_entities"]
        workspace.serving_endpoints.create_and_wait.assert_not_called()
    else:
        request = workspace.serving_endpoints.create_and_wait.call_args.kwargs
        entities = request["config"].served_entities
        workspace.serving_endpoints.update_config_and_wait.assert_not_called()
    assert request["name"] == "test-endpoint"
    assert entities[0].as_dict() == {"entity_name": "main.market_intelligence.market_agent_model",
        "entity_version": "2", "scale_to_zero_enabled": True, "workload_size": "Small",
        "environment_vars": {"DATABRICKS_HOST": "https://example.invalid", "DATABRICKS_VECTOR_SEARCH_INDEX": "cat.schema.idx",
            "DATABRICKS_VECTOR_SEARCH_ENDPOINT": "vector-endpoint", "AGENT_LLM_PROVIDER": "openai",
            "AGENT_LLM_MODEL": "test-model", "OPENAI_API_KEY": "{{secrets/scope/llm}}",
            "DATABRICKS_CLIENT_ID": "{{secrets/scope/id}}", "DATABRICKS_CLIENT_SECRET": "{{secrets/scope/secret}}"}}
    output = capsys.readouterr().out
    action = "Endpoint 'test-endpoint' exists. Updating configuration..." if exists else "Creating new Model Serving Endpoint 'test-endpoint'..."
    assert output == ("Provisioning Model Serving Endpoint 'test-endpoint' for model 'main.market_intelligence.market_agent_model' v2...\n"
        + action + "\n" + "=" * 50 + "\nMODEL SERVING ENDPOINT DEPLOYED SUCCESSFULLY\n" + "=" * 50
        + "\nEndpoint Name: test-endpoint\nURL: https://example.invalid/serving-endpoints/test-endpoint/invocations\n")


def test_active_guardrail_yaml_contract():
    config = yaml.safe_load(Path("config/guardrails/config.yml").read_text(encoding="utf-8"))
    assert config == {"colang_version": "1.0", "models": [{"type": "main", "engine": "ollama", "model": "ami-llama3.1:8b-4k"}],
        "rails": {"input": {"flows": ["self check input"]},
                  "output": {"flows": ["self check hallucination", "verify market topic alignment"]}}}
