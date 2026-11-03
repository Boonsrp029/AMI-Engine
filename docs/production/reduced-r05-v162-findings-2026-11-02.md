# Reduced r05 v1.62 findings — 2 November 2026

**Quality/technical gate failed; allowance closed.** The owner authorized the [prepared protocol](reduced-r05-proposal-v162-2026-11-02.md). One actual local mapper call completed; the engine rejected the selection before composition. The conditional full workflow, NeMo, other cases and twenty-case evaluation did not run. No retry, approval/export, publication or deployment occurred.

## Observed result

| Layer | Result and evidence boundary |
|---|---|
| Identity/transport | Pinned model verified before and after; HTTP 200, complete streamed response, normal stop reason. Service process returned 0 in 22.360 seconds. This verifies this request's transport, not production operation. |
| Parsing | JSON parsed as the new selection-only wire, with four supported components and known span identifiers. Required state/evidence fields were present. |
| Mapping validity | **Failed:** available financial-comparison baseline omitted. Offline validation process returned 1 in 17.094 seconds. No invalid mapping was converted into an abstention or silently repaired. |
| Source support/completeness | Selected current value and project-count passages were relevant, but the 2023 monetary baseline was available and unselected. No complete answer or source-quality pass is claimed. |
| Final answer / owner acceptance | No new draft exists. No manual scoring or acceptance is needed for this technical failure. Earlier owner judgments and approved exports remain unchanged. |

Total diagnostic orchestration was **39.625 seconds**, below 95 seconds. Known main-model usage: **3,374 input + 151 output = 3,525 tokens**. There was one actual main-model call and zero NeMo invocations. These counts do not establish general context fit, sustained latency or monetary/energy cost. The service completed normally; backend cancellation was not exercised or qualified.

## Exact cause

The mapper selected the current-value span for both monetary request slots and the combined count-comparison span for both count slots. It omitted the monetary baseline from both value slots while declaring them supported.

| Evidence | Locator in pinned BOI release | Selection |
|---|---|---|
| 2024 application value of 1.14 trillion baht, reported 35% growth and sector drivers | `BOI_2024:unit:0:0`, zero-based index 0 / PDF page 1; span `s_353f4d3848bbf880`, offsets 312–832 | Selected for r1 and r3 |
| 2024 applications/projects 3,137 versus 2,235 in 2023, reported 40% growth | `BOI_2024:unit:1:2`, index 1 / PDF page 2; span `s_728ed11317b934dd`, offsets 209–400 | Selected for r2 and r4 |
| Adjusted 2023 application value of 846.5 billion baht | Same source record, index 1 / PDF page 2; span `s_e219f668da26f12a`, offsets 401–504 | **Available and offered; omitted** |

Offsets are Python character offsets with an exclusive end. Source identity, text hash and original passages are retained in the ignored local evidence. The [BOI release](https://osos.boi.go.th/article_attach/PR4_2568EN.pdf) was published on 13 January 2025; the requested measurements are 2023/2024. This audit uses the pinned local snapshot, without a new download.

The frozen request already contained current/baseline/change coverage requirements and the baseline span choice. The generated supported-component JSON schema allowed a list of any eligible identifiers, without expressing those coverage requirements. Consequently a one-span current-only selection parsed successfully but failed the application validator. A socket-blocked replay of the actual saved response reproduced exactly:

`Selected evidence omits available financial comparison coverage: baseline`

This is an observed model selection failure plus a mismatch between decoder-permitted structure and application-required coverage. The validator performed its intended protection. The record does not establish an authentication failure, inadequate GPU capacity, a timeout, or an inherent limitation of all open-source models. Exact quote provenance alone would not make the incomplete comparison acceptable.

The model also marked geography unresolved with a generic reason despite Thailand appearing in selected text. This remains a secondary applicability/wording issue to inspect, not a reason to waive scope checks or manufacture a known geography. The earliest baseline-coverage failure is sufficient to stop the batch.

## Next technical action, not a new generation grant

Prepare an offline schema/validator alignment pass: express structurally enforceable current/baseline/change coverage in the decoder's supported/partial alternatives, preserving explicit missing/conflicting states and shared spans that cover several roles. Do not automatically insert the omitted source, infer a baseline from rounded growth, loosen the coverage rule or mark the original run successful. A minimum evidence count alone would not prove role coverage when optional alternatives exist.

Use synthetic separate/shared-span fixtures and this retained response to verify valid selections remain possible and incomplete selections are rejected consistently. Measure the resulting schema/request size before proposing another bounded actual test. Semantic relevance, years, geography and source support still require inspection even if structural constraints pass. Any changed generator needs a new frozen protocol and direct allowance; the unused portion of this run cannot be reused.

## Preservation and manual checkpoints

Raw service stream/result, parsed selection, process outcomes, offline replay and structured assessment are retained under `reports/workflow_pilot/production-readiness-2026-10-27/resume-v77/mapper-only-r05-v162/` and `resume-v82/`. Earlier attempts, judgments, source snapshots and exact approved exports remain historical evidence. No application or dependency change is part of this diagnostic.

No repeated human scoring is requested for this failure. Any later assessable final draft requires owner source/wording review; stored approval/export remains an exact-revision action. Independent reviewer usefulness, fresh held-out quality, current release CI and actual Databricks/security/operations/load qualification remain incomplete under the full [Goal](../production-readiness-goal.md).
