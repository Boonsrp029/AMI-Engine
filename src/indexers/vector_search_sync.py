"""
Databricks AI Search Delta Sync Indexer
"""

import os
from datetime import timedelta
from databricks.ai_search.client import AISearchClient
from src.utils.env import load_project_environment

# Load credentials from .env
load_project_environment()


class VectorSearchSyncManager:

    def __init__(self):
        host = os.getenv("DATABRICKS_HOST")
        token = os.getenv("DATABRICKS_TOKEN")
        # Local development may provide explicit credentials; Databricks jobs
        # should use the SDK's workload identity / configured auth provider.
        self.vsc = AISearchClient(
            workspace_url=host or None,
            personal_access_token=token or None,
            disable_notice=True,
        )


class MarketVectorSearchIndexer:

    def __init__(
        self,
        endpoint_name: str = "market_intelligence_vs_endpoint",
        source_table: str = "main.market_intelligence.silver_market_chunks",
        index_name: str = "main.market_intelligence.silver_market_chunks_vector_index",
        primary_key: str = "feed_id",  # Note: feed_id is primary key in your notebook
        embedding_column: str = "clean_content",  # Column from your silver table
        embedding_model: str = "databricks-bge-large-en",
    ):
        self.vsc = VectorSearchSyncManager().vsc
        self.endpoint_name = os.getenv("DATABRICKS_VECTOR_SEARCH_ENDPOINT", endpoint_name)
        self.source_table = os.getenv("DATABRICKS_SOURCE_TABLE", source_table)
        self.index_name = os.getenv("DATABRICKS_VECTOR_SEARCH_INDEX", index_name)
        self.primary_key = primary_key
        self.embedding_column = os.getenv("DATABRICKS_EMBEDDING_SOURCE_COLUMN", embedding_column)
        self.embedding_model = os.getenv("DATABRICKS_EMBEDDING_MODEL_ENDPOINT", embedding_model)

    def ensure_endpoint_exists(self) -> None:
        """Creates AI Search endpoint if it does not already exist."""
        timeout = timedelta(seconds=int(os.getenv("VECTOR_ENDPOINT_TIMEOUT_SECONDS", "1200")))
        if not self.vsc.endpoint_exists(self.endpoint_name):
            print(f"Creating AI Search endpoint '{self.endpoint_name}'...")
            self.vsc.create_endpoint_and_wait(
                name=self.endpoint_name,
                endpoint_type="STANDARD",
                timeout=timeout,
            )
        else:
            self.vsc.wait_for_endpoint(name=self.endpoint_name, timeout=timeout)

    def sync_index(self, pipeline_type: str = "TRIGGERED") -> None:
        """Creates or updates the Delta Sync index via AI Search."""
        self.ensure_endpoint_exists()
        
        if self.vsc.index_exists(endpoint_name=self.endpoint_name, index_name=self.index_name):
            index = self.vsc.get_index(endpoint_name=self.endpoint_name, index_name=self.index_name)
            print(f"Triggering sync for existing index '{self.index_name}'...")
            index.sync()
            index.wait_until_ready(timeout=timedelta(seconds=int(os.getenv("VECTOR_INDEX_TIMEOUT_SECONDS", "3600"))))
        else:
            print(f"Index '{self.index_name}' not found. Creating new AI Search Delta Sync index...")
            index = self.vsc.create_delta_sync_index(
                endpoint_name=self.endpoint_name,
                source_table_name=self.source_table,
                index_name=self.index_name,
                pipeline_type=pipeline_type,
                primary_key=self.primary_key,
                embedding_source_column=self.embedding_column,
                embedding_model_endpoint_name=self.embedding_model
            )
            index.wait_until_ready(timeout=timedelta(seconds=int(os.getenv("VECTOR_INDEX_TIMEOUT_SECONDS", "3600"))))
            print(f"AI Search Index '{self.index_name}' created successfully.")


if __name__ == "__main__":
    indexer = MarketVectorSearchIndexer()
    indexer.sync_index(pipeline_type="TRIGGERED")
