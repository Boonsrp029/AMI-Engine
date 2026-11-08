# C scoped disclosures — A integration handoff

7 November 2026. Owner authorized **offline C implementation and an A handoff**.
No generation, agent delegation, publication or deployment is included.

## Status and ownership

C implements the separate `ScopedConcurrentComposer` in
`src/pilot/subtasks/_scoped_generation.py`, using `DisclosureScopes` and typed
Report/Result projection in `_disclosures.py`. `project_report()` accepts an
additive private `disclosure_scopes=None` keyword. Existing calls remain unchanged.
No browser, API, runner, Store, scheduler, ranking or dependency file was changed.
The old `ConcurrentComposer` and sequential paths remain the defaults.

**A applied explicit activation on 7 November 2026.** The development call site
in `qualification_runner.py` now chooses through `prepare_composer()`. Do not
substitute the new callback based on an environment default or silently upgrade
an old frozen contract. Keep all prior failed wire versions executable through
their retained snapshots.

## Exact internal interface

```python
from src.pilot.subtasks._scoped_activation import prepare_composer

compose = prepare_composer(
    contract=frozen_contract,
    frozen=frozen_case,
    runtime_plan=plan_after_preparation_deadline_reservation,
    transport=existing_local_transport,
    capture=existing_immutable_raw_capture,
)
# Pass compose to the existing run_stored_plan boundary, after explicit opt-in.
```

For the new path require `composition_contract: "cq-scoped-composition-v1"`.
Each case supplies `requested_scopes` (sidecar path) and
`requested_scopes_sha256`. Its resolved absolute path and hash must also occur in
the frozen contract's `input_sha256` map. Marker-free old contracts retain the
old callback; scoped fields without the marker and unknown markers reject.

**Deadline integration correction:** `execute_development()` reduces the plan
deadline to reserve preparation time, which changes its plan ID. The adapter
validates scopes against the original declared plan, permits only a checked
deadline reduction, and records both declared/executed identities and the original
scope-file hash in `scope_deadline_binding` before final safety/sealing. It rejects
query, corpus, branch, binding or other plan drift; it does not relax identity checks.

The pre-application candidate patch remains at
`reports/workstream-c/scoped-disclosures-2026-11-07/a-activation-candidate.patch`
as an audit artifact. The applied call-site change and A-owned combined tests are
described under the activation checkpoint below. The original C checks included
the spawned runner and one synthetic final safety call; their 1,718-test full
suite predates A's activation change, and that broad suite has not been repeated.
The targeted combined runner/review/export checks pass. A separate real-user
grant is still required before any generation attempt.

Offline preparation for both development cases is available at
`reports/workstream-c/scoped-disclosures-2026-11-07/prepared-development-data/`.
Its `preparation.json` contains sidecars, exact mapper captures and six data hashes.
It is explicitly **not an execution contract or grant**. Review requested-scope
meaning, apply the candidate, validate the combined revision and freeze final
identities before requesting any generation. Existing inputs/failed runs are unchanged.

New private wire: `cq-scoped-selection-v1`.
Mapper version: `cq-mapper-v7-scoped-disclosures`.
Disclosures: `cq-scoped-disclosures-v1`.
Composition version/settings and the public Draft remain unchanged.

`DisclosureScopes` is a separately frozen sidecar, not a new public Plan/API field:

- `plan_id`, `corpus_sha256`, `question_sha256`, `bindings_sha256`.
- `declaration_ref`: traceable caller/plan declaration, never inferred owner review.
- `annotations`: exactly one per bound `(component_id, subtask_id)` pair, up to 25.
- Each annotation requires `question_span: {start, end}` or explicit `null`.
  Positions are Python Unicode code points in the full original question, start
  inclusive/end exclusive. Null produces **scope not established**, never a guess.

The bindings hash uses JSON with sorted component keys, compact separators,
Unicode preserved and declared branch order retained. `bindings_hash()` provides
the canonical implementation. Every component and every plan branch must be bound.
Malformed IDs, duplicates, omitted declarations, changed identities, invalid spans
or stale results fail before a model call. The schema proves annotation membership,
**not** that a caller supplied the right interpretation.

## Behavior and provenance

The mapper selects status and exact source span IDs. Its schema has no gap text,
question offsets, answers or quotations. Existing necessary coverage constraints
and exact source resolution remain. Unknown fields/old wires are rejected, without
repair, retries or another model call.

