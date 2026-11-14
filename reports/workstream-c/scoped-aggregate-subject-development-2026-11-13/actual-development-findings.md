# Aggregate-subject development results

Both cases passed technical, NeMo and assistant exact-source review on 13 November 2026. Each ran once and produced a stored revision 1 awaiting review.

| Case | Finding | Wall time |
|---|---|---:|
| cq1-a15 | The mapper selected the exact EIA table span and the composer selected the verified row unit. The application rendered the 2023 U.S. fossil-fuel subtotal of 2,505 billion kWh and 60.0% of total utility-scale generation. | 46.80 s |
| cq-hint02 | The raw and stored claim kept both requested capabilities and the qualifier that some advanced smart meters offer them. The second sentence was supported general context and unnecessary. | 53.09 s |

No fallback or editorial correction was used. Four local main-model calls reported 6,942 tokens. Two NeMo wrapper invocations ran. Internal NeMo usage and monetary cost remain unmeasured. There were zero retries or warmups. Owner adjudication remains pending. Both cases are consumed development evidence. The earlier CQ1 failure remains preserved.

[Exact fossil-fuel assessment](actual-development-v1/cq1-a15.assessment.json) · [Exact smart-meter assessment](actual-development-v1/cq-hint02.assessment.json)
