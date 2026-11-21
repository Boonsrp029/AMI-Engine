# Membership rendering development results

Both consumed development cases passed technical, final NeMo and assistant exact-source review. Each ran once, on 15 November 2026 Bangkok time, with no retries or warmups. The allowance is exhausted.

| Case | Assessment | Main calls | NeMo invocations | Wall seconds | Captured main tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| cq1-a24 | Both raw phrases match the exact EIA definition. Application rendering kept both groups and the fossil-fuel qualifier, and logged its source and offsets. NeMo accepted the complete sentence. | 2 | 1 | 61.88 | 3,289 |
| cq1-a23 | Bound table selection rendered 8 billion kWh and 0.2% for landfill gas in 2023. U.S. scope is stated in the source and question and implicit in the claim. | 2 | 1 | 37.02 | 3,610 |

Total four main calls, two NeMo invocations, 6,899 captured main-model tokens. NeMo internal usage and monetary cost remain unmeasured. The earlier failures remain archived. No CQ1 case has started.

## Manual review

The new cq1-a24 claim is “The other gases category includes blast furnace gas and other manufactured and waste gases derived from fossil fuels.” Check it against the pinned EIA definition at span s_1c02614a2ce1b7d8 and confirm source support and wording. This is an application-rendered sentence over exact raw source phrases. No fallback or editorial correction was applied. [Exact membership result](actual-development-v1/cq1-a24.result.json)

The cq1-a23 wording matches the earlier draft. The owner's preference for explicit “U.S.” remains recorded and does not require another review of identical text. [Prior wording request](../scoped-conversion-slots-2026-11-15/cq1-a23-owner-adjudication-2026-11-15.md)