Application resolution supplies canonical whole-component anchors only to the
existing internal source validator. These are explicitly logged compatibility
data; they are not raw-model gap answers. The final warnings come from the scoped
branch projection, replacing only the known old generic gap/branch messages.
Geographic/period warnings, fallback disclosures and the exact no-information
message remain. Warning overflow fails; no finding is silently truncated.

| Branch outcome | Disclosure |
|---|---|
| Missing supporting retrieval | No support returned for this subtask; does not establish database absence |
| Returned support unselected | Unselected/unresolved evidence, with source inspection available |
| Failed/cancelled/blocked | Unverified execution; never classify as information absence |
| Reported conflict | Separate conflicting source statements; not generic missing information |
| Selected support | Selection only; semantic support and completeness remain unproven |
| Optional branch unresolved | Retained diagnostics; no invented required branch warning |

Warnings group branch/component findings without losing the full per-pair records.
The exact original question, requested scope, query, outcome, selected/returned
source IDs and child attempt identity remain in diagnostics. A model-declared
partial component remains partial even if all branches selected evidence; branch
selection cannot locate every missing fact within a returned passage.

Required execution failures still block drafting under A's existing policy. The
standalone projection can describe their states; it does not authorize publication.

The result is the existing safety-pending `SynthesisResult`. A's current typed
boundary already snapshots/guards/seals its draft and diagnostics. Preserve:

- `scoped_mapper_raw_selection`, raw `model_responses`, and span catalog.
- `application_source_selection` and `resolved_evidence_mapping` separately.
- `scoped_disclosures` including the full scope contract and Report identity.
- Existing `raw_composer_output`, `fallback_unit_ids` and claim provenance.
- `gap_authorship`, explicit versions, no inferred owner acceptance.

No new event name or database schema is requested. Source/claim lineage and
exact-revision approval/export remain in the existing candidate/metrics path.

## A acceptance and qualification preparation

1. Freeze the sidecar SHA with each opt-in case and include it in input integrity
   checks. Record the new wire/mapper/disclosure versions in the future contract.
2. Supply annotations from the declared request plan, not source content or the
   model's failed gap. A retrieval query is not automatically a requested fragment.
   If no precise annotation exists, record null and leave the quality gap unresolved.
3. Use the unchanged runner lease, serialized model access and one final NeMo gate.
   Scope/callback changes must not reopen a closed allowance or bypass a deadline.
4. Keep explicit contract selection: old frozen contracts use their old callback;
   new scoped contracts use this class. Review any public Plan/API change separately.
5. Check the exact combined revision with offline runner/review/export tests.
   C's synthetic tests already exercise the existing spawned runner with this callback,
   one final safety call, denial/no publication and edit-invalidated cached exports.
6. Only then freeze a new actual-generation diagnostic and obtain its own grant.
   Hold the unchanged fresh-quality criteria; do not count the consumed cases as unseen.

Evidence and final checks are recorded in
`reports/workstream-c/scoped-disclosures-2026-11-07/`. No actual-model success is
claimed. The latest cq-p02 failure and CQ1 **0/20** status remain unchanged.

## A activation and combined validation — 7 November 2026

A applied the explicit selector in `src/pilot/subtasks/qualification_runner.py`.
Contracts without `composition_contract` retain the original
`ConcurrentComposer`; `cq-scoped-composition-v1` contracts use
`prepare_composer()` and require their scope sidecar to match the frozen input
hash. Unknown markers and scope metadata without the marker fail closed. The
adapter validates all declared-plan identities and permits only the owned
runner's deadline reduction, recording both plan IDs and the sidecar hash in
the sealed diagnostics.

The focused combined offline check passed **67 tests** across activation,
scoped disclosures, qualification execution/gates, and the owned spawned runner.
The activation-path runner test additionally verifies that approval is required
for export, repeated export is byte-identical, and editing the approved revision
invalidates export. `git diff --check` passed. The checked-in C implementation
report's 1,718-test Windows suite predates A's one-file selector/test addition;
that broad suite was not repeated because the affected adapter and lifecycle
boundary are covered by the targeted set. No model calls, Ragas, Databricks,
dependency changes, publication, or deployment occurred. These offline checks
do not qualify fresh model quality or production operation.
