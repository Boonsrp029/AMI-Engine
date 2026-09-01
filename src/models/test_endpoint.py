import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def run_test_suite():
    endpoint_name = "market_agent_serving_endpoint"
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")

    if not host or not token:
        raise ValueError("DATABRICKS_HOST and DATABRICKS_TOKEN must be set in .env")

    url = f"{host.rstrip('/')}/serving-endpoints/{endpoint_name}/invocations"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Load test queries from sample payload file
    with open("data/sample_payloads/market_queries.json", "r") as f:
        test_data = json.load(f)

    for item in test_data:
        payload = {
            "dataframe_records": [
                {"query": item["query"]}
            ]
        }
        print(f"\n[Testing Query ID: {item['query_id']}] Category: {item['category']}")
        print(f"Query: {item['query']}")
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("Response Received Successfully:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Failed with status code {response.status_code}: {response.text}")

if __name__ == "__main__":
    run_test_suite()