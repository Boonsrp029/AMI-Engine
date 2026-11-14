# Owner source review for cq1-a14

Status **pending owner adjudication**. This is revision 1 from the stopped CQ1 batch. Reviewing this result records source and wording judgment for this exact draft.

**Question** — What were petroleum coke generation and its share of US utility-scale generation in 2023?

**Stored draft** — In 2023, the table gives Petroleum coke generation in Billion kWh as 5 and its share of total utility-scale electricity generation as 0.1%.

**Source** — The pinned U.S. EIA utility-scale table for 2023 lists Petroleum coke at 5 billion kWh and 0.1% of the total. The row is distinct from Petroleum (total), which is 16 billion kWh and 0.4%. The table is preliminary February 2024 data. [Pinned source text](pool/eia-generation.txt)

**How the draft was produced** — The raw mapper selected span s_cb9a294a4ff9d4c9, offsets 557–1157 in source eia-generation-2023. The raw composer selected unit u1 for component r1. The application rendered the verified table row and kept its citation. NeMo passed. No fallback or editorial correction was applied.

**Manual review** — Confirm the row, period, unit and denominator support the claim. Then accept the exact wording or specify the change you want. The failed cq1-a15 attempt produced no draft to review. Owner review of this case is separate from approval, export and qualification of a future batch.

Exact result SHA-256 `919a9042e75a010677eaa5e0855c98a5db3c91e71e8d6333ab91759e64834522`. [Retained result](actual-cq1/cq1-a14.result.json) · [Assistant assessment](actual-cq1/cq1-a14.assessment.json)
