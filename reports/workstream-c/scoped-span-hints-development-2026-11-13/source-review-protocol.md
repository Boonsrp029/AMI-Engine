# Aggregate row and passage relevance diagnostic

Run cq-hint01 once. Advance to cq-hint02 once only after execution, safety and exact-source review pass. Each case has a 180-second wall deadline including preparation, four local main calls at most and one NeMo wrapper invocation at most. The batch ceiling is eight main calls and two NeMo wrappers, with zero retries or warmups. Stop on the first failure or the standing usage threshold.

| Case | Required evidence and output |
|---|---|
| cq-hint01 | The mapper selects the exact table span and the composer returns the verified row ID. The application renders the 2023 US utility-scale renewables total of 894 billion kWh and 21.4% of total utility-scale generation. A child category or an approximate prose share cannot substitute for the row. |
| cq-hint02 | The mapper selects the sentence establishing both requested advanced smart-meter capabilities. Raw and final prose must retain device-level electricity use tracking and the ability of the utility or customer to control electricity use remotely, with the source’s qualification that some advanced meters offer these capabilities. General meter use or data transmission is insufficient. |

Compare raw selections, exact source spans and lineage, raw composition, rendered text, final safety and the stored revision. Treat relevance hints as ranking aids. Record table rendering, fallback and editorial correction separately. Bind each assistant assessment to the exact result and keep owner acceptance pending.

Both questions are consumed development evidence. Preserve the earlier outcomes and the fifteen unattempted cases. Any later CQ1 run requires a newly frozen roster and a separate grant.
