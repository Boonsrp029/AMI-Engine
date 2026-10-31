# Check an existing index before synchronization — 31 October 2026

The existing-index path previously fetched the named index and immediately called `sync()`, without checking whether its definition matched the configured source. An existing resource name alone did not establish compatibility with the intended ETL output.

`MarketVectorSearchIndexer.sync_index()` now reads `index.describe()` and validates the following fields before calling `sync()`:

- Index name, `DELTA_SYNC` type and primary key.
- Source table and requested pipeline mode.
- Exactly one managed embedding source column, with the configured name and embedding-model endpoint.

Missing, malformed or mismatched metadata raises `ValueError`; the message names field labels without reflecting arbitrary returned values. Metadata access errors propagate without retry. A rejected existing index is neither synchronized nor automatically deleted/recreated. The original endpoint readiness step still runs first; this guard is not a general no-mutation preflight for every branch of the provisioner.

Creation of a new index retains its previous request format and readiness wait. Public constructor and `sync_index()` arguments are unchanged. A matching existing index now incurs one additional metadata read before the original sync/wait sequence. A mismatched existing configuration intentionally changes from an attempted sync to an explicit failure. Resolve that mismatch through a reviewed resource decision; do not automatically repoint a production index or bypass the check.

The installed `databricks-ai-search` SDK source was inspected without importing its clients: `AISearchIndex.describe()` makes a control-plane metadata GET, and the create-index payload defines the checked Delta Sync fields. SDK source hashes and the installed version are retained locally with the audit. No library version changed and no live SDK operation was performed by this pass.

## Validation and limits

Fourteen new offline tests cover matching metadata and call order; wrong names/types/keys/tables/modes/embedding settings; absent or malformed structures; multiple embedding columns; and metadata access failure. Together with the five resource-override tests, **19 focused tests passed**. The full Windows suite passed **1,040 tests with 15 existing warnings**. Clients and metadata are fixed mocks. These prove request gating, not compatibility with an observed workspace resource.

Full-suite results, preservation checks and Docker availability evidence are retained under ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v38/`. Docker Desktop's Linux engine remains unavailable; the actual Linux build/test step is pending, and earlier Linux passes do not validate this revision. The owner has already been asked to start the engine; no repeated request or daemon repair is performed here.

This guard does not verify source schema or data freshness, embedding endpoint readiness or digest, grants, index freshness, pipeline health, separate query-embedding overrides, reranker settings, recovery or rollback. Those remain actual staging qualification requirements. It does not reconcile an existing definition or turn the registered legacy model into the analyst application.

The frozen analyst generator, prompts, dependencies, corpus, evaluation packages and approved exports are preserved. No model, NeMo, Ragas or Databricks requests, commits/pushes, external deployment or reviewer contact are included. No factual human scoring is needed for this engineering check. Resource replacement and the intended staging application/model route remain separate owner decisions.
