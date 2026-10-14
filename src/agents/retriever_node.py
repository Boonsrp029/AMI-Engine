"""
LangGraph Sub-Agent Node: Databricks AI Search Context Retrieval
"""

import os
from typing import Dict, Any, List
from databricks.sdk import WorkspaceClient
from src.utils.env import load_project_environment
from databricks_langchain import DatabricksVectorSearch
from langchain_core.documents import Document

load_project_environment()

def get_market_intelligence_retriever(
    index_name: str | None = None,
    top_k: int = 5
):
    """Initializes a Databricks AI Search vector store retriever using WorkspaceClient."""
    index_name = index_name or os.getenv("DATABRICKS_VECTOR_SEARCH_INDEX") or "main.market_intelligence.silver_market_chunks_vector_index"
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    client_args = {key: value for key, value in {"host": host, "token": token}.items() if value}
    # In Databricks jobs, use the workspace's configured workload identity.
    w_client = WorkspaceClient(**client_args)

    # Use the index definition as the source of truth. In particular, the
    # Databricks LangChain adapter infers text_column for managed embeddings
    # and raises ValueError if a text_column is also passed explicitly.
    index_info = w_client.vector_search_indexes.get_index(index_name=index_name)
    primary_key = getattr(index_info, "primary_key", None)
    if not primary_key:
        raise ValueError(f"Vector Search index {index_name!r} has no primary key in its metadata")

    delta_sync_spec = getattr(index_info, "delta_sync_index_spec", None)
    embedding_source_columns = getattr(delta_sync_spec, "embedding_source_columns", None) or []
    managed_text_column = next(
        (column.name for column in embedding_source_columns if getattr(column, "name", None)),
        None,
    )
    # Managed embeddings provide their source column through index metadata.
    # Self-managed/direct-access indexes still need a configured text column.
    text_column = None if managed_text_column else (
        os.getenv("DATABRICKS_EMBEDDING_SOURCE_COLUMN") or "clean_content"
    )

    vector_store = DatabricksVectorSearch(
        index_name=index_name,
        workspace_client=w_client,
        primary_key=primary_key,
        text_column=text_column,
    )

    return vector_store.as_retriever(search_kwargs={"k": top_k})


def retrieve_market_context_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph Node: Extracts user query, searches AI Search index,
    and updates state with retrieved market context.
    """
    user_query = state.get("query", "")
    if not user_query:
        return {"context": "", "retrieved_docs": []}

    try:
        retriever = get_market_intelligence_retriever(
            top_k=int(os.getenv("DATABRICKS_SEARCH_TOP_K", "5"))
        )
        documents: List[Document] = retriever.invoke(user_query)

        formatted_context = "\n\n---\n\n".join(
            [f"Source Chunk ID: {doc.metadata.get('chunk_id', doc.metadata.get('feed_id', 'N/A'))}\nContent: {doc.page_content}"
             for doc in documents]
        )
        return {
            "context": formatted_context,
            "retrieved_docs": documents
        }
    except Exception as e:
        print(f"[Warning] Vector Search retrieval failed ({type(e).__name__}).")
        return {
            "context": "",
            "retrieved_docs": [],
            "error": f"Vector Search retrieval failed ({type(e).__name__}).",
        }
