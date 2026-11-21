# Conversion development stopped at first source gate

The 15 November 2026 grant attempted one of two consumed development cases once. cq1-a22 passed the technical and final NeMo checks but failed source completeness. cq1-a21 remains unattempted and the allowance is closed. No CQ1 qualification case started. [Batch summary](batch-summary.json)

The mapper selected the exact span s_d1ad042cf9ed1c0a from the pinned EIA measurement source, with separate context roles and no duplicates. The span states both requested conversions: one MW is 1,000 kW or 1,000,000 watts. The raw composer and stored draft both gave only the kilowatt equivalence. The missing watts value was not disclosed. No fallback or editorial correction occurred. [Exact result](actual-development-v1/cq1-a22.result.json) · [Source gate decision](actual-development-v1/cq1-a22.assessment.json)

The run used two main calls and one NeMo invocation, reporting 3,271 main tokens from captures. Internal NeMo usage and monetary cost are unmeasured. Elapsed wall time was 55.97 seconds. No warmup or retry.

No manual review is required for this incomplete development draft. The remaining fault is composition coverage. The mapper bound the exact source but treated both conversions as one supported fact unit. Next, test explicit source-bound target coverage in offline fixtures: require a correct value and matching unit for each requested target, keep ordinary model-written prose, and reject omissions or swapped units through deterministic validation. Do not reopen the run or count the incomplete draft as a pass.
