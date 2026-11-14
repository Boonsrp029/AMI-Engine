# Revised CQ1 stopped at cq1-a02

The authorized 12 November 2026 qualification attempted two of twenty cases and closed at the first technical failure. Eighteen cases remain unattempted. One case received exact-source review. The planned category denominators remain 10 answerable, 2 partial, 4 missing, 2 conflict and 2 injection. No case passed its category gate.

| Case | Outcome | Wall time |
|---|---|---:|
| cq1-a11 | The raw and stored drafts gave 2,400 MWh for 24 hours at 100 MW. The second claim accurately stated the capacity-factor numerator and omitted the requested denominator. The exact-source review recorded the one permitted noncritical answerable miss. | 60.484 s |
| cq1-a02 | The raw mapper skipped the table span containing the requested natural gas amount and share. The raw composer gave unrelated totals and shares. The numeric evidence validator rejected the draft before safety, leaving revision 0 and no published draft. | 34.969 s |

The socket-blocked cq1-a02 replay reproduced `Draft introduces a numeric value absent from its selected evidence`. The requested 2023 row was in the retrieved catalog. Its amount and share were adjacent to the natural gas row label and the table headers, but none of that span was selected. This is an evidence selection failure followed by a composition binding failure. Retrieval had already returned the required facts.

The batch used four main-model calls, one NeMo wrapper invocation and 6,345 known main-model tokens (5,576 input and 769 output). NeMo internal usage and monetary cost remain unknown. All 180 input hashes matched and were preserved. No owner adjudication or stored approval/export was recorded.

The next offline pass should test request-level evidence coverage on a new table fixture with an adjacent row distractor, while retaining the numeric guard. It should also test that a requested ratio role binds to the relevant numerator or denominator statement. Both attempted cases are now consumed. Keep all eighteen unattempted rows and their original artifacts. Predeclare any replacement rows and revised thresholds before a future qualification grant.
