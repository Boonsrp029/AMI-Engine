"""
LangGraph Sub-Agent Node: Databricks AI Search Context Retrieval
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks_langchain import DatabricksVectorSearch
from langchain_core.documents import Document

load_dotenv()

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

    # Use the same source key and text field configured for the Delta Sync index.
    vector_store = DatabricksVectorSearch(
        index_name=index_name,
        workspace_client=w_client,
        primary_key=os.getenv("DATABRICKS_VECTOR_SEARCH_PRIMARY_KEY", "feed_id"),
        text_column=os.getenv("DATABRICKS_EMBEDDING_SOURCE_COLUMN", "clean_content"),
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
            [f"Source Chunk ID: {doc.metadata.get('feed_id', 'N/A')}\nContent: {doc.page_content}" 
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
