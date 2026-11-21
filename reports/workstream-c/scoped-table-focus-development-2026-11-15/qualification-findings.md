# CQ1 stopped at cq1-a22

The authorized 15 November 2026 CQ1 qualification ran two of twenty cases and closed at the first technical failure. One passed assistant source review, one failed and eighteen remain unattempted. Both attempted cases are now consumed. Keep all eighteen reserved cases and predeclare any replacements before future generation. [Batch summary](qualification-batch-summary.json)

- cq1-a21 passed. The raw composer selected the verified Wood row ID and the application rendered 31 billion kWh and 0.8% of total utility-scale generation in 2023. The question and cited EIA table establish U.S. scope. Final NeMo passed. The original text and source assessment are available for manual review. [Exact draft](actual-cq1/cq1-a21.result.json)
- cq1-a22 produced a schema-valid mapping with duplicate direct spans and a direct span repeated as context. Validation threw “Duplicate fact evidence role” before the composer or NeMo. An exact offline replay with sockets blocked reproduced the rejection. The retrieved span s_d1ad042cf9ed1c0a states both equivalences directly: one megawatt is 1,000 kilowatts or 1,000,000 watts. The selected kilowatt definition and utility-scale threshold missed this direct evidence. [Replay evidence](replay-cq1-a22-failure.json)

The batch used three main calls and one NeMo invocation. Captured responses reported 6,163 main tokens. NeMo internal usage and monetary cost remain unmeasured. There were no warmups or retries. Wall times were 55.70 seconds for a21 and 23.36 for a22.

Next engineering step: preserve duplicate rejection while testing how to prevent duplicate and self-context selections at the schema/decoding boundary and improve selection of a span containing both requested equivalences. These are separate issues. Use different units and values for regression fixtures. No mapper changes, new grants or qualification claims arise from this batch.
