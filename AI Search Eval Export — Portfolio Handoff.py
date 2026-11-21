# Databricks notebook source
# DBTITLE 1,Title & purpose
# MAGIC %md
# MAGIC # AI Search Quality Evaluation — Portfolio Handoff
# MAGIC
# MAGIC This notebook is an **export artifact**: it packages a Databricks Vector Search retrieval-quality project for local development (VS Code + ChatGPT Codex). It is authored for reading and export — the cells are not meant to be executed here.
# MAGIC
# MAGIC **What the project does**
# MAGIC
# MAGIC * A medallion ETL pipeline (bronze → silver → gold Delta tables) ingests market-intelligence feeds and feeds a **Vector Search Delta Sync index** for semantic retrieval.
# MAGIC * Two evaluation layers measure retrieval quality on top of that index:
# MAGIC   1. **Databricks AI Search built-in autoeval (Beta)** — auto-generated query sets, LLM-judged 4-point relevance, per-strategy IR metrics.
# MAGIC   2. **A custom multi-label IR eval harness** — golden queries with multiple relevant docs per query, gold precision/recall@k, portable pure-Python metrics.
# MAGIC
# MAGIC The rest of the notebook documents the cloud assets, the investigation timeline, the results, and the code to take into a local repo: a dependency-free metrics module, the golden dataset, cloud and local eval runners, and an MLflow artifact export.

# COMMAND ----------

# DBTITLE 1,Architecture & cloud assets
# MAGIC %md
# MAGIC # Architecture & cloud assets
# MAGIC
# MAGIC | Layer / Asset | Identifier |
# MAGIC | --- | --- |
# MAGIC | Bronze table | `main.market_intelligence.bronze_market_feeds` |
# MAGIC | Silver table | `main.market_intelligence.silver_market_chunks` (PRIMARY KEY `feed_id`, Change Data Feed enabled) |
# MAGIC | Gold table | `main.market_intelligence.gold_market_summary` |
# MAGIC | Vector Search endpoint | `aisearchendpoint1` |
# MAGIC | Vector Search index | `main.market_intelligence.silver_market_chunks_vector_index_v2` (Delta Sync, embedding model `databricks-gte-large-en`) |
# MAGIC | MLflow experiment | `1384967347443709` (autoeval experiment for this index) |
# MAGIC | Eval dataset (UC table) | `main.market_intelligence.market_intel_multilabel_retrieval` — records: `inputs={"query": str}`, `expectations={"relevant_docs": [feed_id]}`, stored as JSON strings |
# MAGIC | Eval runs | autoeval parent runs (root-run Beta bug: parents FAIL while children succeed — ignore parent status) and `multilabel_eval_{ANN,FULL_TEXT,HYBRID}` runs with per-query JSON artifacts |

# COMMAND ----------

# DBTITLE 1,Investigation timeline
# MAGIC %md
# MAGIC # Investigation timeline
# MAGIC
# MAGIC 1. **Autoeval root runs FAIL while child runs succeed.** Confirmed as a Databricks Beta aggregation bug — the root run fails during aggregation while the three child runs (one per strategy: ANN, FULL_TEXT, HYBRID) finish with complete IR metrics (precision, recall, nDCG, MAP, MRR). 8 occurrences across 3 experiments. Judge the child runs, not the parents.
# MAGIC 2. **Retrieval was catastrophically bad** (Hit@1 = 10%, LLM relevance ≈ 0.0): root cause was a **TRIGGERED-sync index that never re-synced** after the corpus expanded from 2 to 20 documents — the index only had 2 rows. Fixed by recreating the index as `silver_market_chunks_vector_index_v2` and triggering sync.
# MAGIC 3. **After the fix**: precision@1 = recall@1 = MRR = 1.0 across all strategies — retrieval of the single gold doc became perfect.
# MAGIC 4. **Precision@k structural cap discovered**: every autoeval-generated query had exactly 1 gold doc, so gold precision@k was frozen at 1/k (P@10 = 0.100 for all strategies) — the metric carried no signal below rank 1. Run-level `precision_at_10` values above 0.10 revealed those were LLM-judged, not gold-based.
# MAGIC 5. **Built a custom multi-label dataset**: 14 queries — 7 sector-level, 2 cross-sector themes, 5 hard single-label unique-fact; avg 2.07 gold docs/query. Raises the gold P@10 ceiling to 0.207 and the P@3 ceiling to 0.643.
# MAGIC 6. **Ran the multi-label eval** — results in the next cell.

# COMMAND ----------

