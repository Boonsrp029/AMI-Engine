# V11 CQ1 stopped at the geothermal mapping

On 17 November 2026 Bangkok time, two of twenty ordered cases ran once. cq1-a27 passed assistant source review and cq1-a28 failed the technical gate. The allowance closed. Eighteen cases in this roster remained unattempted. Both attempted cases are consumed. [Batch summary](qualification-batch-summary.json)

- cq1-a27: verified source row and application rendering gave 6 billion kWh and 0.1% of total U.S. utility-scale generation for biogenic municipal solid waste in 2023. NeMo passed. U.S. scope is implicit in the sentence, established by the question and pinned EIA table. [Exact draft](actual-cq1/cq1-a27.result.json)
- cq1-a28: the mapper returned the same direct span five times. Offline replay of the exact schema-valid response reproduced the “Duplicate fact evidence role” rejection. The source row crosses adjacent spans: s_cb9a294a4ff9d4c9 ends at “Geothermal” and s_53a9904131330b03 starts with 16 and 0.4%. No table focus was recognized. The composer and NeMo did not run. [Replay evidence](cq1-a28-offline-replay.json)

The batch used three model calls and one NeMo invocation. Captures report 6,196 main-model tokens. NeMo internal usage and monetary cost are unmeasured. Per-case wall times were 64.41 and 21.63 seconds, with no retries or warmups.

Next offline engineering: verify whether one exact, adjacent source window can preserve the header, label and both cells before applying table-row constraints. Handle split boundaries without joining distinct source records, treating neighboring values as the requested row, or weakening duplicate validation. Use unrelated table fixtures and preserve the archived failures and reserved roster. Repeat generation requires a new grant.

Manual review is available for cq1-a27. Check the category label and figures, and apply the existing “U.S.” wording preference if you request an editorial revision. cq1-a28 produced no draft.
