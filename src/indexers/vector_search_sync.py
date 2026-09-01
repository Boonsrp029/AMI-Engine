"""
Databricks AI Search Delta Sync Indexer
"""

import os
import time
from dotenv import load_dotenv
from databricks.ai_search.client import AISearchClient

# Load credentials from .env
load_dotenv()


class VectorSearchSyncManager:

    def __init__(self):
        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")

        if not host or not token:
            raise ValueError(
                "DATABRICKS_HOST and DATABRICKS_TOKEN must be defined in .env"
            )

        # Pass host and token explicitly to avoid MLflow credential lookup errors
        self.vsc = AISearchClient(
            workspace_url=host, personal_access_token=token, disable_notice=True
        )


class MarketVectorSearchIndexer:

    def __init__(
        self,
        endpoint_name: str = "vs_market_intelligence_endpoint",
        source_table: str = "main.market_intelligence.silver_market_chunks",
        index_name: str = "main.market_intelligence.silver_market_chunks_vector_index",
        primary_key: str = "feed_id",  # Note: feed_id is primary key in your notebook
        embedding_column: str = "clean_content",  # Column from your silver table
        embedding_model: str = "databricks-bge-large-en",
    ):
        self.vsc = VectorSearchSyncManager().vsc
        self.endpoint_name = endpoint_name
        self.source_table = source_table
        self.index_name = index_name
        self.primary_key = primary_key
        self.embedding_column = embedding_column
        self.embedding_model = embedding_model

    def ensure_endpoint_exists(self) -> None:
        """Creates AI Search endpoint if it does not already exist."""
        existing = [ep["name"] for ep in self.vsc.list_endpoints().get("endpoints", [])]
        if self.endpoint_name not in existing:
            print(f"Creating AI Search endpoint '{self.endpoint_name}'...")
            self.vsc.create_endpoint(name=self.endpoint_name, endpoint_type="STANDARD")
            
            while self.vsc.get_endpoint(self.endpoint_name).get("state", {}).get("config_status") != "COMPLETED":
                time.sleep(10)
            print("Endpoint creation complete.")

    def sync_index(self, pipeline_type: str = "TRIGGERED") -> None:
        """Creates or updates the Delta Sync index via AI Search."""
        self.ensure_endpoint_exists()
        
        try:
            index = self.vsc.get_index(endpoint_name=self.endpoint_name, index_name=self.index_name)
            print(f"Triggering sync for existing index '{self.index_name}'...")
            index.sync()
        except Exception:
            print(f"Index '{self.index_name}' not found. Creating new AI Search Delta Sync index...")
            self.vsc.create_delta_sync_index(
                endpoint_name=self.endpoint_name,
                source_table_name=self.source_table,
                index_name=self.index_name,
                pipeline_type=pipeline_type,
                primary_key=self.primary_key,
                embedding_source_column=self.embedding_column,
                embedding_model_endpoint_name=self.embedding_model
            )
            print(f"AI Search Index '{self.index_name}' created successfully.")


if __name__ == "__main__":
    indexer = MarketVectorSearchIndexer()
    indexer.sync_index(pipeline_type="TRIGGERED")