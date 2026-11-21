# Publication development diagnostic, 20 November 2026

Contract SHA-256 `caa4ac9a435bc5efd3f0d83b0f73ccb61484446ff35acbfb0bd3d39899f808b0` pins 244 inputs. [Frozen contract](development-contract.json) · [Source review](source-review-protocol.md)

Run cq1-a43 once and then cq1-a42 once only if all first-case checks pass. Eight local main calls and two NeMo invocations maximum combined, 180 seconds per case, zero retries or warmups. Stop at the first failure or the standing usage threshold. Development only. The closed CQ1 result and its 19 unattempted cases are retained.

The 142 focused offline tests passed. A network-blocked replay rejected the old mapper and composer independently and accepted a fixed complete attribution. [Offline replay](../cq1-us-table-qualification-2026-11-20/offline-attribution-repair.json)

Reply **Authorize scoped publication development diagnostics** to run this frozen diagnostic.