# DBTITLE 1,Multi-label eval results
# MAGIC %md
# MAGIC # Multi-label eval results (v2 index, num_results=10, no reranker)
# MAGIC
# MAGIC | Metric | ANN | FULL_TEXT | HYBRID |
# MAGIC | --- | --- | --- | --- |
# MAGIC | precision@1 | 1.000 | 1.000 | 1.000 |
# MAGIC | precision@3 | **0.571** | 0.524 | 0.524 |
# MAGIC | precision@5 | 0.357 | 0.329 | **0.371** |
# MAGIC | precision@10 | 0.193 | **0.207** | 0.200 |
# MAGIC | recall@5 | 0.905 | 0.851 | **0.940** |
# MAGIC | recall@10 | 0.958 | **1.000** | 0.982 |
# MAGIC | MRR | 1.000 | 1.000 | 1.000 |
# MAGIC
# MAGIC **Key findings**
# MAGIC
# MAGIC * **ANN is best at the top** (precision@3 0.571), **FULL_TEXT is best at depth** (perfect recall@10 = 1.000, hits its 0.207 precision@10 ceiling), **HYBRID is best mid-list** (recall@5 0.940).
# MAGIC * **ANN and HYBRID miss `feed_102`** (the LangGraph / self-hosted GenAI orchestration doc) on AI-themed queries — a `databricks-gte-large-en` embedding weakness: semantic matching fails where keyword matching succeeds.
# MAGIC * **Top-1 is saturated** (P@1 = MRR = 1.0 for every strategy) — the singleton corpus (20 docs / 11 sectors) is too easy; same-topic distractor docs are needed to make top-1 precision measurable.

# COMMAND ----------

# DBTITLE 1,ir_metrics.py — dependency-free IR metrics
# ir_metrics.py — copy this file directly into a local project; zero dependencies
# Pure-Python information-retrieval metrics for multi-label gold ground truth.
# Works on plain doc-id strings/sets/lists (e.g. "feed_104") — no pandas, no Spark, no Databricks.

KS = (1, 3, 5, 10)


def precision_at_k(gold, retrieved, k):
    """Fraction of the top-k retrieved docs that are in gold.

    >>> precision_at_k({"feed_112", "feed_118"}, ["feed_112", "feed_103", "feed_118"], 3)
    0.6666666666666666
    """
    return len(set(list(retrieved)[:k]) & set(gold)) / k


def recall_at_k(gold, retrieved, k):
    """Fraction of gold docs present in the top-k retrieved.

    >>> recall_at_k({"feed_112", "feed_118"}, ["feed_118", "feed_103", "feed_110"], 3)
    0.5
    """
    return len(set(list(retrieved)[:k]) & set(gold)) / len(set(gold))


def first_hit_rank(gold, retrieved):
    """1-based rank of the first gold doc in the ranked list, or None if none retrieved."""
    gold = set(gold)
    for i, doc in enumerate(retrieved):
        if doc in gold:
            return i + 1
    return None


def mrr(gold, retrieved):
    """Reciprocal rank of the first gold hit for one query (0.0 if no gold doc retrieved).

    >>> mrr({"feed_107"}, ["feed_114", "feed_107"])
    0.5
    """
    rank = first_hit_rank(gold, retrieved)
    return 1.0 / rank if rank is not None else 0.0


def evaluate_all(queries):
    """Aggregate IR metrics per retrieval strategy (unweighted mean over queries).

    queries: [{"query": str,
               "gold": {"feed_112", ...},
               "retrieved_by_strategy": {"ANN": [...], "FULL_TEXT": [...], "HYBRID": [...]}}, ...]
    Returns: {"ANN": {"precision_at_1": ..., "recall_at_3": ..., "mrr": ...}, ...}

    The harness is retrieval-provider-agnostic: anything that fills the
    retrieved_by_strategy dict (Databricks Vector Search, FAISS, brute-force cosine)
    can be scored with this function unchanged.
    """
    strategies = sorted({s for q in queries for s in q["retrieved_by_strategy"]})
    out = {}
    for s in strategies:
        n = len(queries)
        out[s] = {
            **{f"precision_at_{k}":
               sum(precision_at_k(q["gold"], q["retrieved_by_strategy"][s], k) for q in queries) / n
               for k in KS},
            **{f"recall_at_{k}":
               sum(recall_at_k(q["gold"], q["retrieved_by_strategy"][s], k) for q in queries) / n
               for k in KS},
            "mrr": sum(mrr(q["gold"], q["retrieved_by_strategy"][s]) for q in queries) / n,
        }
    return out


