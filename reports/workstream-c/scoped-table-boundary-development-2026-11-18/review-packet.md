# Actual table-boundary development review — 18 November 2026

Assistant source checks passed both consumed development cases. Owner acceptance is pending. The original generated drafts remain stored at revision 1 with needs_review status. This packet does not approve or export those revisions.

## cq1-a28

What were geothermal generation and its share of US utility-scale generation in 2023?

Exact generated claim

> In 2023, the table gives Geothermal generation in Billion kWh as 16 and its share of total utility-scale electricity generation as 0.4%.

Proposed editorial copy following the owner's U.S. preference

> In 2023, the table gives Geothermal generation in Billion kWh as 16 and its share of total U.S. utility-scale electricity generation as 0.4%.

Source identifier eia-generation-2023. Pinned table heading states U.S. utility-scale electricity generation by source, amount, and share of total in 2023. Selected span s_917774a0cd14288c, source character offsets 635–1165. The column headings are Energy source, Billion kWh and Share of total. These are preliminary 2023 net-generation data published in February 2024. PDF page is unavailable for this HTML source.

No extra context selected.

Raw composer selected the verified unit. Application rendering produced the final prose. No fallback or editorial correction occurred in generation. NeMo passed.

[Exact result](actual-development-v1/cq1-a28.result.json) · [Source assessment](actual-development-v1/cq1-a28.assessment.json)

## cq1-a27

What were municipal solid waste (biogenic) generation and its share of US utility-scale generation in 2023?

Exact generated claim

> In 2023, the table gives Municipal solid waste (biogenic) generation in Billion kWh as 6 and its share of total utility-scale electricity generation as 0.1%.

Proposed editorial copy following the owner's U.S. preference

> In 2023, the table gives Municipal solid waste (biogenic) generation in Billion kWh as 6 and its share of total U.S. utility-scale electricity generation as 0.1%.

Source identifier eia-generation-2023. Pinned table heading states U.S. utility-scale electricity generation by source, amount, and share of total in 2023. Selected span s_cb9a294a4ff9d4c9, source character offsets 557–1157. The column headings are Energy source, Billion kWh and Share of total. These are preliminary 2023 net-generation data published in February 2024. PDF page is unavailable for this HTML source.

The model selected extra same-record context about small-scale solar and a U.S. fragment. These passages add no necessary support to the requested waste row and supply no claim. Record as unnecessary context, with the complete direct row and final answer supported.

Raw composer selected the verified unit. Application rendering produced the final prose. No fallback or editorial correction occurred in generation. NeMo passed.

[Exact result](actual-development-v1/cq1-a27.result.json) · [Source assessment](actual-development-v1/cq1-a27.assessment.json)

## Owner review

Confirm source support, requested amount/share completeness and wording for each case. You may accept the proposed U.S.-explicit editorial copies, request a specific change or reject. This records semantic/wording review. Saving an approved brief still requires review of that exact stored revision.

This diagnostic is consumed development evidence. It does not establish the twenty-case quality gates or production readiness.
