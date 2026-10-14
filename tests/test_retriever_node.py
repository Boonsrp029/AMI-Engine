from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.agents import retriever_node


def test_retriever_passes_sdk_bearer_token_to_ai_search_adapter(monkeypatch):
    index_info = SimpleNamespace(
        primary_key="feed_id",
        delta_sync_index_spec=SimpleNamespace(
            embedding_source_columns=[SimpleNamespace(name="clean_content")]
        ),
    )
    workspace_client = MagicMock()
    workspace_client.config.host = "https://dbc-567e5110-5578.cloud.databricks.com"
    workspace_client.config.authenticate.return_value = {
        "Authorization": "Bearer short-lived-token"
    }
    workspace_client.vector_search_indexes.get_index.return_value = index_info
    vector_store = MagicMock()
    vector_store.as_retriever.return_value = "retriever"

    monkeypatch.setattr(retriever_node, "WorkspaceClient", lambda **_: workspace_client)
    adapter = MagicMock(return_value=vector_store)
    monkeypatch.setattr(retriever_node, "DatabricksVectorSearch", adapter)
    monkeypatch.setenv("DATABRICKS_HOST", "https://dbc-567e5110-5578.cloud.databricks.com")
    monkeypatch.setenv("DATABRICKS_VECTOR_SEARCH_INDEX", "main.market_intelligence.test_index")

    result = retriever_node.get_market_intelligence_retriever(top_k=2)

    assert result == "retriever"
    adapter.assert_called_once_with(
        index_name="main.market_intelligence.test_index",
        workspace_client=workspace_client,
        client_args={
            "workspace_url": "https://dbc-567e5110-5578.cloud.databricks.com",
            "personal_access_token": "dapi7a47fe46205d6e82d41a182bf88e1f95",
        },
        primary_key="feed_id",
        text_column=None,
    )
    vector_store.as_retriever.assert_called_once_with(search_kwargs={"k": 2})


def test_retriever_rejects_missing_authorization_header(monkeypatch):
    workspace_client = MagicMock()
    workspace_client.config.authenticate.return_value = {}
    monkeypatch.setattr(retriever_node, "WorkspaceClient", lambda **_: workspace_client)

    with pytest.raises(ValueError, match="did not provide an Authorization header"):
        retriever_node.get_market_intelligence_retriever()
