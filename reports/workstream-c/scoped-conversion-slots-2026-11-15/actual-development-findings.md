# Conversion slot development results

Both consumed development cases passed technical, final NeMo and assistant exact-source checks on 15 November 2026 Bangkok time. Each ran once, in order. No retries or warmups. The development allowance is exhausted.

| Case | Finding | Main calls | NeMo wrapper | Wall seconds | Captured main tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| cq1-a22 | The mapper selected the pinned EIA equivalence. Raw fields both matched their cited value and unit. The application joined the two submitted sentences. | 2 | 1 | 69.25 | 3,304 |
| cq1-a21 | The mapper and composer selected the verified Wood row, rendering 31 billion kWh and 0.8% for 2023. U.S. scope is implicit in the sentence and established by the question and source table. | 2 | 1 | 37.98 | 3,604 |

Total: 4 main calls, 2 NeMo invocations, 6,908 captured main tokens. NeMo internal usage and monetary cost are unmeasured. Prior failures remain in their original directories. No CQ1 case has started.

## Manual review

For cq1-a22, the exact public claim reads “One megawatt equals one thousand kilowatts. One megawatt equals one million watts.” Compare with EIA span s_d1ad042cf9ed1c0a in eia-measurement. The source gives both equivalents and the output uses no fallback or editorial correction. Confirm source support and whether the two-sentence wording is acceptable. [Exact conversion result](actual-development-v1/cq1-a22.result.json)

For cq1-a21, the verified row renderer reproduced the same wording the owner requested to revise. The saved request for explicit “U.S.” still applies. No repeat review of that same wording is needed. This run did not edit or approve a stored revision. [Prior wording request](../scoped-table-focus-development-2026-11-15/cq1-a21-owner-adjudication-2026-11-15.md)
