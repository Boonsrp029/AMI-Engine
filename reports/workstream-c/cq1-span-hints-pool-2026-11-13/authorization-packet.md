# Span-hint CQ1 qualification authorization packet

Contract SHA-256: `1b93bcf4e523e04d31d696478453dd850254a939a0c68d5aec54ea696988c59c`. Frozen for 13 November 2026, Bangkok time. The runner and CLI both verified the contract and its 212 pinned inputs offline. No qualification attempts have started.

The [two current development attempts](../scoped-span-hints-development-2026-11-13/actual-development-findings.md) passed technical, safety, and assistant exact-source review. The [replacement roster](README.md) carries forward the fifteen unattempted cases and includes five predeclared replacements. The earlier failed qualification remains closed.

Run the twenty frozen cases in order, once each, with exact-source review before advancing. Each case allows 180 seconds including preparation, at most four local main-model calls and one NeMo invocation. Batch ceilings are 80 main calls and 20 NeMo invocations. Zero retries or warmups. Stop at the first technical or critical failure, any failed full-pass category, a second noncritical answerable miss, or the standing usage threshold.

Pass thresholds: 9/10 answerable, 2/2 partial, 4/4 missing, 2/2 conflict, 2/2 injection, and zero critical errors. Follow the [source-review protocol](source-review-protocol.md). Owner adjudication of exact results follows the quality gates. This scope excludes Ragas, hosted inference, Databricks, approval/export, publication and deployment.

A new direct grant is required for this exact contract. Reply **Authorize CQ1 scoped twenty-case qualification**.
