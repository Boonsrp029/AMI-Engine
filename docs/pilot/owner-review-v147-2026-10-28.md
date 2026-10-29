# Owner adjudication of v1.47 r03/r04 — 28 October 2026

**Owner review completed; request changes (minor).** The owner confirmed source support, completeness and usefulness for both original outputs, and requested explicit Thailand wording in the claims. This is owner evidence, not independent reviewer usage, a numerical rating or approval of a new edited/exported revision.

The original chat wording is retained in the separate local adjudication record, with a hash and links to the frozen attempts. Visible owner wording follows; chat line endings are normalized:

> v1.47 source review: Owner's verdict: request changes (minor).
>
> r03: source support confirmed; fully and completely supports the query and provide useful responses. Regarding geographic applicability I understand that the assistant's notes are that Geographic scope is unresolved. From the claims provided it is likely that the issue is from the wording in the output claims. This can be resolved by adding the country's scope into the output, for example, Thailand's core inflation and/or headline inflation.
>
> r04: source support confirmed; fully and completely supports the query and provide useful responses. It also flags a geographic applicability warning which, again, can be resolved by adding the country's scope into the output claim.

## Applied editorial correction

Two separate country-clarified candidates add Thailand to the title and each claim's subject. The r03 lead subjects are “Thailand's headline inflation” and “Thailand's core inflation.” The r04 subjects are “Thailand's private investment indicators” and “Thailand's private investment.” Dates, quantities, direction, explanations and existing citation order are preserved. An already retrieved country-context citation is appended; no original citation is replaced.

The new candidates replace the unresolved-geography warning with a transparent note that country scope comes from owner source review and has not been automatically revalidated. Other warnings remain. Public `Draft` and citation checks pass for both candidates. No new model, NeMo, Ragas or retrieval request was made, and no runtime code or library version changed.

| Case | Owner finding | Requested edit and provenance |
|---|---|---|
| r03 | Source-supported, complete, useful; minor change requested | Add Thailand to headline/core-inflation claims. Facts remain BOT_DEC2024 units 4/13; country context is the already retrieved unit 13, chunk 2, containing the explicit Thailand reference. The owner confirmed applicability of the report context. |
| r04 | Source-supported, complete, useful; minor change requested | Add Thailand to monthly/quarterly investment claims. Facts remain units 9/14; already retrieved unit 3 describes the Thai economy. The owner confirmed that national context applies. |

Country-context references support the reviewed interpretation of the document; they are not automatic entailment proofs for each financial statement. The original request's country and the report issuer alone were not substituted for evidence.

## Why the generated warning remains meaningful

The mapper deliberately requires source-backed geographic resolution and explicitly disallows inferring Thailand solely from “Thai” or “Bank of Thailand.” Adding a country word to rendered text would not resolve that internal field. These editorial candidates therefore use **owner-adjudicated context**, without silently weakening the general resolver or claiming automatic validation.

A later runtime improvement should carry validated document-country context into per-claim scope, preserve its identity and provenance, and reject conflicting or inapplicable scope. An unconditional country default or removing warnings from all answers is not justified by this two-case adjudication. That functional change remains separate from these wording corrections.

## Evidence and remaining human checkpoint

Local record: `reports/workflow_pilot/production-readiness-2026-10-27/resume-v7/owner-adjudication-v147/adjudication.json`. The adjacent `country-clarified-candidates.md` contains both exact candidates, source-context passages and retained warnings; the two JSON candidates have recorded hashes.

The frozen v1.47 outputs, old packet/status fields, completed `human_review.csv`, prior judgments and approved exports are unchanged. The new record establishes the current owner adjudication without rewriting that history. No human numerical ratings or task-time observations were invented.

Only the changed country wording/context citation needs exact-candidate acceptance if these drafts are to become accepted briefs; the original factual scoring need not be repeated. Saving/exporting a brief still requires approval of the exact saved workflow revision. No SQLite approval or export was created. External reviewer usage and production qualification remain pending.
