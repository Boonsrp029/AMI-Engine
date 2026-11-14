# Owner source review for the stopped aggregate-subject CQ1 batch

Both drafts are stored revision 1 and await owner adjudication. This packet records the exact generated wording. The stopped qualification remains a failed batch. An owner judgment here does not approve or export a stored revision.

## cq1-a19 — Biomass generation

**Question** — What were biomass generation and its share of US utility-scale generation in 2023?

**Exact draft claim**

> In 2023, the table gives Biomass (total) generation in Billion kWh as 47 and its share of total utility-scale electricity generation as 1.1%.

**Source check** — The pinned U.S. EIA utility-scale generation table for 2023 gives 47 billion kWh and 1.1% for Biomass (total). Check the row against the all-source denominator and the distinction between biomass and its child rows. The raw composer selected the verified row and the application rendered the quoted claim. [Pinned source text](pool/eia-generation.txt)

**Manual judgment** — Confirm source support and accept the wording or specify a change. The assistant assessment passed.

Result SHA-256 `5ea2007e840dc7b3aa664b1c9e144b7cd2496d9be1e98f314cba6c5577e39963`. [Exact result](actual-cq1/cq1-a19.result.json) · [Assistant assessment](actual-cq1/cq1-a19.assessment.json)

## cq1-a20 — Automated electricity meter reporting

**Question** — What did automated electricity meters report periodically, and who received those reports?

**Exact draft claims**

> Automated electricity meters periodically report electricity use to the utility, according to the EIA-measurement source.
>
> Utility companies measure and monitor electricity use with meters, as stated in the EIA-measurement source.
>
> These meters wirelessly send power usage data in real time, as per the EIA-measurement source.

**Source check** — The EIA measurement snapshot describes earlier automated meters periodically reporting electricity use to the utility. The next sentences switch to electronic smart meters and describe real-time wireless transmission for those meters. Source offsets are 1417–1503 for the historical reporting sentence, 1504–1555 for the electronic smart-meter antecedent, and 1556–1615 for the real-time sentence. [Pinned corpus](pool/public-corpus.json)

**Manual judgment** — Confirm the first claim's support. Assess whether claim 3's “These meters” misleads in the context of the historical question and whether claims 2 and 3 should be omitted. The assistant rejected the draft because claim 3 dropped the antecedent and attached the reporting behavior to the wrong meter scope. Any proposed wording is an editorial review of this historical draft.

Result SHA-256 `4741ae2de5959af277a60427263b7717eeab076c8e6b8c71192e4ba711f6a950`. [Exact result](actual-cq1/cq1-a20.result.json) · [Assistant assessment](actual-cq1/cq1-a20.assessment.json)