# --- doctest-style example with feed ids from the golden dataset ---
_EXAMPLE_QUERIES = [
    {
        "query": "battery supply chain investments from minerals to vehicles",
        "gold": {"feed_112", "feed_118", "feed_105", "feed_113"},
        "retrieved_by_strategy": {
            "ANN": ["feed_105", "feed_113", "feed_112", "feed_101", "feed_109"],
            "FULL_TEXT": ["feed_118", "feed_112", "feed_110", "feed_113", "feed_105"],
            "HYBRID": ["feed_112", "feed_113", "feed_118", "feed_105", "feed_101"],
        },
    },
    {
        "query": "Japan doubles quantum computing research budget to $4 billion",
        "gold": {"feed_107"},
        "retrieved_by_strategy": {
            "ANN": ["feed_107", "feed_114", "feed_102"],
            "FULL_TEXT": ["feed_107", "feed_115", "feed_103"],
            "HYBRID": ["feed_107", "feed_114", "feed_115"],
        },
    },
]
# e.g. evaluate_all(_EXAMPLE_QUERIES)["ANN"]["recall_at_3"] -> 0.875
#      evaluate_all(_EXAMPLE_QUERIES)["FULL_TEXT"]["precision_at_1"] -> 1.0

# COMMAND ----------

# DBTITLE 1,Golden multi-label dataset
# Golden multi-label dataset — the 14-query evaluation set with multi-label gold.
# Exported from UC table main.market_intelligence.market_intel_multilabel_retrieval
# (records: inputs={"query": str}, expectations={"relevant_docs": [feed_id]}).
# These are the exact gold labels behind the multilabel_eval_{ANN,FULL_TEXT,HYBRID} runs
# in MLflow experiment 1384967347443709.

GOLDEN_RECORDS = [
    {"query": "AI infrastructure and data center investments across Asia-Pacific",
     "relevant_docs": ["feed_102", "feed_114", "feed_111"]},
    {"query": "critical minerals and mining projects in the Asia-Pacific region",
     "relevant_docs": ["feed_120", "feed_105", "feed_113"]},
    {"query": "fintech growth and digital financial services across Asia",
     "relevant_docs": ["feed_104", "feed_116"]},
    {"query": "software and SaaS industry expansion in Southeast Asia and India",
     "relevant_docs": ["feed_119", "feed_106"]},
    {"query": "electric vehicle industry growth and exports in Asia",
     "relevant_docs": ["feed_112", "feed_118"]},
    {"query": "renewable energy and clean tech investment in Asia",
     "relevant_docs": ["feed_109", "feed_101"]},
    {"query": "semiconductor manufacturing and supply chain developments in Asia",
     "relevant_docs": ["feed_115", "feed_103"]},
    {"query": "battery supply chain investments from minerals to vehicles",
     "relevant_docs": ["feed_112", "feed_118", "feed_105", "feed_113"]},
    {"query": "how is AI adoption transforming industries across Asia",
     "relevant_docs": ["feed_119", "feed_102", "feed_114", "feed_111"]},
    {"query": "Mongolia Oyu Tolgoi copper mine powered by solar and wind",
     "relevant_docs": ["feed_120"]},
    {"query": "Hong Kong Web3 and blockchain startups raise $3.5 billion",
     "relevant_docs": ["feed_108"]},
    {"query": "Japan doubles quantum computing research budget to $4 billion",
     "relevant_docs": ["feed_107"]},
    {"query": "Thailand smart city 5G IoT deployment across 30 provinces",
     "relevant_docs": ["feed_117"]},
    {"query": "Vietnam manufacturing FDI from Samsung and Intel",
     "relevant_docs": ["feed_110"]},
]

# --- JSON export to the workspace export folder (plain os + json on the /Workspace path — no dbutils) ---
import json
import os

EXPORT_DIR = "/Workspace/Users/s_sirapop@hotmail.com/ai_search_eval_export"
os.makedirs(EXPORT_DIR, exist_ok=True)
export_path = os.path.join(EXPORT_DIR, "golden_dataset.json")
with open(export_path, "w") as f:
    json.dump(GOLDEN_RECORDS, f, indent=2)
print(f"wrote {len(GOLDEN_RECORDS)} records to {export_path}")

# COMMAND ----------

# DBTITLE 1,Cloud eval harness (Databricks)
# Cloud eval harness — runs ON Databricks.
# Loads the golden dataset from the UC table, queries the Vector Search index for each
# strategy, computes multi-label metrics with the ir_metrics functions (cell above), and
# logs one MLflow run per strategy (params + metrics + per-query JSON artifact).
#
# Client notes (current as of 2026-10):
#   * `databricks-vectorsearch` is deprecated in favor of `databricks-ai-search`:
#       pip install databricks-ai-search   ;   from databricks.ai_search import ...
#     The `databricks.vector_search.client.VectorSearchClient` import below still works
#     as a thin re-export.
#   * Gotcha: after pip-installing in a RUNNING kernel you must clear sys.modules entries
#     starting with "databricks" before importing, or the stale preinstalled package wins.
#   * VectorSearchClient() takes no `disable_proxy` argument in the new version.

