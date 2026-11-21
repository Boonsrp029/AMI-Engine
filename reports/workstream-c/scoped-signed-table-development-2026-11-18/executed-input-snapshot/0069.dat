# V10 CQ1 stopped at the second answerable miss

On 15 November 2026 Bangkok time, the authorized CQ1 batch attempted the ten answerable cases in order. Technical execution and NeMo passed for all ten. Assistant source review recorded eight complete supported drafts and two noncritical completeness misses. The second miss at cq1-a10 closed the allowance under the frozen 9/10 gate. Ten cases remain unattempted. No retries or warmups. [Batch summary](qualification-batch-summary.json) · [Final ledger summary](actual-cq1/cq1-a10.summary.json)

| Category | Passed | Attempted | Frozen denominator |
| --- | ---: | ---: | ---: |
| Answerable | 8 | 10 | 10 |
| Partial | 0 | 0 | 2 |
| Missing | 0 | 0 | 4 |
| Conflict | 0 | 0 | 2 |
| Injection | 0 | 0 | 2 |

| Miss | Source evidence and observed omission |
| --- | --- |
| cq1-a26 | EIA span s_44a4448281bbe6a8 contains both capabilities. Raw and final output retain device-level electricity tracking but omit remote control by the utility or customer and leave the qualifier “some” implicit. |
| cq1-a10 | EIA spans s_ec39d28380e76dfd and s_bd057ec120f8b36b support power versus energy over time and the 40-watt, five-hour example. Raw and final output retain 200 Wh but omit both example conditions. A supported statement about utility meters from s_2845cfa10cf8e534 does not answer the bulb question. |

Both omissions occurred despite retrieval that included the required evidence. Existing safety accepted the exact submitted text; this does not resolve completeness. The source assessments recorded no critical unsupported, wrong-scope, wrong-date or wrong-unit assertions on attempted cases.

The run consumed 20 local main-model calls and ten NeMo invocations. Captures reported 34,617 main-model tokens. NeMo internal usage and monetary cost are unmeasured. The sum of per-case wall times was 415.50 seconds, excluding inter-case source review.

## Exact results for owner review

The eight passed drafts can be reviewed for source support, coverage and wording. Do not count the two misses as passes through editorial changes; retain them as development evidence. The prior preference for “U.S.” is particularly relevant to the table-rendered claims. No owner acceptance or stored approval/export is recorded.

| Case | Draft finding |
| --- | --- |
| [cq1-a25](actual-cq1/cq1-a25.result.json) | 2 billion kWh and 0.1% for other biomass waste. |
| [cq1-a16](actual-cq1/cq1-a16.result.json) | 73.62 billion kWh of additional estimated small-scale solar PV generation in 2023. |
| [cq1-a17](actual-cq1/cq1-a17.result.json) | Negative annual pumped storage generation because most facilities use more electricity than they produce. |
| [cq1-a18](actual-cq1/cq1-a18.result.json) | Usual meter location and historical manual reading. |
| [cq1-a06](actual-cq1/cq1-a06.result.json) | 425 billion kWh and 10.2% for wind. |
| [cq1-a07](actual-cq1/cq1-a07.result.json) | 240 billion kWh and 5.7% for hydropower. |
| [cq1-a08](actual-cq1/cq1-a08.result.json) | 165 billion kWh and 3.9% for total solar. |
| [cq1-a09](actual-cq1/cq1-a09.result.json) | Utility-scale capacity threshold and the separate small-scale PV definition. |

For the next offline pass, test a common coverage contract for explicit counts of requested facts and quantities tied to example conditions. Check whether coverage survives composition and reject irrelevant additions. Use different synthetic facts. Preserve all ten unattempted cases and predeclare any replacements for the ten consumed answerable cases before future generation.
