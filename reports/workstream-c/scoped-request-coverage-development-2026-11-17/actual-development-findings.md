# V11 request-coverage development results

On 17 November 2026 Bangkok time, both consumed development cases passed technical, final NeMo and assistant exact-source review. Each ran once. The development allowance is exhausted.

| Case | Outcome | Main calls | NeMo invocations | Wall seconds | Captured main tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| cq1-a26 | Both raw actions match the EIA source. The application-rendered claim retained “some,” tracking individual devices and remote control by the utility or customer. No fallback. | 2 | 1 | 58.59 | 3,267 |
| cq1-a10 | Both raw example fields match the source. Rendering kept 40 W and five hours with 200 Wh or 0.2 kWh. Raw composition omitted the watt/watthour distinction. Disclosed verbatim fallbacks u1 and u2 supplied it, making the final answer supported and complete. | 2 | 1 | 39.72 | 3,762 |

Across the two cases: 4 local calls, 2 NeMo invocations and 7,029 captured main tokens. NeMo internal usage and monetary cost are unmeasured. No retries or warmups. The previous CQ1 failure and both old omissions remain on record. No new CQ1 case ran.

## Manual review

- cq1-a26: confirm source support and wording of the complete rendered capability sentence, including the qualified subject. [Exact draft](actual-development-v1/cq1-a26.result.json)
- cq1-a10: confirm the source support and readability of the two fallback excerpts alongside the complete example. The header embedded in the first excerpt and the repetitive definition may warrant editorial revision. No editorial adjustment or exact-revision approval was applied. [Exact draft](actual-development-v1/cq1-a10.result.json)
