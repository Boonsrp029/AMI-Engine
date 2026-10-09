"""
Databricks Model Serving Endpoint Provisioning for Unity Catalog Registered Agent Model
"""

import os
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedEntityInput

load_dotenv()


def deploy_serving_endpoint():
    endpoint_name = os.getenv("DATABRICKS_SERVING_ENDPOINT", "market_agent_serving_endpoint")
    model_uc_path = "main.market_intelligence.market_agent_model"
    model_version = os.getenv("DATABRICKS_MODEL_VERSION")
    if not model_version:
        raise ValueError("Set DATABRICKS_MODEL_VERSION to a registered Unity Catalog model version before deploying.")

    host = os.getenv("DATABRICKS_HOST")
    if not host:
        raise ValueError("DATABRICKS_HOST must be configured")

    provider = os.getenv("AGENT_LLM_PROVIDER", "").lower()
    model_name = os.getenv("AGENT_LLM_MODEL", "")
    if provider not in {"ollama", "groq", "openai"} or not model_name:
        raise ValueError("Set AGENT_LLM_PROVIDER and AGENT_LLM_MODEL before deploying")

    env_vars = {
        "DATABRICKS_HOST": host,
        "DATABRICKS_VECTOR_SEARCH_INDEX": os.getenv(
            "DATABRICKS_VECTOR_SEARCH_INDEX", "main.market_intelligence.silver_market_chunks_vector_index"
        ),
        "DATABRICKS_VECTOR_SEARCH_ENDPOINT": os.getenv(
            "DATABRICKS_VECTOR_SEARCH_ENDPOINT", "market_intelligence_vs_endpoint"
        ),
        "AGENT_LLM_PROVIDER": provider,
        "AGENT_LLM_MODEL": model_name,
    }
    if provider in {"groq", "openai"}:
        secret_scope = os.getenv("LLM_API_KEY_SECRET_SCOPE")
        secret_key = os.getenv("LLM_API_KEY_SECRET_KEY")
        if not secret_scope or not secret_key:
            raise ValueError("Configure LLM_API_KEY_SECRET_SCOPE and LLM_API_KEY_SECRET_KEY")
        env_vars["GROQ_API_KEY" if provider == "groq" else "OPENAI_API_KEY"] = (
            f"{{{{secrets/{secret_scope}/{secret_key}}}}}"
        )
    elif provider == "ollama":
        ollama_url = os.getenv("OLLAMA_BASE_URL")
        if not ollama_url:
            raise ValueError("Serving with Ollama requires a reachable OLLAMA_BASE_URL")
        env_vars["OLLAMA_BASE_URL"] = ollama_url

    # Serving uses an OAuth service principal for workspace API access; its
    # credentials are resolved by Databricks from secret references.
    dbx_secret_scope = os.getenv("DATABRICKS_AUTH_SECRET_SCOPE")
    client_id_secret = os.getenv("DATABRICKS_CLIENT_ID_SECRET_KEY")
    client_secret_secret = os.getenv("DATABRICKS_CLIENT_SECRET_SECRET_KEY")
    if not all((dbx_secret_scope, client_id_secret, client_secret_secret)):
        raise ValueError(
            "Configure DATABRICKS_AUTH_SECRET_SCOPE, DATABRICKS_CLIENT_ID_SECRET_KEY, "
            "and DATABRICKS_CLIENT_SECRET_SECRET_KEY for serving identity"
        )
    env_vars["DATABRICKS_CLIENT_ID"] = f"{{{{secrets/{dbx_secret_scope}/{client_id_secret}}}}}"
    env_vars["DATABRICKS_CLIENT_SECRET"] = f"{{{{secrets/{dbx_secret_scope}/{client_secret_secret}}}}}"

    w = WorkspaceClient(host=host)

    print(f"Provisioning Model Serving Endpoint '{endpoint_name}' for model '{model_uc_path}' v{model_version}...")

    # Configure served entity matching Unity Catalog registered model
    served_entities = [
        ServedEntityInput(
            entity_name=model_uc_path,
            entity_version=model_version,
            scale_to_zero_enabled=True,
            workload_size="Small",
            environment_vars=env_vars,
        )
    ]

    try:
        # Check if endpoint exists
        existing_endpoint = w.serving_endpoints.get(name=endpoint_name)
        print(f"Endpoint '{endpoint_name}' exists. Updating configuration...")
        w.serving_endpoints.update_config_and_wait(
            name=endpoint_name,
            served_entities=served_entities
        )
    except NotFound:
        print(f"Creating new Model Serving Endpoint '{endpoint_name}'...")
        w.serving_endpoints.create_and_wait(
            name=endpoint_name,
            config=EndpointCoreConfigInput(
                name=endpoint_name,
                served_entities=served_entities
            )
        )

    print("==================================================")
    print("MODEL SERVING ENDPOINT DEPLOYED SUCCESSFULLY")
    print("==================================================")
    print(f"Endpoint Name: {endpoint_name}")
    print(f"URL: {host}/serving-endpoints/{endpoint_name}/invocations")


if __name__ == "__main__":
    deploy_serving_endpoint()
