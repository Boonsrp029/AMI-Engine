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

# Force Databricks SDK to use PAT token authentication explicitly
os.environ["DATABRICKS_AUTH_TYPE"] = "pat"


def get_market_intelligence_retriever(
    index_name: str = "main.market_intelligence.silver_market_chunks_vector_index",
    top_k: int = 5
):
    """Initializes a Databricks AI Search vector store retriever using WorkspaceClient."""
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")

    if not host or not token:
        raise ValueError("DATABRICKS_HOST and DATABRICKS_TOKEN must be defined in .env")

    # Instantiate Databricks SDK WorkspaceClient with explicit host and token
    w_client = WorkspaceClient(
        host=host,
        token=token,
        auth_type="pat",
    )

    # Initialize vector store without text_column to let Unity Catalog auto-resolve it
    vector_store = DatabricksVectorSearch(
        index_name=index_name,
        workspace_client=w_client
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
        retriever = get_market_intelligence_retriever(top_k=5)
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
        print(f"[Warning] Vector Search Retrieval Failed: {e}")
        return {
            "context": "No index context available.",
            "retrieved_docs": []
        }