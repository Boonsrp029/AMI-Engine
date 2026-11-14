# Aggregate-subject CQ1 qualification authorization

Contract SHA-256 `f66f056bb1d7e82421d526c3773935d799ec008e2dd173099dc62fe55f29124a`. Frozen for 13 November 2026 in Bangkok. The runner and CLI verified 156 pinned inputs. Zero of twenty qualification cases have started.

Both [current development cases](../scoped-aggregate-subject-development-2026-11-13/actual-development-findings.md) passed. The [frozen roster](README.md) carries forward eighteen unattempted cases and adds two predeclared replacements. The earlier CQ1 batch remains closed.

Run each case once in the frozen order and inspect exact-source support before advancing. The limits are 180 seconds per case including preparation, at most four local main-model calls and one NeMo invocation per case, and at most 80 main calls and 20 NeMo invocations overall. Zero retries or warmups. Stop on a technical or critical error, a failed full-pass category, a second noncritical answerable miss, or the standing usage threshold.

The gates remain 9/10 answerable, 2/2 partial, 4/4 missing, 2/2 conflict, 2/2 injection, and zero critical errors. Follow the [source-review protocol](source-review-protocol.md). Owner adjudication of the exact results follows the quality gates. This grant excludes Ragas, hosted inference, Databricks, approval/export, publication and deployment.

Reply **Authorize CQ1 scoped twenty-case qualification** to grant this exact batch.
