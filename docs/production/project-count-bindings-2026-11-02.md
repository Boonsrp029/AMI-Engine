# Preserve explicit project-count comparisons safely — 2 November 2026

This offline pass addresses a conservative count-omission flag observed in the [actual r05 v1.63 diagnostic](reduced-r05-v163-findings-2026-11-02.md). Runtime is now **analyst-pilot-v1.64**; mapping remains requested-evidence-v43. The exact v1.63 output and pending owner review are unchanged. No new model or NeMo request is made by this repair.

## Observed behavior and rejected shortcut

The raw composer had already expressed both counts and their years, but its wording placed the unit before the numbers: “Number of projects …”. The existing literal quantity parser recognized number-plus-unit forms, so the completeness check treated those counts as missing and used exact-source fallback.

A separate offline probe demonstrated that merely finding both expected numbers after a project-count heading is unsafe: the same numbers can be assigned to the wrong years. That proposed shortcut was rejected without changing the application. Numeric membership alone does not establish a year/value relationship.

## Bounded source binding

Within the existing four-slot historical application-value/project-count comparison guard, a narrow recognizer now handles explicit project-count wording with two years, two integer counts, a reported percentage and a change direction. It compares the ordered bindings in the candidate with a uniquely established comparison in the selected source quotations.

The source vocabulary covers the observed number-of-applications/projects form, including optional investment-promotion/all-sectors wording and an explicit January-to-December annual period. Selected source quantities must independently establish project units. The candidate must explicitly introduce the number of projects. Both requested years, counts, reported percentage and direction must match. Increase/decrease direction must be consistent with the source count ordering; reported growth is compared literally, not recalculated from rounded figures.

A recognized candidate with different year/count/growth bindings raises the existing unsupported-quantity error. An unknown, multi-sentence, unparsed or ambiguously sourced form does not gain this exception to the omission check. Existing fallback, numeric/unit/period validation and final guardrail behavior remain in place. Other request grammars, unknown units and unrecognized source relationships retain their previous behavior.

This is a narrow syntactic relationship check. It does not establish entity identity, geographic applicability, causal support, general semantic equivalence or independently correct source statistics. It does not calculate growth, infer dates, insert sources or transform an invalid response into an abstention. Monetary omissions still use the existing logged fallback; this pass does not clean up press-release headers or rewrite the draft awaiting owner review.

## Validation and parity boundaries

Twenty-five synthetic tests extend the 1,194-test Windows baseline. They cover correct prefix/suffix wording, case/whitespace and percentage formatting, swapped years/counts, changed direction/growth, invented counts, missing baselines, wrong measures/scales, forecasts/commands, multi-sentence ambiguity, unknown or conflicting sources and duplicate identical evidence. The first five tests failed against the old code; red logs remain preserved.

Final checks:

- **102 targeted tests passed.**
- **1,219 Windows tests passed**, with 15 existing warnings.
- **1,218 Linux tests passed, one skipped**, with 15 existing warnings; sanitized snapshot, source/image identity checks and networking disabled.
- Dependency checks remain clean; no library version or dependency manifest changed.
- Non-root container recovery/restart checks preserve all four cached approved exports and the original backup, with no model inference or human decisions.

The Linux image is a source-only overlay on the existing dependency image. These checks are not a fresh dependency rebuild, remote CI or a change to the running Docker Desktop application.

## Frozen-response replay

With sockets blocked, replay of the saved r05 tool/mapper/composer responses retains the numerically correct count sentence exactly. Only the monetary components still require source fallback. A separately labeled counterfactual swapping the counts between years rejects before the safety test double is reached.

The replay uses a fixed guardrail result and makes zero actual model/NeMo calls. It proves the code path, not real model quality or actual safety performance. The original v1.63 attempt, its generation-time status and the exact owner-review packet remain byte-identical; the replay is not substituted for them.

Public APIs, Draft/SQLite shape, prompts, model/context/completion settings, retrieval, selection wire and approval/export controls are unchanged. The runtime version changes because output-retention and validation behavior change. Evidence is retained under ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v86/` and `resume-v87/`.

## Human checkpoint and remaining work

The owner source/wording review for the **v1.63 exact output** remains pending. No repeated human score is needed for this engineering check. Any future assessable generated output and any stored approval/export retain their separate exact-draft decisions; earlier acceptance must not transfer automatically to a replay or new runtime.

All previous generation allowances are closed. This repair does not authorize another diagnostic or the held-out set. Fallback readability, fresh quality, independent reviewer tasks/feedback, intended-release CI and actual operational/Databricks qualification remain required by the full [Goal](../production-readiness-goal.md). Neither milestone is complete.
