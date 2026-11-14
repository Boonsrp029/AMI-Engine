import os
import json
from databricks.sdk import WorkspaceClient
from src.utils.env import load_project_environment

load_project_environment()

def run_test_suite():
    endpoint_name = os.getenv("DATABRICKS_SERVING_ENDPOINT", "market_agent_serving_endpoint")
    host = os.getenv("DATABRICKS_HOST")
    if not host:
        raise ValueError("DATABRICKS_HOST must be set")
    workspace = WorkspaceClient(host=host)

    # Load test queries from sample payload file
    with open("data/sample_payloads/market_queries.json", "r") as f:
        test_data = json.load(f)

    for item in test_data:
        print(f"\n[Testing Query ID: {item['query_id']}] Category: {item['category']}")
        print(f"Query: {item['query']}")
        response = workspace.serving_endpoints.query(
            name=endpoint_name,
            dataframe_records=[{"query": item["query"]}],
        )
        print("Response Received Successfully:")
        print(json.dumps(response.as_dict(), indent=2, default=str))

if __name__ == "__main__":
    run_test_suite()
