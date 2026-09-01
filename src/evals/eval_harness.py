"""
MLflow Agent Evaluation Harness for Databricks LangGraph Pipeline
"""

import os
import pandas as pd
import mlflow
from dotenv import load_dotenv
from src.agents.graph import app  # Import your compiled LangGraph app

load_dotenv()


def run_graph_evaluation():
    """Evaluates compiled LangGraph agent using real Vector Search context."""
    mlflow.set_experiment("/Shared/Market_Intelligence_Evaluation")

    # Define test questions across market sectors
    test_cases = pd.DataFrame([
        {"inputs": "What are the latest APAC clean energy investment trends?"},
        {"inputs": "How are enterprise companies deploying GenAI infrastructure in APAC?"}
    ])

    def real_agent_predict(inputs: pd.DataFrame) -> pd.Series:
        """Invokes the actual LangGraph compiled graph for each evaluation query."""
        results = []
        for _, row in inputs.iterrows():
            user_query = row["inputs"]
            initial_state = {"query": user_query}
            
            # Execute compiled graph
            final_state = app.invoke(initial_state)
            
            # Extract final response or fallback context
            response_text = final_state.get("response", final_state.get("context", ""))
            results.append(response_text)
            
        return pd.Series(results)

    with mlflow.start_run(run_name="LangGraph_Real_Agent_Eval"):
        print("Running predictions through real LangGraph agent...")
        test_cases["predictions"] = real_agent_predict(test_cases)
        
        # Log table artifact
        mlflow.log_table(test_cases, artifact_file="agent_evaluation_output.json")
        
        print("\n==================================================")
        print("REAL AGENT EVALUATION COMPLETED")
        print("==================================================")
        print(test_cases[["inputs", "predictions"]])


if __name__ == "__main__":
    run_graph_evaluation()