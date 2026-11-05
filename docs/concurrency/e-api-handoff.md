# E read-only progress API handoff

Implemented and API-validated by A. A owns `api.py`, `_identity.py`, `store.py`, `subtasks/persistence.py` and `tests/test_subtask_progress_api.py` for this pass. E owns browser assets/UI tests/docs and should not edit these shared runtime files concurrently. No generation, creation route activation, browser activation, schema/dependency change or mutation behavior is added by this handoff.

## Endpoint and snapshot

`GET /api/runs/{id}/progress` returns `{run, progress, sequence}`. It applies the same existing host/origin/token boundary as other API calls and the existing ordinary-GET role policy: reader, analyst, reviewer and operator can read it. Export permissions and every mutation permission remain unchanged. Missing run: 404; denied token/role: 403; normal responses remain `Cache-Control: no-store`.

`run` is the existing `Store.get()` representation, unchanged in shape. `Store.get()` now explicitly begins a SQLite read transaction before reading the run, events and reviews. `progress` and `sequence` are computed from that single returned snapshot; the endpoint does not reread the database, write audit events, submit work or probe models. `sequence` is the maximum durable event `seq` **for this run**, or zero without events. SQLite event numbers are global; gaps are normal.

**Polling contract:** sequence is an event watermark, not a version of every run/review field. Existing draft saves, reviews and retries do not all emit events; parent status/revision/review data can change at the same sequence. Do not discard equal-sequence snapshots as identical. Keep one poll in flight, capture selection/request generation locally, and ignore responses after selection changes or superseded requests. Compare run ID, attempt ID, plan ID, parent status and revision when updating the view. A decreasing sequence indicates stale/event-history inconsistency, not permission to roll UI state back. Attempt IDs are opaque; never lexically sort them. Do not implement a second event reducer in JavaScript.

## Projection fields

`progress_view(row, detailed=True)` is A's common projection. Its legacy default return shape remains compatible.

| Field | Meaning |
|---|---|
| `availability` | `available`, `no_plan`, or `unavailable`. |
| `mode` | `subtasks`, `sequential` for no observed latest-attempt plan, or `unavailable`. No-plan does not promise that a plan cannot be registered later. |
| `run_id`, `attempt_id`, `plan_id`, `corpus_sha256` | Parent and latest-attempt identities. IDs may be null for no plan/no attempt; unavailable projections deliberately do not assert unverified attempt/plan IDs. |
| `parent_status` | The actual stored run status; branch completion never overrides it. |
| `attempt_current` | False for queued retry awaiting a new claim, or no attempt. Completed/failed/interrupted attempts can remain the latest retained history. It does not mean a worker is alive. |
| `phase` | Stored parent status when not running. For an available running plan: `retrieval`, `awaiting_composition`, `composition`, or `safety`, derived from validated branch states and existing stage markers. No-plan uses parent status; malformed projection uses `unavailable`. |
| `plan` | Null without a validated plan; otherwise plan ID, version, retrieval/model concurrency, deadline, main-call ceiling and subtask count. No arbitrary source content or subtask query is required to render progress. |
| `branches` | Stable declared plan order. Each contains `subtask_id`, `operation`, `required`, `depends_on`, `status`, `reason`, `derived`, `child_attempt_id`, `outcome`. |
| `reason` | Top level: `none`, `no_subtask_plan`, `invalid_progress_records`. Branch reasons use A's existing safe enum only. Raw projection exception text is not returned. |

Branch statuses: `queued`, `waiting_on_dependency`, `running`, `completed`, `failed`, `cancelled`, `blocked`. `derived=true` labels missing initial queued records or an interruption overlay after parent termination. `outcome` is null until a completed child's validated result is present, then `evidence`, `missing` or `conflicting`. An outcome validates envelope identity/provenance, not factual support. Missing evidence is not technical failure. No completion percentage is supplied.

`availability=unavailable` preserves the separately returned authorized run snapshot but returns no asserted branch plan/state. A missing/malformed plan, wrong parent/corpus/child identity, invalid transitions, ordinals or result/dependency provenance cannot masquerade as a sequential run. Historical attempts do not leak into the latest attempt. A queued retry may still display the latest retained history, with `attempt_current=false` and phase `queued`; once claimed, an unregistered new attempt has no inherited branches.

Do not infer final brief readiness from completed retrieval. Only parent `needs_review` means a saved draft awaits review; `approved` still refers to that exact stored revision. E must preserve current source inspection, approval/edit/export controls and empty-claim restrictions.

## Validation scope

`tests/test_subtask_progress_api.py` covers all GET roles, missing/denied requests, no mutation/generation, no plan versus unavailable data, outcomes/phases, retry isolation, derived interruption, and a controlled WAL writer committing between row/event reads to prove one consistent read snapshot. Existing persistence/identity/execution tests are included in the targeted run. Browser behavior is E's separate verification; none is claimed here.

Final API snapshot: `947beafe1b9b4b3a84498d67b7320e561bd7aeb28937096471781a7693baf66f` (234 selected files). Local offline source-overlay image: `sha256:c89544a213454875a165e14bfbedd2b6aa0f8b91ccccdd269bc704eecc131b83`. Dependencies came from the unchanged cached base; no clean-install or remote-CI claim.

| Check | Result |
|---|---|
| Endpoint-specific final suite | 16 passed |
| Identity/persistence/execution targeted pass before final phase hardening | 43 passed |
| Full Windows suite on final API snapshot | 1,456 passed; zero failures/deselections; 15 warnings; 415.08 seconds |
| Full Linux suite on same snapshot | 1,455 passed; one Windows-only skip; zero failures/deselections; 15 warnings; 87.86 seconds |
| Source preservation | Five API-owned implementation/test files match the tested snapshot; dependency constraints unchanged. Store/API baseline changes are explicitly requested, not undeclared drift. |
| Diff whitespace | `git diff --check` passed; only Git line-ending conversion warnings. |

Logs/manifests are local under `.pilot-work/subtasks-a/`: `e-api-snapshot-identity.json`, `e-api-preservation.json`, `full-windows-e-api.txt`, `full-windows-e-api-process.json`, `linux-e-api/result.json` and `linux-e-api/linux-pytest.txt`. Both A-owned suite processes are terminal. The full suite includes the projection/API tests; no model or live external service calls were made.

**E's later UI integration is not covered by this snapshot.** E has reported landing only its browser files/tests after the freeze. A left those files untouched. E should finish its combined UI/API offline checks against that newer checkout, using this exact route/field contract. Do not relabel these snapshot counts as validation of the newer UI revision. No human source adjudication is needed for these fixed-response API tests.
