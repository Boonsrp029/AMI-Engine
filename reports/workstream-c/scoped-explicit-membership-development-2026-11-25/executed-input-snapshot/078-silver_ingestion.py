"""Build Silver and Gold Delta tables from an existing Bronze feed table.

The Bronze source is populated by an upstream ingestion process. This job is
idempotent: Silver and Gold are full refreshes derived from that source.
"""

import os

from pyspark.sql import SparkSession, functions as F
from pyspark.sql.window import Window


def run() -> None:
    spark = SparkSession.builder.getOrCreate()
    catalog = os.getenv("DATABRICKS_CATALOG", "main")
    schema = os.getenv("DATABRICKS_SCHEMA", "market_intelligence")
    bronze = os.getenv("DATABRICKS_BRONZE_TABLE", f"{catalog}.{schema}.bronze_market_feeds")
    silver = os.getenv("DATABRICKS_SOURCE_TABLE", f"{catalog}.{schema}.silver_market_chunks")
    gold = os.getenv("DATABRICKS_GOLD_TABLE", f"{catalog}.{schema}.gold_market_summary")

    if not spark.catalog.tableExists(bronze):
        raise RuntimeError(f"Required Bronze table does not exist: {bronze}")

    source = spark.table(bronze)
    required = {"feed_id", "timestamp", "source", "title", "raw_content", "sector"}
    missing = sorted(required.difference(source.columns))
    if missing:
        raise ValueError(f"Bronze table {bronze} is missing columns: {', '.join(missing)}")

    prepared = (
        source
        .where(F.col("feed_id").isNotNull() & F.col("raw_content").isNotNull())
        .withColumn("ingested_at", F.to_timestamp("timestamp"))
        .withColumn("clean_content", F.trim(F.regexp_replace(F.col("raw_content"), r"\s+", " ")))
        .withColumn("_content_hash", F.sha2(F.col("raw_content"), 256))
        .where(F.length("clean_content") > 0)
    )
    latest_per_feed = Window.partitionBy("feed_id").orderBy(
        F.col("ingested_at").desc_nulls_last(),
        F.col("source").asc_nulls_last(),
        F.col("title").asc_nulls_last(),
        F.col("_content_hash").asc(),
    )
    cleaned = (
        prepared.withColumn("_row_number", F.row_number().over(latest_per_feed))
        .where(F.col("_row_number") == 1)
        .drop("_row_number", "_content_hash")
    )
    cleaned.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(silver)
    spark.sql(f"ALTER TABLE {silver} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")

    ordered_records = F.sort_array(
        F.collect_list(F.struct("ingested_at", "feed_id", "title", "clean_content"))
    )
    summary = cleaned.groupBy("sector").agg(
        F.countDistinct("feed_id").alias("total_sources"),
        F.transform(ordered_records, lambda record: record["title"]).alias("source_titles"),
        F.concat_ws(" | ", F.transform(ordered_records, lambda record: record["clean_content"])).alias("aggregated_context"),
        F.max("ingested_at").alias("last_updated"),
    )
    summary.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(gold)
    print(f"Silver refreshed: {silver}")
    print(f"Gold refreshed: {gold}")


if __name__ == "__main__":
    run()
