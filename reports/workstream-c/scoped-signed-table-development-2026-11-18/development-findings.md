# Actual signed-table development results

Both authorized consumed cases passed once-only technical, assistant source, completeness, safety and storage checks. The allowance is exhausted. The actual model selected complete direct evidence and the raw composer selected each verified table unit. Application rendering retained the requested row, year, amount, unit, share and denominator. No fallback or editorial correction occurred during generation. [Exact results and usage](batch-summary.json)

| Case | Verified source facts | Main calls | NeMo | Owned wall time |
|---|---|---|---|---|
| cq1-a38 | Other sources, 10 billion kWh, 0.2% of total U.S. utility-scale generation in 2023 | 2 | 1 | 63.19 seconds |
| cq1-a37 | Other gases, 11 billion kWh, 0.3% of the same total and period | 2 | 1 | 39.08 seconds |

The first case used the new complete 591-character source window after the negative pumped-storage row. The marker 5 was correctly distinguished from the amount 10. The second case retained its earlier positive-row interpretation, with marker 3 distinct from amount 11.

Both mapper responses select additional same-record context. The first includes a neighboring fragment and preliminary-data/utility-scale definition text. The second includes a U.S. fragment and small-scale solar text. Those additions supply no final claim. Retain the extra context as a relevance/efficiency observation.

Both final drafts leave U.S. implicit, consistent with the frozen assistant source gate's use of question and table scope. Proposed explicit-U.S. copies follow the owner's wording preference and remain separate. Owner source/wording acceptance of these new copies is pending. Earlier owner acceptance applies to the prior development copies. [New review packet](review-packet.md)

Stored revision 1 for each case remains needs_review, with no approval or export. Human review is needed before calling these new copies owner-accepted. The failed qualification remains one pass, one technical failure and eighteen unattempted cases. A later qualification must freeze two fresh replacements and obtain its own applicable grant.
