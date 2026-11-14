# Request-bound geography development gate

Run cq-geo01 once. Run cq-geo02 once only after the first case passes technical and exact-source review. Each case has a 180-second wall deadline including preparation, four local main calls at most and one NeMo wrapper invocation at most. The total ceiling is eight main calls and two NeMo invocations. The batch has zero retries and warmups. Stop on the first technical, source or completeness failure.

| Case | Required output |
|---|---|
| cq-geo01 | The raw and final answer cover 18 million Peru passenger rail journeys in 2019 and the provisional status. The amount and status trace to their respective supplied records. The Bolivia figure and distance measurement unit do not support either answer. Geography may resolve only to a source-bound literal Peru occurrence. Any unresolved geography warning must be accurate. |
| cq-geo02 | The raw and final answer preserve Canada's observed 5.7% electricity demand growth in 2016 and Japan's projected annual 2.6% growth through 2036. If the mapper picks one country, the final title must still apply to the full draft. |

Check the actual mapper response, raw composer claims, final output, exact citations and branch lineage, safety verdict, timings and stored review-pending revision. Compare each claim against the pinned synthetic source. Report any fallback or editorial correction separately. Neither can make an incomplete raw composer response pass this development gate. Bind every assistant finding to the retained result hash. Keep owner acceptance pending until explicitly provided.

The preceding CQ1 failure stays closed. cq1-a01 and the new development cases are consumed evidence. The 19 unattempted CQ1 cases stay frozen. Any later roster must explicitly declare a replacement answerable case, preserve the agreed category counts and thresholds, and receive a separate grant. Keep the earlier r07 failure and its original reserved cases intact.
