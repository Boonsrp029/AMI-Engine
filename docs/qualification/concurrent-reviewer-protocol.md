# Reviewer protocol — concurrent workflow v1

Status: prepared, no sessions or reviewer outcomes recorded. Reuse the [existing kit](../pilot/reviewer-session-kit-2026-10-31.md) and [release contract](../production/release-contract.md). Owner arranges 1–3 independent peers and permission for anonymized notes. Consent is separate from execution authorization and draft approval. Owner assessments and independent participation must be reported separately.

## Session admission

Pin the integrated source manifest/revision, image, model digest/settings, prompt/mapping, corpus, plan and UI version. A's contract limits read-only branches to 1–5, retrieval concurrency to 1–2, model concurrency to one and parent-wide main calls to four; these are engineering limits, not measured service SLOs. Confirm the actual integrated implementation with A–F. Live mode requires applicable technical and quality gate evidence plus a new explicit generation budget; no closed allowance may be reused. If unavailable, permit only labelled frozen-draft or synthetic progress inspection.

## Tasks and conditions

| Activity | Material | Observation |
|---|---|---|
| Manual brief | Consumed r03: December 2024 Thai headline/core inflation; pinned BOT release | Checked final brief, checking/editing effort, omissions |
| Assisted brief | Consumed r04: Thai December private investment versus Q4 movement and categories; same pinned source access | Raw draft through checking/correction/decision, failure and waiting time |
| Counterbalance | Reverse task/mode order for next reviewer where feasible | Record assignment and familiarity; do not give reference answers or owner judgments first |
| Progress comprehension | Labelled synthetic timelines: concurrent running/waiting, optional failure, required failure, cancellation | Ask what is active, what failed, whether drafting may proceed and whether approval exists |
| Visible/hidden progress comparison | Matched synthetic scenarios; reverse order when feasible | State-identification errors, confusion, checking actions and subjective usefulness |

Task cards are detailed in the existing kit. Supply identical source access across manual and assisted modes. Different tasks, repeated source exposure and 1–3 reviewers cannot establish causal speedup. Concurrent versus sequential comparisons require matched tasks, a declared comparison protocol and separate live budgets; do not infer them from a manual/assisted comparison.

Do not use reserved cases for demonstrations or tuning. The older kit's blanket r07 reservation is historical: r07 was consumed by the v1.68 failure. Reconcile every task against the current qualification manifest before sessions; preserve the remaining nineteen reserved cases. Do not assume a historical heldout label proves independence.

## Recording procedure

1. Record alias, actual consent, mode/order, prior familiarity, task and frozen identities. Modes: manual, assisted_live_sequential, assisted_live_concurrent, assisted_frozen, progress_synthetic. No sensitive customer/KYC/payment data.
2. Start the total timer when task/source access is supplied; stop after the checked final brief and decision, or abandonment. Include waiting, checking and correction. Record interruptions and incomplete outcomes. Do not reset on failure or conceal retries.
3. Capture waiting/checking/correction/decision intervals where observable. Overlapping activities are not additive; mark the overlap and method. Frozen-draft inspection excludes generation and is not end-to-end assisted latency.
4. Preserve raw output, each revision, material edit/reason, unsupported claims and requested omissions with evidence locators. Separate unsupported, contradicted and unverifiable judgments. Do not change reference answers to agree with a reviewer.
5. Ask usefulness 1–5 with explanation, what would prevent reuse, and whether progress/warnings helped. Unknown or declined ratings remain null, never zero. Record the reviewer's words without leading answers.
6. Record completion as complete, partial, abandoned or blocked with reason. Manual tasks have no application run/revision ID. A session decision is not a stored application approval. Human approval/export must target the exact revision; edits invalidate approval and empty claims remain unexportable.

Use templates/session-record.json and templates/claim-finding.json. No examples contain actual observations.

## Analysis and feedback

Report participant/task counts by mode, raw times, missing observations, failed/abandoned tasks, checking/correction burden, material edits and qualitative progress findings. Never silently remove failures to improve averages. Describe successful-task timing separately if useful, with its denominator and exclusions. No inferred ROI, production scale or model-quality score.

Select one improvement traceable to real independent feedback; preserve its finding IDs, proposed change and rationale. Coordinate implementation ownership, repeat affected engineering checks and, where appropriate and arranged by owner, the affected task. Preserve before/after inputs and familiarity effects; claim only the observation supported. Until sessions occur, reviewer evidence and feedback-driven improvement remain pending.

## Ready-to-use progress materials

[Participant synthetic cards](progress-task-cards.md) and a [separate facilitator rubric](progress-facilitator-rubric.md) provide matched visibility probes plus required-failure/cancellation boundaries. Keep expected answers out of participant packets until responses are recorded. They establish no live execution or quality evidence.
