# Scoped modal diagnostic findings

Contract 55b16188320ceb7ffeb36c53749d2b224da29598ee2eb029c959bfef93ac3a89. Two of two development cases attempted once. One passed (cq1-a20), one failed (cq1-a19), zero unattempted, zero retries and warmups. No CQ1 qualification case was attempted under this grant. The allowance closed at cq1-a19.

| Case | Technical and source result | Main calls | NeMo wrapper | Wall seconds | Main tokens reported by captures |
| --- | --- | ---: | ---: | ---: | ---: |
| cq1-a20 | Technical, final NeMo, and assistant exact-source checks passed. Owner review pending. | 2 | 1 | 68.05 | 3,379 |
| cq1-a19 | Mapping returned a schema-valid unrelated table fragment. Exact-focus validation rejected it before the composer or NeMo. No draft to review. | 1 | 0 | 18.42 | 2,381 |

Across the captures, 5,760 main-model tokens were reported. NeMo internal usage and monetary cost are unmeasured. The failed worker's stored counters could not account for token usage; the retained mapping capture supplies its reported total.

The biomass case's selected span s_53a9904131330b03 contains the end of the table with pumped-storage and other-source rows. The verified span s_cb9a294a4ff9d4c9 contains the Biomass (total) row with 47 billion kWh and 1.1% of total U.S. utility-scale generation in 2023. The socket-blocked exact replay reproduced “Fact selection does not retain its verified focus.” The table data was available and the response parsed. The error is evidence selection before composition. A follow-up should qualify whether the mapper can be constrained to an already verified row when one uniquely matches the requested label, measures and scope. Preserve composer row selection and the unresolved path for ambiguous rows. No runtime change was made in this diagnostic.

## Manual review of cq1-a20

Question: What did automated electricity meters report periodically, and who received those reports?

Raw composer and stored claim: “Automated electricity meters could periodically report electricity use to the utility.”

Pinned EIA direct span s_6af27ac482a98ade (eia-measurement): “Eventually, automated meters could periodically report electricity use to the utility.”

Assistant exact-source review passed because the claim retains the capability, cadence, measured quantity and recipient. Same-record mechanical-meter context introduced no claim; no fallback or editorial correction was used. Check whether “could” and the wording adequately preserve the source's framing. This is semantic wording review of a development result. Approval and export are separate actions.

- [Exact result](actual-development-v1/cq1-a20.result.json)
- [Assistant assessment](actual-development-v1/cq1-a20.assessment.json)
- [Biomass failure replay](replay-biomass-failure.json)
