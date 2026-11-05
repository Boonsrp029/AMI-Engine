# A integration: guarded composition lineage in the owned runner

The integration below is implemented in A-owned `_handoff.py` and `runner.py`, consuming C's [handoff proposal](c-runner-integration-proposal.md). Real spawned fixed-response tests and the full Windows/Linux offline suites pass. See [completion audit](completion-audit-a.md). No inference grant, public API change or dependency change was needed for this offline implementation.

## Current behavior

Before this pass, `runner._child` accepted only a plain Draft dictionary from `compose(report, access)`. It now also accepts C's unguarded `SynthesisResult(draft, provenance, diagnostics, safety_passed, guarded_sha256)`. Parent-side `run_stored_plan` saves only after clean child exit and current-attempt/corpus/accounting checks. C's standalone `persist_synthesis` is not called by the owned child: the parent remains the sole database writer.

The shared Report retains branch/source origins; parent events retain accepted Result envelopes. C's claim-to-evidence-unit attribution and raw/fallback diagnostics now persist as a separately labeled candidate and revision metrics. A plain Draft remains a valid legacy callback return.

## Reviewable changes and ownership

1. A adds an internal composition-handoff helper and integrates it in A-owned `runner.py`. C's `synthesis.py`, source selection and semantic validators remain C-owned. Do not edit D's test fixtures.
2. Accept either a plain dictionary or an unguarded C `SynthesisResult`. Reject another report/attempt/corpus identity, pre-guarded results and malformed lineage. Validate origin references against actual accepted child/source identities. Never interpret a mutable boolean as proof of safety.
3. Snapshot the validated draft, sources, lineage and diagnostics through strict JSON serialization. Add optional-branch warnings before the final safety check. Route safety through the existing single `ModelAccess.guard` invocation; do not call C's standalone guarded-persistence path or double-count NeMo.
4. Bind the exact final draft/source/lineage snapshot to safety. A callback that changes guarded content must not publish a modified draft. Preserve empty-claim abstention's zero-guard and no-approval/export policy.
5. Return an internal candidate artifact with the child result. Parent validates identity/digests, waits for clean child exit, rechecks corpus/attempt/accounting and records `composition_candidate` through the fenced Store API. Label it as a candidate, never approval or successful publication. Save lineage/diagnostics in the revision's metrics through existing `save_draft`; retain the draft/source digest in history for later edits.
6. No table/schema migration or public Draft/API change. Keep old dictionary callback metrics compatible. Candidate-event failure must stop draft publication. Cancellation after candidate persistence may retain an unapproved candidate, but cannot publish a draft from a stale attempt.

## Fixed-response acceptance checks

- A real spawned worker returns C's unguarded projected result, with two bounded fixed main callbacks and exactly one final safety call. Stored claim provenance retains unit, subtask, child attempt, source content hash and corpus identity.
- Raw and fallback attribution survive in diagnostics and immutable candidate history; subsequent editing cannot rewrite the original candidate.
- Plain dictionary callbacks keep working. Wrong identity, unknown source/child origin, malformed typed result and pre-guarded result are rejected without a second guard or repair call.
- Guard rejection and guard-time draft/lineage/source mutation produce no draft. Cancellation, corpus change, deadline, abnormal exit and stale attempts also publish no draft.
- Exact-revision review/export and edit invalidation remain unchanged; cached approved bytes remain identical.
- Use frozen synthetic facts distinct from r07 and reserved qualification facts. These tests establish structural plumbing, not semantic model quality.

After targeted checks pass, freeze a new combined source snapshot and run the full Windows/Linux offline suites. The preceding scheduler snapshot remains historical baseline evidence and must not be relabeled as validation of this new handoff. Recheck usage before implementation and long validation; at 90% used save an exact handoff and pause.
