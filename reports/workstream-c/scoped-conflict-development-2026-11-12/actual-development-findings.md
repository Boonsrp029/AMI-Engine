# Scoped conflict development results

The 12 November 2026 batch attempted two cases and closed at cq-status02's source failure. Both executions completed within the deadline and passed NeMo. The stored revisions have zero reviews and exports. Revised CQ1 remains at zero of twenty attempts.

| Case | Exact-source result | Wall time |
|---|---|---:|
| cq-status01 | Pass. The raw composer and stored draft cite the Peru journey count and provisional status separately. The earlier false conflict did not recur. | 50.625 s |
| cq-status02 | Fail. The raw mapper selected only the provisional notice. Both the provisional and final notices were retrieved for the same Cambodia ferry counts. The raw composer and stored draft report only provisional status and omit the disagreement. | 44.985 s |

The new status validator checks a mapper selection labeled conflicting. cq-status02 was labeled supported, so that check had no opportunity to compare the two statements. NeMo passed the one-sided draft. The failed assistant assessment binds the exact stored result and did not alter its content.

The batch used four local main-model calls and two NeMo wrapper invocations. The main model returned 2,585 input and 523 output tokens, totaling 3,108. Internal NeMo usage and cost remain unknown. All 125 execution inputs matched their contract hashes and were preserved.

The next offline repair should check whether a supported status selection omits an explicit opposing statement among the bound, retrieved sources. The comparison must remain scoped to the same literal subject, measure, period and geography. Keep the mapper output, application-detected disagreement and exact source statements separately inspectable. Test supported, genuine conflict, ambiguous language and out-of-scope cases before freezing another development grant.
