# Workstream C: aggregate synthesis boundary

Status: opt-in Python integration implemented; final offline audit in progress.
No model generation or browser activation is enabled by this module.

## Interfaces

`src/pilot/subtasks/synthesis.py` consumes A's `Plan` and scheduler `Report`.
Callers provide an evidence mapping, composed response, explicit component-to-branch
bindings and an as-of date. Retrieval keywords are not treated as question anchors.

- `project_report(...)` returns a `SynthesisResult` marked `safety_passed=False`.
  This is the projection seam for runners that own the final safety invocation.
  It must not be persisted as a guarded result.
- `compose_report(..., guard, is_current)` performs projection and checks final
  safety, including fallback claims, before returning a guarded result.
- `persist_synthesis(store, report, result)` requires guarded matching identity.
  It checks a fingerprint binding the guarded draft, provenance, diagnostics and
  source results against post-guard mutation, records a `composition_candidate`
  event, then uses Store's existing atomic
  attempt fence and revision creation. Candidate artifacts are not approvals or
  proof of publication. Publication may fail after the candidate event is saved.

The existing sequential entry points remain unchanged. A has integrated the
opt-in spawned runner through `_handoff.prepare`, candidate sealing and parent
verification. It accepts safety-pending typed results, invokes final safety once
for nonempty claims, and persists C lineage and diagnostics after clean worker
exit and current-attempt checks. Legacy dictionary callbacks remain supported
without invented lineage. The targeted integrated run passed 79 tests; full-suite
validation passed 1,440 tests with 15 warnings in
`reports/workstream-c/integrated-landed-full.txt`, with no pinned source drift.

## Rules and lineage

Required technical failures block drafting with branch IDs. Optional technical
failures produce explicit unresolved-coverage warnings, not claims that no
information exists. Completed missing/conflicting outcomes remain visible while
supported independent answers are retained. Every declared branch must be bound.

The adapter rechecks source hashes, corpus/parent identity, completed states,
child-attempt uniqueness, aggregate consistency and plan ordering. A component
can select supporting sources only from its bound branches. Context-only records
cannot support claims. Existing exact-quotation, numeric/measure and composition
validators remain active. Explicit observed/projected lexical checks are narrow
regressions, not a general semantic classifier or entailment judge.

Canonical claim coverage is expanded back to original evidence units, source
hashes, component IDs, subtask IDs and child attempt IDs. Shared evidence retains
all matching origins. Raw composed output and fallback diagnostics are retained;
editorial correction remains a distinct later revision. Warning/claim capacity
errors fail explicitly rather than silently truncating required coverage.

Persistence stores lineage and diagnostics in current metrics and a historical
candidate event keyed to a draft/source hash. Existing Store review/export rules
remain authoritative: human confirmation of an exact revision, no export before
approval, edits invalidate approval, and cached approved exports remain stable.
Do not use a `safety_passed` flag from an untrusted external object: this is a
trusted internal API, and Store/guard/attempt controls are still required.

## Validation and limits

Fixed-response tests cover numeric/date/measure substitutions, explicit forecast
versus observation wording, partial/missing/conflicting branches, rejected guard
verdicts, cancellation fences, stale/changed identity, fallback lineage and a real
scheduler-to-Store approval/export lifecycle. No test is model-quality evidence.
The original r07 failure remains consumed and unchanged; reserved evaluation
facts must not be used for tuning. Final test results and preservation checks are
recorded in `reports/workstream-c/`.
