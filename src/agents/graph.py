import os
from dotenv import load_dotenv

# Load environment variables before importing Databricks modules
load_dotenv()

# Rest of your imports follow
from typing import TypedDict, List, Any
from langgraph.graph import StateGraph, END
from src.agents.retriever_node import retrieve_market_context_node
from databricks_langchain import DatabricksVectorSearch


class MarketGraphState(TypedDict):
    query: str
    context: str
    retrieved_docs: List[Any]
    response: str


def generate_synthesis_node(state: MarketGraphState) -> MarketGraphState:
    """Generates final market intelligence summary using retrieved Silver context."""
    context = state["context"]
    query = state["query"]
    
    # Prompt synthesis logic (e.g., using ChatGroq or ChatDatabricks)
    synthesized_text = f"Synthesized analysis based on context:\n{context[:300]}..."
    
    return {"response": synthesized_text}


# Build StateGraph
workflow = StateGraph(MarketGraphState)

workflow.add_node("retrieve_context", retrieve_market_context_node)
workflow.add_node("generate_synthesis", generate_synthesis_node)

workflow.set_entry_point("retrieve_context")
workflow.add_edge("retrieve_context", "generate_synthesis")
workflow.add_edge("generate_synthesis", END)

app = workflow.compile()

if __name__ == "__main__":
    test_state = {"query": "Latest trends in tech capital expenditure"}
    result = app.invoke(test_state)
    print("Retrieved Context Length:", len(result["context"]))
    print("Response:", result["response"])