import json
import sys

import mlflow

try:
    from databricks.vector_search.client import VectorSearchClient
except (ImportError, ModuleNotFoundError):
    # package freshly pip-installed in this kernel: clear stale module cache and retry
    for _mod in [k for k in list(sys.modules) if k == "databricks" or k.startswith("databricks.")]:
        del sys.modules[_mod]
    from databricks.vector_search.client import VectorSearchClient

# --- config ---
ENDPOINT_NAME = "aisearchendpoint1"
INDEX_NAME = "main.market_intelligence.silver_market_chunks_vector_index_v2"
EXPERIMENT_ID = "1384967347443709"
DATASET_TABLE = "main.market_intelligence.market_intel_multilabel_retrieval"
NUM_RESULTS = 10
STRATEGIES = ["ANN", "FULL_TEXT", "HYBRID"]
USE_RERANKER = False  # optional reranker arm: reranker={"model": "databricks_reranker"}

vsc = VectorSearchClient(disable_notice=True)
idx = vsc.get_index(endpoint_name=ENDPOINT_NAME, index_name=INDEX_NAME)


def retrieve(query_text, strategy):
    kwargs = dict(query_text=query_text, query_type=strategy,
                 num_results=NUM_RESULTS, columns=["feed_id"])
    if USE_RERANKER:
        kwargs["reranker"] = {"model": "databricks_reranker"}
    resp = idx.similarity_search(**kwargs)
    # resp["result"]["data_array"] is a list of [doc_id, score] pairs in rank order
    return [row[0] for row in resp["result"]["data_array"]]


def _parse(v):
    return json.loads(v) if isinstance(v, str) else v  # UC table stores JSON strings


# --- load golden dataset from UC table ---
rows = spark.sql(f"SELECT inputs, expectations FROM {DATASET_TABLE}").collect()
queries = [
    {
        "query": _parse(r["inputs"])["query"],
        "gold": set(_parse(r["expectations"])["relevant_docs"]),
        "retrieved_by_strategy": {s: retrieve(_parse(r["inputs"])["query"], s) for s in STRATEGIES},
    }
    for r in rows
]

# --- score with the dependency-free metrics module (ir_metrics cell) ---
metrics_by_strategy = evaluate_all(queries)

# --- log one MLflow run per strategy ---
for strat in STRATEGIES:
    per_query = [
        {"query": q["query"], "gold": sorted(q["gold"]),
         "retrieved": q["retrieved_by_strategy"][strat]}
        for q in queries
    ]
    with mlflow.start_run(experiment_id=EXPERIMENT_ID, run_name=f"multilabel_eval_{strat}"):
        mlflow.log_params({
            "index_name": INDEX_NAME,
            "endpoint_name": ENDPOINT_NAME,
            "dataset": DATASET_TABLE,
            "num_results": NUM_RESULTS,
            "reranker": "databricks_reranker" if USE_RERANKER else "none",
        })
        mlflow.log_metrics(metrics_by_strategy[strat])
        mlflow.log_dict(per_query, f"per_query_results_{strat}.json")

for strat in STRATEGIES:
    print(strat, json.dumps(metrics_by_strategy[strat], indent=2))

# COMMAND ----------

# DBTITLE 1,Local eval runner (VS Code)
# Local eval runner (VS Code) — the same evaluation, driven from a laptop.
# Requires: pip install databricks-sdk
# Auth: DATABRICKS_HOST + DATABRICKS_TOKEN environment variables, or a databricks CLI profile.
#
# If the portfolio must run fully OFFLINE: only the ir_metrics module and the golden dataset
# are needed. The harness is retrieval-provider-agnostic via the retrieved_by_strategy dict —
# swap `retrieve_local()` for any local ANN (FAISS, sklearn NearestNeighbors, or a brute-force
# cosine over the corpus) and evaluate_all() scores it unchanged.

import os

from databricks.sdk import WorkspaceClient

w = WorkspaceClient(
    host=os.environ.get("DATABRICKS_HOST"),
    token=os.environ.get("DATABRICKS_TOKEN"),  # omit both to use databricks CLI profile auth
)
idx = w.vector_search.get_index(
    endpoint_name="aisearchendpoint1",
    index_name="main.market_intelligence.silver_market_chunks_vector_index_v2",
)


