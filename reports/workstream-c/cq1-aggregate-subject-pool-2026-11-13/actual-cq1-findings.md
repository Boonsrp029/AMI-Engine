# Aggregate-subject CQ1 stopped at cq1-a20

The authorized batch closed at its first critical source error. One of twenty cases passed, one failed source review, and eighteen were unattempted. All 156 frozen input copies match.

| Case | Outcome |
|---|---|
| cq1-a19 | Passed technical, safety and assistant source review. The verified Biomass (total) row gave 47 billion kWh and 1.1% of total U.S. utility-scale generation in 2023. |
| cq1-a20 | Passed technical and safety checks. The first claim correctly gave both the information historically reported and its recipient. The final claim used a dangling “These meters” and attached real-time wireless reporting to the wrong meter scope in this brief. Source review recorded one critical error and closed the batch. |

In the pinned eia-measurement source, span s_6af27ac482a98ade at offsets 1417–1503 supports periodic reporting of electricity use to the utility. For the recipient component, the mapper instead selected span s_792c4494ed697e52 at offsets 1556–1615. That sentence depends on the preceding electronic-smart-meter antecedent at offsets 1504–1555. The raw composer repeated the dependent sentence as a standalone claim and the application retained it. Both drafts persisted at revision 1. No fallback or editorial change was applied.

The [batch summary](batch-summary.json) records the exact denominator, unattempted IDs and source offsets. [Passing case assessment](actual-cq1/cq1-a19.assessment.json) · [Critical case assessment](actual-cq1/cq1-a20.assessment.json)

Four local model calls reported 6,973 tokens, and two NeMo invocations ran. Internal NeMo usage and monetary cost are unmeasured. Zero retries occurred. Owner adjudication is pending and cannot change the recorded batch result.

The next offline investigation should test inherited subject context in evidence spans and answer relevance for short follow-up components. Preserve these exact outputs and test with different facts before preparing a new development gate. Preserve the eighteen unattempted cases and predeclare replacements for the two consumed cases.
