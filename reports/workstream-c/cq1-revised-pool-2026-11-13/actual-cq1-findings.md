# 13 November revised CQ1 stopped at cq1-a05

The frozen batch attempted five of twenty cases and closed at the first technical failure. Fifteen remain unattempted. Four attempts reached exact-source review. Three passed the answerable gate, one used the permitted noncritical answerable miss, and the fifth produced no draft.

| Case | Finding |
|---|---|
| cq1-a12 | Passed. Composer selected the petroleum-liquids row. The application rendered 12 billion kWh and 0.3%, distinct from total petroleum. |
| cq1-a13 | Noncritical miss. The mapper selected general meter-use and data-transmission spans, skipping the available sentence about device-level tracking and remote control. Raw and final drafts repeated general meter facts. |
| cq1-a03 | Passed. Composer selected the coal row. The application rendered 675 billion kWh and 16.2%. |
| cq1-a04 | Passed. Composer selected the nuclear row. The application rendered 775 billion kWh and 18.6%. |
| cq1-a05 | Technical stop. The mapper skipped the table span with the requested renewable-generation total. The composer returned unrelated figures and the numeric validator rejected a claim before safety. |

The table focus requires a literal row label. The question says “renewable generation” and the source labels its row “Renewables (total).” The offline check found no focus with the original question and resolved the 894 billion kWh and 21.4% row with the exact label substituted. The saved execution used the original question. The [socket-blocked replay](cq1-a05-offline-replay.json) reproduced “Draft introduces a numeric value absent from its selected evidence.” The selected table fragment included adjacent percentages. Their proximity did not establish their attribution.

The batch used ten main-model calls, four NeMo wrapper invocations and 17,307 known main-model tokens. Internal NeMo usage and monetary cost remain unavailable. All 205 pinned inputs matched and were saved. Owner adjudication and revision approval remain pending. The [batch summary](batch-summary.json) retains the full category denominators and unattempted IDs.

The next offline pass should test a conservative row-label match for qualified totals without collapsing parent and child categories. It should also test evidence relevance within a retrieved document when generic background and the exact requested capabilities coexist. Preserve the numeric and unit guards. The five attempted cases are consumed for future qualification. Keep the fifteen unattempted cases frozen and predeclare replacements before any further qualification run.
