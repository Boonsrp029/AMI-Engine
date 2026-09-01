"""
Databricks Model Serving Endpoint Provisioning for Unity Catalog Registered Agent Model
"""

import os
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedEntityInput

load_dotenv()


def deploy_serving_endpoint():
    endpoint_name = "market_agent_serving_endpoint"
    model_uc_path = "main.market_intelligence.market_agent_model"
    model_version = "2" # Specify the version of the registered model to serve

    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")

    if not host or not token:
        raise ValueError("DATABRICKS_HOST and DATABRICKS_TOKEN must be set in .env")

    w = WorkspaceClient(host=host, token=token, auth_type="pat")

    print(f"Provisioning Model Serving Endpoint '{endpoint_name}' for model '{model_uc_path}' v{model_version}...")

    # Configure served entity matching Unity Catalog registered model
    served_entities = [
        ServedEntityInput(
            entity_name=model_uc_path,
            entity_version=model_version,
            scale_to_zero_enabled=True,
            workload_size="Small",
            environment_vars={
                "DATABRICKS_HOST": host,
                "DATABRICKS_TOKEN": token,
                "DATABRICKS_AUTH_TYPE": "pat"
            }
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
    except Exception:
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