# Span-hint CQ1 stopped at cq1-a15

The authorized batch closed at its first technical failure. One of twenty cases passed, one failed, and eighteen were unattempted. All 212 frozen inputs still match.

| Case | Outcome |
|---|---|
| cq1-a14 | Passed technical, safety and assistant source review. The verified Petroleum coke row gave 5 billion kWh and 0.1% of total U.S. utility-scale generation in 2023. |
| cq1-a15 | The mapper selected prose about fossil fuels' approximate share and the all-source total. The raw draft omitted the fossil-fuel subtotal of 2,505 billion kWh and repeated the 4,178 billion kWh all-source total. Numeric evidence validation failed before NeMo and no draft was stored. |

The [socket-blocked replay](cq1-a15-offline-replay.json) reproduced the numeric validation error. The table was present in the mapper payload, but the focus matcher recognized the single-word aggregate alias used in development and omitted this multiword aggregate. With the source's exact label, Fossil fuels (total), the same offline matcher returns the row with 2,505 billion kWh and 60.0%. The [batch summary](batch-summary.json) records this comparison and the full unattempted list.

Four local main calls used 6,852 reported tokens and one NeMo invocation ran. Internal NeMo usage and monetary cost are unmeasured. No retries occurred. Owner review of cq1-a14 remains pending. The failed case has no draft for wording review.

For the next offline pass, test exact whole-subject matching for multiword aggregate labels and test aggregate siblings and child rows with synthetic facts. Preserve the strict numeric validator and the frozen batch. Any new qualification should preserve the eighteen unattempted cases and predeclare replacements for both consumed cases.
