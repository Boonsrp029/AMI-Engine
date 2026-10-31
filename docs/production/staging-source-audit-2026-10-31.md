# Staging source wiring audit — 31 October 2026

**Offline source evidence only.** No Databricks authentication, resource discovery, model calls or deployment occurred. Configured names below are code defaults, not observed workspace resources. This audit does not authorize a migration or reactivate a closed diagnostic allowance.

| Finding | Source evidence | Qualification consequence |
|---|---|---|
| Workspace-host override is ineffective | `databricks.yml` declares `variables.workspace_host`, but the dev target uses a literal host and never references `${var.workspace_host}`. | Changing that declared variable alone does not change the target host. This is not a diagnosis of invalid credentials. Validate the final target host before authorized workspace operations. |
| Index primary-key environment setting is ignored | The job supplies `DATABRICKS_VECTOR_SEARCH_PRIMARY_KEY`; `MarketVectorSearchIndexer` assigns its constructor argument to `self.primary_key` and never reads that environment key. | Default `feed_id` agrees with the current ETL. A non-default environment override is ineffective; do not claim configurable creation until this is repaired and tested. The retriever separately reads actual index metadata, which does not repair index creation. |
| Registration is the legacy inference graph | `LangGraphAgentPyFunc.load_context()` imports `src.agents.graph.app`. | Registering/deploying this model does not deploy the reviewed analyst application's SQLite revision/review/export lifecycle. Keep durable analyst storage outside ephemeral serving replicas. |
| ETL and registration namespace overrides differ | Bundle catalog/schema variables configure ETL tables. Registration hardcodes `main.market_intelligence.market_agent_model`; the deployer uses the same hardcoded model path. | An alternative ETL catalog/schema does not automatically relocate the registered model. Verify both resource sets explicitly; no cross-catalog deployment is demonstrated. |

The current ETL expects Bronze columns `feed_id`, `timestamp`, `source`, `title`, `raw_content` and `sector`; it full-refreshes Silver and Gold, then enables Silver change data feed. There is no upstream ingestion service in this job. The indexer creates or synchronizes a Delta Sync index; its existing-index branch does not reconcile source/key/embedding configuration before syncing. None of this proves actual grants, freshness, schema compatibility, repeat-run recovery or rollback.

The [architecture boundary](architecture.md) already requires the analyst application to remain the user-facing system of record. Its local-only model route and local corpus are not automatically replaced by these Databricks adapters. A staging design must specify where the application and durable storage run, how its model is reachable, and how retrieval preserves its source identity/citation contracts. A remote `localhost` address does not identify the owner's desktop model service.

## Next action and evidence required

Prepare resource-override repairs as a separate focused change with mocked constructor/job tests and unchanged library versions. Before activation, the owner must accept the staging application/model/retrieval route and authorize external deployment or provider migration. That decision must cover identity, secrets custody, durable review storage and costs. Do not silently substitute the legacy endpoint for the reviewed workflow.

During an authorized qualification, record actual table/index names, primary key, embedding source column/endpoint, serving model/version/signature, build identity, grants and freshness. Exercise repeat runs, failure recovery and rollback before claiming the path works. Current local tests and configured defaults cannot establish those facts.

The retained local audit is `reports/workflow_pilot/production-readiness-2026-10-27/resume-v36/staging-source-audit.json`: hashes of seven inspected sources, syntax-tree extraction of indexer environment reads, and assertions for the four findings. Runtime files, dependencies, frozen cases, judgments and approved exports remain unchanged. No factual human scoring is needed for this source inspection; staging design and activation remain owner decision points.
