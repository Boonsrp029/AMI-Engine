# COMMAND ----------
# MAGIC %md
# MAGIC # Autonomous Market Intelligence ETL & Evaluation Pipeline
# MAGIC **Architecture:** Medallion Delta Lake (Bronze -> Silver -> Gold)
# MAGIC **Evaluation:** Native `mlflow.evaluate()` with MLflow Tracking

# COMMAND ----------
import os
import json
from datetime import datetime
import pandas as pd

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType, FloatType, ArrayType
)

import mlflow
import mlflow.data
from mlflow.data.spark_dataset import SparkDataset
from mlflow.metrics import genai

# Enable Delta Lake ACID transaction features
spark.conf.set("spark.sql.parquet.compression.codec", "snappy")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled", "true")
spark.conf.set("spark.databricks.delta.autoCompact.enabled", "true")

# Setup Catalog and Database Schema
CATALOG = "main"
SCHEMA = "market_intelligence"

spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Bronze Layer: Raw Ingestion to Delta Lake
# MAGIC * Ingest raw JSON payload feeds into a append-only streaming/batch Delta table.

# COMMAND ----------
# Define schema for incoming raw JSON feed
raw_schema = StructType([
    StructField("feed_id", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("source", StringType(), True),
    StructField("title", StringType(), True),
    StructField("raw_content", StringType(), True),
    StructField("sector", StringType(), True)
])

# Mock raw market feed payloads
mock_raw_data = [
    {
        "feed_id": "feed_101",
        "timestamp": "2026-08-10T08:30:00Z",
        "source": "Bloomberg Green",
        "title": "APAC Clean Energy Investment Reaches Record $45B in H1 2026",
        "raw_content": "Clean energy infrastructure spending across Southeast Asia spiked due to new grid modernization subsidies...",
        "sector": "Green Tech"
    },
    {
        "feed_id": "feed_102",
        "timestamp": "2026-08-10T09:15:00Z",
        "source": "TechCrunch AI",
        "title": "Enterprise GenAI Infrastructure Deployments Surge Across APAC",
        "raw_content": "Companies are migrating from external API wrappers to self-hosted orchestration platforms like LangGraph on Databricks...",
        "sector": "AI Infrastructure"
    }
]

# Write to Bronze Delta Table
raw_df = spark.createDataFrame(mock_raw_data, schema=raw_schema)

bronze_table_path = f"{CATALOG}.{SCHEMA}.bronze_market_feeds"
raw_df.write \
    .format("delta") \
    .mode("append") \
    .option("mergeSchema", "true") \
    .saveAsTable(bronze_table_path)

print(f"Bronze table updated: {bronze_table_path}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Silver Layer: Cleaning, Deduplication & Structural Transformation
# MAGIC * Parse timestamps, sanitize text content, remove duplicates, and index for retrieval.

# COMMAND ----------
bronze_df = spark.table(bronze_table_path)

silver_df = (
    bronze_df
    .filter(F.col("raw_content").isNotNull())
    .withColumn("ingested_at", F.to_timestamp(F.col("timestamp")))
    .withColumn("clean_content", F.regexp_replace(F.col("raw_content"), r"\s+", " "))
    .dropDuplicates(["feed_id"])
)

silver_table_path = f"{CATALOG}.{SCHEMA}.silver_market_chunks"
silver_df.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(silver_table_path)

print(f"Silver table optimized: {silver_table_path}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. Gold Layer: Aggregated Market Insights Synthesis
# MAGIC * Structure processed insights for downstream query & multi-agent execution.

# COMMAND ----------
silver_data = spark.table(silver_table_path)

gold_df = (
    silver_data
    .groupBy("sector")
    .agg(
        F.count("feed_id").alias("total_sources"),
        F.collect_list("title").alias("source_titles"),
        F.concat_ws(" | ", F.collect_list("clean_content")).alias("aggregated_context"),
        F.max("ingested_at").alias("last_updated")
    )
)

gold_table_path = f"{CATALOG}.{SCHEMA}.gold_market_summary"
gold_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(gold_table_path)

print(f"Gold table written: {gold_table_path}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 4. MLflow Automated Evaluation Pipeline
# MAGIC * Log Delta Lake dataset lineage and evaluate generated responses using `mlflow.evaluate()`.

# COMMAND ----------
# Set MLflow Experiment
mlflow.set_experiment("/Shared/Market_Intelligence_Evaluation")

# Prepare test benchmark evaluation dataset from Gold Delta Table
eval_pyspark_df = spark.table(gold_table_path).select(
    F.col("sector").alias("inputs"),
    F.col("aggregated_context").alias("context")
)

# Convert evaluation dataset into SparkDataset object for tracking lineage
eval_dataset: SparkDataset = mlflow.data.from_spark(
    eval_pyspark_df,
    table_name=gold_table_path,
    version="1"
)

# Simulated Agent Prediction Logic (Replace with actual LangGraph runner)
def mock_agent_pipeline(inputs: pd.DataFrame) -> pd.Series:
    """Mock agent inference callable for MLflow evaluate harness."""
    results = []
    for _, row in inputs.iterrows():
        sector = row["inputs"]
        results.append(f"Synthetic summary for {sector}: Investment and infrastructure growth trends show strong 5-10 year momentum.")
    return pd.Series(results)

# COMMAND ----------
# MAGIC %md
# MAGIC ### Execute MLflow Evaluation Run

# COMMAND ----------
with mlflow.start_run(run_name="MLflow_Delta_ETL_Eval") as run:
    # Log MLflow Dataset Lineage
    mlflow.log_input(eval_dataset, context="eval")
    
    # Convert Spark DataFrame to Pandas for local evaluation evaluation execution
    eval_data_pd = eval_pyspark_df.toPandas()
    eval_data_pd["targets"] = eval_data_pd["inputs"].apply(
        lambda x: f"Accurate APAC market analysis for {x}"
    )

    # Evaluate Model Output using MLflow builtin text metrics & custom judges
    eval_results = mlflow.evaluate(
        model=mock_agent_pipeline,
        data=eval_data_pd,
        targets="targets",
        model_type="question-answering",
        extra_metrics=[
            mlflow.metrics.toxicity(),
            mlflow.metrics.flesch_kincaid_grade_level()
        ]
    )

    # Log Custom Evaluation Summary Metrics to Run
    metrics = eval_results.metrics
    print("\n==================================================")
    print("MLFLOW EVALUATION RESULTS")
    print("==================================================")
    for metric_name, score in metrics.items():
        print(f"{metric_name:<30}: {score}")
    print("==================================================")

    # Save artifact paths
    mlflow.log_params({
        "catalog": CATALOG,
        "schema": SCHEMA,
        "bronze_table": bronze_table_path,
        "silver_table": silver_table_path,
        "gold_table": gold_table_path
    })