# Proposed private concurrent composition instruction contract

**Proposal only. No runtime or prompt change is implemented by this document. No new inference grant exists.** C owns the concurrent-only adapter/tests; A/B interfaces, shared sequential composition, retrieval and library versions remain unchanged.

## Current behavior and evidence

`ConcurrentComposer` sends the shared `COMPOSITION_INSTRUCTION` and `_composition.payload()`, including one global request and separately bound representative units. The response schema constrains unit/component IDs and ordering, while prose is free. Strict application validation checks each sentence against its selected unit. In actual v6 the mapper selected both facts, but the composer answered the whole comparison in each claim, duplicated a relative assertion and borrowed another unit's period/rate. The strict guard rejected before safety. The exact payload/rejection is retained in `v6-offline-replay.json`; r07 remains a separate historical failure.

The shared instruction already says to compose independently and not duplicate another unit. It also includes specialized investment/count/ranking/coverage rules unrelated to this request. Existing unit cues are necessary context, not proof the model obeys them. Do not weaken the numeric guard, merge evidence units merely to admit the bad sentence, count fallback as raw completeness, or replace free-prose interpretation with a source-selection success claim.

## Proposed small passes

1. Define a short **concurrent-only** composition instruction, replacing the shared instruction at this private callback only. State first: each returned claim answers only its supplied unit; the global request explains the overall task and does not authorize repeating a whole-question answer in every slot. Preserve the schema, quotations, origins and source-literal cues.
2. Explicitly distinguish side-by-side reporting from a quantitative relative comparison. Do not infer a relative difference, rank, conversion or arithmetic relationship unless that relationship is established by the selected unit's quotations and requested. Never compare a historical observed rate with a future annual projection as demand levels. Use different synthetic facts/examples, not consumed case values.
3. Keep all applicable existing rules: number/unit/denominator, geography/period/scenario, annual versus cumulative, negation, missing/conflict handling, instruction-like sources, citation assignment, omission/fallback disclosure and bounded five claims. Preserve the four-call ceiling, same model/settings, final safety and exact-revision lifecycle. No repair loop or extra model call.
4. Test the exact callback instruction/schema/request wire with fixed responses; replay saved bad outputs to prove rejection is retained. Exercise supported partial/missing and optional/context branches as well as complete units. Recount actual composition message and grammar budgets, and run targeted integration checks. Broaden once if runtime changes justify it.

This explicitly changes the private concurrent instruction contract; it does not change public Draft, API, SQLite schema, retrieval ranking or sequential workflow. It still relies on model interpretation, so successful offline checks will not prove a factual improvement. Prepare a bounded composer-only/frozen-stage diagnostic before proposing another full workflow; new scope/budget/owner grant must be concrete. Do not reuse the closed v6 grant.

## Acceptance and risks

Offline acceptance requires unchanged strict rejection of cross-unit numeric/date/measure/basis transfers, safe partial answers, final safety, provenance and approval/export. Actual acceptance requires a source-supported, complete raw response and separately reported final/fallback behavior under an explicit grant. Human source/wording acceptance remains a later exact-output step.

A shorter instruction may lose specialized behavior, so only the concurrent adapter changes and relevant fixed-response contracts must be retained. Neither prompt wording nor schema parsing can guarantee semantic support. If the actual model still fails after a well-defined bounded diagnostic, report it rather than starting repeated silent prompt tuning or substituting an easier success criterion. Per-unit extra model calls, deterministic text rendering as a replacement for composition, changing models/limits and migrations require separate explicit design/scope decisions.
