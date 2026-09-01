"""
MLflow Model Registration for Databricks LangGraph Pipeline
"""

import os
import pandas as pd
import mlflow
import mlflow.pyfunc
from mlflow.models.signature import infer_signature
from dotenv import load_dotenv

load_dotenv()


class LangGraphAgentPyFunc(mlflow.pyfunc.PythonModel):
    """MLflow PyFunc wrapper for serving the compiled LangGraph agent."""

    def load_context(self, context):
        import sys
        sys.path.insert(0, context.artifacts.get("code") or ".")
        from src.agents.graph import app
        self.app = app

    def predict(self, context, model_input):
        """Processes incoming requests and returns synthesized context/responses."""
        results = []
        if hasattr(model_input, "iterrows"):
            queries = (
                model_input["query"].tolist()
                if "query" in model_input.columns
                else model_input.iloc[:, 0].tolist()
            )
        elif isinstance(model_input, dict):
            queries = [model_input.get("query", "")]
        else:
            queries = list(model_input)

        for query in queries:
            state = self.app.invoke({"query": query})
            results.append(state.get("response", state.get("context", "")))

        return results


def register_agent_model():
    catalog = "main"
    schema = "market_intelligence"
    model_name = "market_agent_model"
    uc_model_path = f"{catalog}.{schema}.{model_name}"

    mlflow.set_registry_uri("databricks-uc")
    mlflow.set_experiment("/Shared/Market_Intelligence_Evaluation")

    # Define input sample & output sample to infer Unity Catalog model signature
    input_example = pd.DataFrame({"query": ["What are the latest clean energy trends in APAC?"]})
    output_example = ["Synthesized analysis based on context..."]
    signature = infer_signature(input_example, output_example)

    # Pin dependencies to resolve the protobuf conflict
    pip_requirements = [
        "protobuf>=5.29.5,<6.0.0",
        "googleapis-common-protos<1.75.0",
        "databricks-vectorsearch",
        "databricks-sdk",
        "databricks-langchain",
        "langchain-core",
        "langgraph",
        "pandas",
        "python-dotenv"
    ]

    with mlflow.start_run(run_name="Register_LangGraph_Model") as run:
        print(f"Logging MLflow model with explicit pip requirements to Unity Catalog path: {uc_model_path}...")

        # Log PyFunc model artifact with custom dependencies
        model_info = mlflow.pyfunc.log_model(
            artifact_path="langgraph_agent",
            python_model=LangGraphAgentPyFunc(),
            registered_model_name=uc_model_path,
            code_paths=["src"],
            signature=signature,
            input_example=input_example,
            pip_requirements=pip_requirements
        )

        print("==================================================")
        print("MODEL REGISTRATION COMPLETED")
        print("==================================================")
        print(f"Model URI: {model_info.model_uri}")
        print(f"Registered Version in UC: {uc_model_path}")


if __name__ == "__main__":
    register_agent_model()