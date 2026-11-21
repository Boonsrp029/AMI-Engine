# Table-focus development results

On 15 November 2026, both development cases passed technical, final NeMo and assistant exact-source review on the same frozen table-focus contract. Each ran once, in order. No retries or warmups. The development allowance is exhausted.

| Case | Result | Main calls | NeMo invocations | Wall time | Reported main tokens |
| --- | --- | ---: | ---: | ---: | ---: |
| cq1-a20 | Raw and stored prose reproduced the wording previously accepted by the owner, with no fallback. | 2 | 1 | 77.16 s | 3,379 |
| cq1-a19 | Mapper selected the verified biomass span. Composer selected the bound unit ID. Application rendered the verified row with its citation. | 2 | 1 | 44.30 s | 3,607 |

Total: four local main calls and two NeMo invocations. Captures reported 6,986 main tokens. NeMo internal usage and monetary cost are unavailable. No CQ1 case ran. The earlier biomass failure remains archived.

## Manual review of the biomass draft

Question: What were biomass generation and its share of US utility-scale generation in 2023?

Exact stored claim:

> In 2023, the table gives Biomass (total) generation in Billion kWh as 47 and its share of total utility-scale electricity generation as 1.1%.

The direct EIA table span s_cb9a294a4ff9d4c9 from eia-generation-2023 gives Biomass (total), 47 billion kWh, 1.1% of the total. The question and linked source title provide U.S. scope; the rendered sentence leaves it implicit. The raw composer returned IDs only. The application supplied the text through the verified-row path, with no fallback or editorial correction. Review source support and whether to make “U.S.” explicit in the sentence. Exact-revision approval/export is separate.

- [Biomass draft and provenance](actual-development-v1/cq1-a19.result.json)
- [Biomass source assessment](actual-development-v1/cq1-a19.assessment.json)
- [Automated-meter source assessment](actual-development-v1/cq1-a20.assessment.json)
- [Pinned EIA source URL](https://www.eia.gov/tools/faqs/faq.php?id=427&t=3)
