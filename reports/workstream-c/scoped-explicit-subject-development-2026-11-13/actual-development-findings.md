# Explicit-subject development stopped at cq1-a20

One of two cases ran. Technical and safety checks passed, but the exact-source relevance gate failed. The allowance is closed. The biomass case cq1-a19 remains unattempted, and the replacement CQ1 qualification did not start. All 102 pinned inputs were verified and copied to the executed-input snapshot.

## Exact stored draft, revision 1

**Question** — What did automated electricity meters report periodically, and who received those reports?

> Automated electricity meters report electricity use periodically to the utility.
>
> Utility companies measure and monitor electricity use with meters.

The EIA source says earlier automated meters could periodically report electricity use to the utility. That span, s_6af27ac482a98ade at offsets 1417–1503, was selected for both request components. The first claim preserves the data, cadence and recipient. It uses present tense where the source describes historical capability. The generic utility-monitoring statement comes from s_2845cfa10cf8e534 at offsets 1055–1211 and does not answer either component. The mapper selected both spans for both components. The composer repeated both claims in the stored draft. The earlier wrong-scope wireless-reporting claim is absent. There was no fallback or editorial correction.

## Manual source review

Confirm whether claim 1 should preserve the source's historical capability wording and whether claim 2 should be omitted. This records an owner judgment on revision 1. The frozen source-gate result remains failed. [Exact result](actual-development-v1/cq1-a20.result.json) · [Assistant assessment](actual-development-v1/cq1-a20.assessment.json)

The attempt took 55.14 seconds including preparation. Two main calls reported 3,444 tokens and one NeMo invocation ran. Internal NeMo usage and monetary cost are unmeasured. Zero retries or warmups. [Batch summary](batch-summary.json)

The next offline step should test how the composer handles an evidence unit that is supported but adds nothing to a requested component, including whether the contract's one-claim-per-unit instruction is encouraging that output. Preserve modality and time scope in the synthetic tests. Any contract change should be explicit. A fresh run requires a separate applicable grant.
