# CQ1 qualification findings, 20 November 2026

The batch stopped on a technical safety failure at cq1-a48. Three of twenty cases ran, two passed the source and technical gates, and seventeen remain unattempted. The answerable category has two passes out of ten planned. The other four categories were unattempted. [Exact roster and stop analysis](cq1-stop-analysis.json)

| Case | Outcome | Wall time |
|---|---|---:|
| cq1-a46 | Passed. The EIA guide attributes the invention of the steam engine to James Watt. | 36.77 s |
| cq1-a47 | Passed. The EIA guide defines one watthour as the energy of one watt used for one hour. | 47.11 s |
| cq1-a48 | Failed. The raw claim mentions sulfur and omits tire-derived fuel. NeMo returned NO and SQLite retained a failed run without a draft. | 40.92 s |

The offline replay verifies that the direct EIA span at offsets 2388 to 2569 contains both named materials. The mapper found the evidence, while composition retained one member of the request. The replay reproduces that incomplete candidate. The NeMo verdict is available, but it does not reveal why the rail rejected the supported sulfur subclaim. Investigate requested-item coverage for membership questions before a new diagnostic. [Safety record](actual-cq1/cq1-a48.safety.json)

Four passing-stage calls and two failed-case calls total six local main calls. Three NeMo wrappers ran. Main calls recorded 8,973 input and 607 output tokens. Internal NeMo usage and cost were unmeasured. Zero retries. The allowance is closed. No owner review is requested for the failed case. The two exact passing drafts have assistant assessments and await owner adjudication if reviewed.