def retrieve_local(query_text, strategy, num_results=10):
    resp = idx.similarity_search(
        query_text=query_text,
        query_type=strategy,
        num_results=num_results,
        columns=["feed_id"],
    )
    # resp["result"]["data_array"] is a list of [doc_id, score] pairs in rank order
    return [row[0] for row in resp["result"]["data_array"]]


# Example sweep using GOLDEN_RECORDS (golden-dataset cell) + evaluate_all (ir_metrics cell):
#
# queries = [
#     {
#         "query": rec["query"],
#         "gold": set(rec["relevant_docs"]),
#         "retrieved_by_strategy": {
#             s: retrieve_local(rec["query"], s) for s in ("ANN", "FULL_TEXT", "HYBRID")
#         },
#     }
#     for rec in GOLDEN_RECORDS
# ]
# from pprint import pprint
# pprint(evaluate_all(queries))

# COMMAND ----------

# DBTITLE 1,MLflow artifact export
# MLflow artifact export — fetch the per-query results artifacts from the logged runs so the
# local project keeps the exact retrieval lists behind every metric in the results table.
# Runs ON Databricks (workspace-attached compute); writes next to golden_dataset.json in
# /Workspace/Users/s_sirapop@hotmail.com/ai_search_eval_export/.

import os

import mlflow
from mlflow import MlflowClient

EXPERIMENT_ID = "1384967347443709"
EXPORT_DIR = "/Workspace/Users/s_sirapop@hotmail.com/ai_search_eval_export"
RUNS = {
    "multilabel_eval_ANN": "765a26cb22b54ccdb9cc96417ce10d84",
    "multilabel_eval_FULL_TEXT": "5ea563c61a524cb2b35f82c132f95f63",
    "multilabel_eval_HYBRID": "b0d90b4395534427aefcdeffc73620d2",
}

client = MlflowClient()
os.makedirs(EXPORT_DIR, exist_ok=True)

for run_name, run_id in RUNS.items():
    run = client.get_run(run_id)  # asserts the run exists in EXPERIMENT_ID
    for art in client.list_artifacts(run_id, ""):
        if art.path.endswith(".json"):
            local_path = mlflow.artifacts.download_artifacts(
                run_id=run_id, artifact_path=art.path, dst_path=EXPORT_DIR
            )
            print(f"{run_name}: exported {art.path} -> {local_path}")

# COMMAND ----------

# DBTITLE 1,How to get this into VS Code / Codex
# MAGIC %md
# MAGIC # How to get this into VS Code / Codex
# MAGIC
# MAGIC 1. **Sync the export folder**: install the Databricks extension for VS Code and sync the workspace folder `ai_search_eval_export`, or download the files from the workspace UI.
# MAGIC 2. **Export this notebook**: File > Export > Source (.py) or IPython Notebook (.ipynb).
# MAGIC 3. **Suggested local project layout for Codex**:
# MAGIC    * `ir_metrics.py` — the dependency-free metrics module (from the ir_metrics cell)
# MAGIC    * `golden_dataset.json` — written by the golden-dataset cell
# MAGIC    * retrieval client adapter — the `WorkspaceClient` pattern (from the local-runner cell)
# MAGIC    * `eval_runner.py` — orchestrates strategy sweeps
# MAGIC    Make the retrieval provider pluggable so the portfolio demo can run offline with a local vector index.
# MAGIC 4. **Transcript**: the full chat thread behind this notebook can be shared read-only via the thread's **Share** button.

# COMMAND ----------

# DBTITLE 1,Open problems / next steps
# MAGIC %md
# MAGIC # Open problems / next steps
# MAGIC
# MAGIC * **Top-1 saturation** — P@1 = MRR = 1.0 for every strategy; the singleton corpus needs same-topic distractor docs before top-1 precision is measurable.
# MAGIC * **Embedding weakness** — `databricks-gte-large-en` misses `feed_102` (LangGraph / self-hosted GenAI orchestration) on AI-themed queries; try a stronger embedding model or embed `title` + sector context alongside the body text.
# MAGIC * **Reranker arm** — reranking (`databricks_reranker`) is expected to fix deep-rank precision; the cloud harness already supports it via `USE_RERANKER`.
# MAGIC * **Autoeval root-run Beta bug** — parents FAIL while children succeed; report to Databricks support and ignore parent status until fixed.
# MAGIC * **Singleton gold labels** — with one gold doc per autoeval query, LLM-judged `avg_relevance` is the only differentiating metric in the built-in autoeval; the multi-label dataset and harness in this notebook are the workaround.