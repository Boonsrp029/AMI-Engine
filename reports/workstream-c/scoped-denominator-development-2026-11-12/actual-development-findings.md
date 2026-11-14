# Scoped percentage-denominator development results

Both actual development cases passed technical, source-support, completeness, title, safety and persistence checks on 12 November 2026. Each case reached revision 1 awaiting review. The stored drafts have zero reviews and exports.

| Case | Source findings | Main calls | NeMo checks | Wall time |
|---|---|---:|---:|---:|
| cq-p01 | Raw and final claims keep Canada's observed 5.7% demand growth in 2016 and Japan's projected 2.6% annual growth through 2036 with their separate citations. The application suppressed a Canada-only title suffix. | 2 | 1 passed | 73.625 s |
| cq-p02 | The raw and final claim retain Denmark wind's 29% share of total electricity generation in 2015. The application explicitly discloses the missing dated retail price evidence. | 2 | 1 passed | 47.203 s |

The new cq-p02 composer independently returned the wording that the preceding validator rejected. The revised check accepted the relocated country and year. Both drafts retained their raw claims without source fallback or editorial correction. The earlier cq-p02 failure remains in its original batch.

The batch used 2,304 input and 486 output tokens across four main calls, totaling 2,790 known main-model tokens. NeMo internal usage, monetary cost and earlier interrupted backend usage remain unmeasured. With the prior tracked batches, the cumulative counts are 20 observed main starts, five NeMo wrapper invocations, and 14,054 known main-model tokens.

Assistant assessments bind the exact new results. Owner source/wording acceptance remains pending. The questions and sources are consumed synthetic development fixtures. CQ1 is a separate frozen 20-case run.
