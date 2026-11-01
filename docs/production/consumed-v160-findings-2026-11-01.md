# Consumed v1.60 diagnostic findings — 1 November 2026

The owner-authorized batch stopped at r05's completeness failure. r03 passed assistant source and completeness checks, with exact-output owner review pending. r06 was not attempted. Both attempted workflows completed technically and passed NeMo; neither fact establishes answer completeness or production qualification.

| Case | Result | Main calls / NeMo | Worker duration |
|---|---|---|---|
| r03 | Answered the requested inflation causes; owner wording and warning review pending | 4 / 1 | 52.306 seconds |
| r05 | Failed the predeclared baht and baseline completeness criterion | 4 / 1 | 38.965 seconds |
| r06 | Not attempted after the failure | 0 / 0 | Not measured |

The closed batch used eight main-model calls and two NeMo invocations. Known main-model usage was 9,310 input and 707 output tokens; NeMo's internal usage remains unavailable. The remaining four main calls and one NeMo invocation are closed. There were no retries, Ragas, hosted inference, fresh twenty-case evaluation, approval/export, publication or deployment. These are consumed development cases, not unseen qualification results. Runtime v1.60, mapping v40, model settings, dependencies, corpus and benchmark data were unchanged during this batch.

## Supported r03 output and warning limitations

The draft retained the headline-inflation energy, government-subsidy base-effect and benzene-price explanations, and the offsetting movements underlying stable core inflation. Heading and section evidence establish December 2024. The automated geographic resolver remained unresolved; document-level Thai economic context supports the assistant's applicability assessment, but is not an additional citation in the generated claim. New exact-output owner review is required; earlier judgments do not transfer automatically.

The raw composer already included the substantive headline causes. A conservative lexical check nevertheless substituted a source excerpt. Its causal-omission event and generic fallback warning do not demonstrate that the original synthesis actually omitted those causes. Warning usefulness needs separate review.

## Why r05 failed

The answer distinguished application value from project count, but omitted required comparison context. It dropped the selected 2024 value of 1.14 trillion baht and the selected 2023 baseline of 2,235 projects. Adjusted 2023 application value of 846.5 billion baht was present in retrieved record `BOI_2024:unit:1:2` and in the offered span catalog, but was not selected.

The selected value span in `BOI_2024:unit:0:0` ended at an abbreviation before the currency/sector continuation. That continuation was offered separately but not selected. The underlying corpus contains these facts; the observations do not establish a GPU-capacity problem or an inherent open-source-model limitation.

An offline replay of the saved mapping, composition and scope reproduced the final claims without a projection fallback. Existing numeric checks reject unsupported values but did not require the requested financial comparison facts to survive composition. Structural component coverage and a NeMo pass were insufficient quality gates.

## Next engineering pass and human checkpoints

Repair financial sentence/continuation span handling within existing bounds, distinguish current/base-year value and count evidence roles, and enforce retention of requested selected comparison facts. Do not derive historical baselines from rounded growth, require the same span twice when it covers multiple roles, or silently present an unselected fact as a successful generation. Preserve this failed run before testing a repair.

The new r03 exact-output packet requires human semantic and wording review. r05's technical/completeness failure does not require repeated manual scoring. Exact-revision approval remains necessary before any export. Independent reviewer sessions remain a later requirement.

Detailed local evidence is in `reports/workflow_pilot/production-readiness-2026-10-27/resume-v74/`; raw attempts and hash-bound source gates are in `resume-v70/consumed-v160/`. New inference requires a repaired, reviewable protocol and a separate allowance. The full [Goal](../production-readiness-goal.md) remains incomplete, including fresh quality qualification, external usefulness evidence, current release CI and actual production operation.
