# C-to-A runner integration handoff

Status: **A applied the integration handoff** through runner.py and _handoff.py.
The combined targeted validation passed79tests; integrated full-suite validation
passed 1,440 tests with 15 warnings and no pinned source drift. The proposal below records the reviewed design and acceptance checks.

The shared contract assigns A sole integration ownership of runtime/runner/store
boundaries. Current runner.py calls `draft=compose(report,access)` and constructs
fixed metrics; returning only a Draft loses C's claim/evidence-unit provenance.

## Proposed additive internal callback result

Keep existing dict-returning callbacks supported. Permit an opt-in callback to
return C's `SynthesisResult` from `project_report` (`safety_passed=False`).

1. In the owned child, recognize this typed result, check diagnostic identity
   against the current Report identity, and extract its Draft for the existing
   citation, warning-capacity and final safety path.
2. Reject a pre-guarded result to avoid unaccounted/double NeMo. Route selection
   and composer callbacks through ModelAccess.main; final safety remains the
   runner's single ModelAccess.guard invocation. Empty claims retain zero guards.
3. After successful final safety, include claim provenance, raw/fallback diagnostics
   and current identity in a separate internal composition artifact. Keep public
   Draft unchanged and retain the old result behavior for dict callbacks.
4. Parent waits for clean child exit and existing corpus/attempt/budget checks.
   Before publication it records a composition_candidate artifact via the existing
   fenced Store API; label it candidate, never approval or proof of publication.
5. Save lineage in metrics in the same revision publication path. Retain the
   candidate's draft/source digest so historical edits cannot erase attribution.
   Recheck exact identity; no child-side database write or new database table.
6. Failed safety, cancelled/stale attempts, modified corpora and worker failure
   publish no draft. Existing revision review, export and edit invalidation apply.

## Acceptance tests

Use real run_stored_plan with spawned synthetic adapters. Assert one safety call,
two bounded main callbacks, persisted unit/subtask/source hashes and child attempts,
raw versus fallback attribution, no publication on rejection/cancellation, and
approval/export/edit-invalidates-approval behavior. A plain legacy dict callback
must still work. Reject typed results from another Report/attempt or pre-guarded
outputs. No generation, dependency or public API change is required.

Current C tests already cover standalone guarded publication and rejection of
safety-pending persistence; they do not prove this spawned runner extension.

Safety addendum: snapshot/bind the exact draft and lineage checked by final safety
to the artifact persisted by the parent. C standalone guarded persistence now
uses a fingerprint over draft, provenance, diagnostics and source results; edits
after guarding reject. A must preserve this invariant in the spawned boundary,
without treating a mutable safety_passed flag as proof. C safety-seal targeted
run:31passed, including D synthesis integration and post-guard tampering tests.

Upstream validation update: D semaphore cleanup revision passed all five owned-
runner integration cases (reports/workstream-c/d-cleanup-fixed.txt). The obsolete
full-suite process stalled in the old cleanup was stopped after process identity
verification; its faulthandler evidence remains preserved. That historical provenance dependency is resolved by the integration above.
Final integrated targeted tests:79passed; full suite:1,440passed.
