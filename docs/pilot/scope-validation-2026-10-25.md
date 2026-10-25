# Fresh local scope validation — 2026-10-25

**The period repair passed its check on a fresh mapper response, but the overall gate failed on geography retention.** Generation stopped after the first probe. No application, prompt, dependency or test changes were made. These are assistant-authored findings, not human acceptance or a general model benchmark.

## Frozen experiment

Three fresh synthetic fixtures and checks were frozen before generation: scoped multipart evidence with punctuation/distractors, a missing dated observation, and causal explanation versus measurement definition. The allowance was at most three one-shot mapper probes, stopping on first failure; only three passes could open d01/d02/d03/d04/d06 once each, at four workflow calls maximum. No retries, hosted inference or Ragas were included.

Unlike the older stopped experiment, these new checks allow raw short answers to be fragments and evaluate final application scope retention. Geography must remain in the projected title/claims, and the requested period must qualify the capacity claim. Fixed positive examples exercised the harness before generation; they are not model-quality evidence. Fixtures/checks and implementation hashes were pinned before the first call.

## Retained result

The question asked for Juniper Reach's installed storage capacity in February 2021 and support for expansion. The mapper selected the exact intended capacity/expansion spans and answered **23.4 GWh** and **new battery halls entering service**. It excluded unrelated solar-generation and tariff material, retained the source punctuation and used valid anchors.

The application resolved the supported period and produced **February 2021: 23.4 GWh** in a deterministic fallback projection. That projection used a scripted empty composer, not an additional model call. It retained the period in its title as well.

The sole failed check was geography: **Juniper Reach** was absent from the projected title and claims despite occurring in the question and selected quotation. The raw JSON omitted `geography`; the schema permits omission and parsing inserts `""`. The scope helper intentionally does not infer geography, so there was no geographic value to propagate. This is a remaining response-contract gap, rather than a retrieval miss, incorrect capacity figure or quotation error.

| Layer | Result |
|---|---|
| Parsing, exact spans, anchors and citations | Passed |
| Capacity figure, expansion support and distractor exclusion | Passed for these synthetic facts |
| Requested period in final projected capacity claim | Passed |
| Geography in final projected title/claims | Failed |
| Missing-observation and causal-definition probes | Not run after stop |
| Five analyst workflows | Not run; gate closed |
| Actual composer / NeMo behavior | Not tested in this probe |

The one mapper call used **763 input and 99 output tokens**, took **15.10 seconds**, and ended normally with `stop`. It was not truncated. This does not establish an inherent open-source-model limitation or insufficient GPU capacity. A real composer might handle geography differently; none was run, and the deterministic fallback path did fail the frozen criterion.

The [structured record](evidence/scope-validation-2026-10-25.json) contains checks and provenance. The previous 204-test/three-warning result remains historical offline evidence; the full suite was not rerun because implementation was unchanged. The [integrity check](../../reports/workflow_pilot/scope-validation-2026-10-25/verification.json) verifies preserved files and frozen inputs.

## Next technical action

Make geography explicit in the mapper response contract instead of silently defaulting an omitted value to empty. Retain selected-span provenance and distinguish a genuinely unresolved location from a schema omission. Add offline regression checks before any further generation. Preserve partial facts and avoid guessing locations from capitalized or possessive phrases. Keep this stopped experiment and its checks unchanged; another experiment requires a new bounded run.

## Where manual human review is required

| Stage | Human action |
|---|---|
| Current technical failure | **No mandatory score.** Geography omission is directly inspectable in raw JSON/schema/projection. |
| Current synthetic packet | Optional inspection of the unchanged response, quotations and findings. |
| Future actual drafts passing technical checks | **Required:** assess claim support, completeness, geographic/temporal/measure/scenario scope, causes (especially d03), partial answers and gaps. |
| Export | **Required:** approve that exact draft revision. |
| Independent-usefulness claims | **Required later:** external reviewers complete real tasks and provide feedback. |

The [local review packet](../../reports/workflow_pilot/scope-validation-2026-10-25/review-packet.md) marks these points. Your previously saved checklist, completed CSV, owner judgments, sources and historical outputs remain unchanged. **Do not edit `human_review.csv` for this technical probe.** The [handoff](../../reports/workflow_pilot/scope-validation-2026-10-25/handoff.md) identifies the exact next action.

**Verdict: Request Changes.** Period retention is demonstrated in this one actual-mapper-plus-deterministic-projection example; geography completeness and the remaining local gates are unresolved. No commits, pushes, deployment or reviewer contact occurred.
