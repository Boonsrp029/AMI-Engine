# V8 CQ1 stopped at cq1-a24

On 15 November 2026 Bangkok time, qualification attempted two of twenty ordered cases once. cq1-a23 passed assistant exact-source review. At cq1-a24, the final NeMo fact-check rail blocked the response and the ledger closed the allowance. Eighteen cases remained unattempted. Both attempted cases are consumed evidence. [Batch summary](qualification-batch-summary.json)

| Case | Result | Main calls | NeMo wrapper | Wall seconds | Captured main tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| cq1-a23 | The composer selected the verified Landfill gas table unit. Application rendering retained 8 billion kWh and 0.2% of total utility-scale generation for 2023. U.S. scope follows from the question and pinned EIA table. | 2 | 1 | 75.47 | 3,610 |
| cq1-a24 | Mapper selected s_1c02614a2ce1b7d8. Its source states that the category includes blast furnace gas and other manufactured and waste gases derived from fossil fuels. Raw composer included only blast furnace gas. NeMo blocked the response at self check facts; no draft was published. | 2 | 1 | 34.56 | 3,139 |

Four main calls and two NeMo invocations used. Captures report 6,749 main tokens. NeMo internal usage and monetary cost are unmeasured. No retries or warmups.

The cited passage supports blast furnace gas as a member. The raw answer is incomplete independently of the recorded safety rejection. The safety artifact names the blocking rail but gives no reason for its decision, so the omission cannot be assigned as the cause of the block. Preserve the fail-closed gate. Next, use offline evidence to test source-bound coverage of explicit multipart category definitions and verify the exact evidence envelope delivered to the rail. Any actual follow-up requires a new grant and predeclared replacements. Preserve all 18 remaining held-out cases.

Manual review is available for the exact cq1-a23 claim and its source. Check the quantities and whether to state U.S. explicitly. cq1-a24 has no stored draft. The consumed development conversion wording has its own pending owner review. No owner judgment or export was recorded for qualification.

- [Exact a23 draft](actual-cq1/cq1-a23.result.json)
- [a23 source assessment](actual-cq1/cq1-a23.assessment.json)
- [a24 raw composer](actual-cq1/cq1-a24.composition.raw.json)
- [a24 safety artifact](actual-cq1/cq1-a24.safety.json)
