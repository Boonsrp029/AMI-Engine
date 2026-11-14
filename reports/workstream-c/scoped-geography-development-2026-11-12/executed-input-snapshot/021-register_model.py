"""
MLflow Model Registration for Databricks LangGraph Pipeline
"""

from pathlib import Path
import pandas as pd
import mlflow
import mlflow.pyfunc
from mlflow.models.signature import infer_signature
from src.utils.env import load_project_environment

load_project_environment()


class LangGraphAgentPyFunc(mlflow.pyfunc.PythonModel):
    """MLflow PyFunc wrapper for serving the compiled LangGraph agent."""

    def load_context(self, context):
        import sys
        code_root = context.artifacts.get("code") or "."
        sys.path.insert(0, code_root)
        from src.agents.graph import app
        self.app = app

    def predict(self, context, model_input, params=None):
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
            state = self.app.invoke({"query": str(query)})
            results.append(state.get("response", ""))

        return pd.DataFrame({"response": results})


def _serving_requirements():
    """Let MLflow copy the unchanged constraints into its portable environment."""
    root = Path(__file__).resolve().parents[2]
    constraints = root / "constraints-pilot.txt"
    if not constraints.is_file():
        raise FileNotFoundError("The baseline serving constraints are missing")
    requirements = [line.strip() for line in (root / "requirements-serving.txt").read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.lstrip().startswith("#")]
    return [*requirements, f"-c {constraints}"]


def register_agent_model():
    pip_requirements = _serving_requirements()
    catalog = "main"
    schema = "market_intelligence"
    model_name = "market_agent_model"
    uc_model_path = f"{catalog}.{schema}.{model_name}"

    mlflow.set_registry_uri("databricks-uc")
    mlflow.set_experiment("/Shared/Market_Intelligence_Evaluation")

    # Define input sample & output sample to infer Unity Catalog model signature
    input_example = pd.DataFrame({"query": ["What are the latest clean energy trends in APAC?"]})
    output_example = pd.DataFrame({"response": ["Synthesized analysis based on context..."]})
    signature = infer_signature(input_example, output_example)

    with mlflow.start_run(run_name="Register_LangGraph_Model"):
        print(f"Logging MLflow model with explicit pip requirements to Unity Catalog path: {uc_model_path}...")

        # Log PyFunc model artifact with custom dependencies
        model_info = mlflow.pyfunc.log_model(
            name="langgraph_agent",
            python_model=LangGraphAgentPyFunc(),
            registered_model_name=uc_model_path,
            code_paths=["src", "config"],
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
