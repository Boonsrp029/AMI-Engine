# U.S. table development results and owner review

Both consumed cases passed exact-source, completeness, safety and persistence checks on their single attempts. Both exact drafts are stored at revision 1 awaiting review. No fallback or editorial correction occurred.

| Case | Exact claim | Elapsed |
|---|---|---:|
| cq1-a41 | In 2023, the table gives U.S. Pumped storage hydropower generation in Billion kWh as -6 and its share of total U.S. utility-scale electricity generation as -0.1%. | 68.25 s |
| cq1-a42 | In 2023, the table gives U.S. Photovoltaic generation in Billion kWh as 162 and its share of total U.S. utility-scale electricity generation as 3.9%. | 37.69 s |

The same cited EIA record supplies the relevant row and the explicit U.S. table heading. Both drafts retained the period and denominator. The first preserved the negative signs and the second retained the photovoltaic row rather than the aggregate solar row. [cq1-a41 source assessment](actual-development-v1/cq1-a41.assessment.json) · [cq1-a42 source assessment](actual-development-v1/cq1-a42.assessment.json)

Total four local main calls and two NeMo invocations, 7,195 recorded input and 384 output tokens, zero retries. Internal NeMo usage and cost are unavailable. The previous CQ1 failures remain on record. Owner source and wording acceptance of these exact drafts remains pending.
