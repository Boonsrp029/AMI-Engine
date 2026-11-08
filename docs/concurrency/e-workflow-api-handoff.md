# E workflow selection and API/runtime handoff

Status: additive opt-in API contract for E's browser workflow selector. The
existing sequential route remains the default. Production inference is not
enabled by the default app configuration and was not run for this integration.

## Workflow identifiers and session capability

`GET /api/session` keeps its existing fields and adds:

```json
{
  "capabilities": {"sequential": true, "bounded_subtasks": false},
  "workflow_modes": {
    "sequential": "sequential",
    "bounded_subtasks": "disabled"
  }
}
```

`capabilities.bounded_subtasks` is true only when an executor was explicitly
configured. `workflow_modes.bounded_subtasks` is `disabled`, `owned_runner`, or
`synthetic_test`. E should only offer the workflow if the boolean is true; the
mode is diagnostic. The ordinary `create_app()` factory has no executor and
therefore returns `false`/`disabled`. In a production configuration, the app
accepts only `OwnedSubtaskExecutor`, whose implementation calls the persisted,
owned-process `run_stored_plan()` path. A custom executor is accepted only with
an injected test engine/run-inline mode and is labeled `synthetic_test`.

Workflow identifiers are fixed strings: `sequential` and `bounded_subtasks`.
The existing `POST /api/runs` remains sequential and its `{id, created}` response
is unchanged. Do not infer concurrent mode from a run's status or from the
presence of branch-shaped UI state.

## Submit and idempotency contract

`POST /api/runs/subtasks` is analyst/operator-only under configured principal
tokens. It returns 409 if the capability is disabled. Request:

```json
{
  "query": "Compare the requested market measures",
  "request_key": "opaque-client-generated-key",
  "subtasks": [
    {"subtask_id": "s01", "operation": "retrieve", "query": "exports growth"},
    {"subtask_id": "s02", "operation": "retrieve", "query": "sector contribution"}
  ],
  "retrieval_concurrency": 2,
  "deadline_seconds": 180
}
```

`subtasks` is explicit client/app policy, not an LLM output. The server validates
it with the current `Plan`/`Subtask` schema, assigns the current corpus SHA-256,
and rejects malformed DAGs, unsupported operations, extra fields, too many
branches or invalid limits. `request_key` uses the existing
`[A-Za-z0-9_-]`-compatible 8–100 character contract. The same key is bound in
one SQLite write transaction to request text, corpus identity, workflow ID and
canonical plan ID before the new run is visible to the queue.

Each branch accepts only these fields (unknown fields are rejected):

| Field | Accepted values / default |
|---|---|
| `subtask_id` | Required ordered IDs `s01` through `s05`; no gaps. |
| `operation` | Required: `retrieve` or `inspect_sources`. |
| `query` | For `retrieve`, required nonblank text up to 500 chars; forbidden for `inspect_sources`. |
| `source_ids` | For `inspect_sources`, 1–5 source IDs; default empty; forbidden for `retrieve`. |
| `dependencies` | 0–4 declared branch IDs, default empty; unknown IDs and cycles rejected. Inspect branches must depend on retrieval branches that return their requested IDs. |
| `required` | Boolean, default true. |
| `timeout_seconds` | Positive and at most 180, default 30. |

Plan-level `retrieval_concurrency` is 1 or 2 (default 2),
`deadline_seconds` is positive and at most 180 (default 180), model concurrency
is fixed at 1, and main calls are capped at 4 by the current contract. Use a
single retrieval branch for a single-source task; branch decomposition is
submitted explicitly and is not inferred by the server.

Response:

```json
{"id": "<run-id>", "created": true, "workflow": "bounded_subtasks"}
```

An exact replay returns the same ID, `created:false`, and does not enqueue work a
second time. Reusing a key with different text, corpus, workflow or plan returns
409. The existing sequential route also returns 409 if its key belongs to a
bounded-subtask run. SQLite's unique request-key constraint plus the atomic
submission event closes concurrent and late-original POST races; a client may
repeat the exact same body/key safely.

The immutable `subtask_submission` event stores the validated plan before the
dispatcher can claim it. Each execution attempt then registers its own
attempt-bound `subtask_plan` and progress/results through A's existing fenced
event adapter. Retry reuses the immutable submitted plan, creates fresh attempt
and child identities, and never auto-resumes an interrupted attempt.

## Lost response / reconnect lookup

`GET /api/runs/by-request/{request_key}` is analyst/operator-only with configured
principal tokens. E must URL-encode the key. It returns no prompt or source data:

```json
{"id": "<run-id>", "workflow": "bounded_subtasks"}
```

The workflow is either `sequential` or `bounded_subtasks`; absent keys return
404. This read-only lookup works whether the initial POST is sequential or
bounded-subtask. If a duplicate exact POST races the original before either
response reaches the browser, atomic Store idempotency still yields one parent
run.

E stores only `{request_key, workflow}` in `sessionStorage` while awaiting the
POST result. On refresh/reconnect, lookup first. A found row reconnects by ID;
it must never trigger a new POST automatically. If absent, let the user re-enter
the request and retry the exact key/body; never silently rotate to a new key.
While confirmation is pending, freeze that workflow/key pair. A deliberate
same-page retry may repeat the identical body/key only.

## Progress, cancellation, retry and review lifecycle

- Continue polling `GET /api/runs/{id}/progress`; its `{run, progress, sequence}`
  shape is unchanged. A just-created subtask run exposes the validated plan and
  derived queued branches before the first attempt has started. Completed branch
  retrieval is not a completed brief or a human approval.
- Use the existing `POST /api/runs/{id}/cancel`. A subtask attempt is fenced in
  SQLite; the owned runner observes the fence and stops/reaps its child. A
  queued request can be canceled before an attempt exists.
- Use the existing `POST /api/runs/{id}/retry` only after failed/interrupted
  status. It reuses the persisted bounded plan. If bounded-subtask execution is
  disabled after restart, the endpoint returns 409 without changing task state.
- Source inspection, exact-revision edit/review, nonempty-claim approval and
  export keep their current routes and Store checks. A sequential run can never
  be relabeled as a bounded-subtask run, and an empty-claim abstention remains
  unapprovable/unexportable.

## Ownership and validation boundary

A owns `src/pilot/api.py`, `src/pilot/_identity.py`, `src/pilot/_runtime.py`,
`src/pilot/store.py`, `src/pilot/schemas.py`,
`src/pilot/subtasks/api_runtime.py`, `src/pilot/subtasks/runner.py`, and the
additive `src/pilot/subtasks/persistence.py` projection change. B owns the local
BM25 adapter; C owns corpus-bound synthesis; D owns cross-component request to
review/export lifecycle tests; E owns `src/pilot/index.html`, browser tests and
UI documentation. No B/C file is edited by A here.

Production construction must explicitly pass an `OwnedSubtaskExecutor` with
spawn-pickleable read-only operation, composition and safety callbacks. That
executor enters the existing `ProcessRuntime` queue and dispatches to
`run_stored_plan` while reusing the already-held database runtime lease. It does
not call the sequential `PilotEngine.run()` path. Test-only custom executors
must be injected with the test engine/run-inline mode and are visibly labeled
`synthetic_test`. The default session capability is disabled.

A-owned tests should cover schema/route capability gating, idempotency and
cross-workflow conflict, lookup authorization/404, plan visibility before an
attempt, queue dispatch and disabled-mode retry. D owns the real fixed-response
owned-runner path through composition, safety, review/edit/approval/export and
cached export checks. These checks prove workflow wiring, not model quality.
No generation, Ragas, Databricks, publication, deployment or reviewer contact
is included.

## A-owned verification checkpoint (6 November 2026)

The current focused API/runtime boundary check passes **38 tests**:

```powershell
.venv-release-check\Scripts\python.exe -m pytest -q tests/test_subtask_workflow_api.py tests/test_pilot_identity.py tests/test_subtask_progress_api.py tests/test_subtask_persistence.py --basetemp .pytest-tmp/a-workflow-api-final-targeted-4
```

The run includes the additive submission/lookup API, identity boundaries,
progress projection, and persistence. It found and fixed one lookup defect:
`workflow_for_request()` now selects the SQLite `kind` column as well as
`payload`, which its persisted-event classification requires. Result after fix:
38 passed, with one existing Starlette/httpx deprecation warning (36.11 sec).
This is focused offline evidence, not the broad integrated suite, actual model
quality, or production qualification. D/E cross-component validation remains
owned by their workstreams; avoid starting a second broad suite while those
checks are in progress.

The integrated offline run recorded by E against its earlier frozen snapshot
finished with **1 failed, 1,498 passed**. The sole failure was the existing
`test_http_factory_uses_process_runtime_and_authenticated_cancellation` test:
its `ProcessRuntime` test double preserves the original three-positional-
argument constructor. `create_app()` had passed the additive
`subtask_executor=None` keyword even with the feature disabled. A now calls the
original three-argument constructor on that default path and supplies the new
keyword only when an executor is explicitly enabled. Targeted regression check
after the fix passed **7 tests** (the runtime compatibility test plus the
subtask-workflow API file), with one existing Starlette/httpx deprecation
warning. At that checkpoint E had made an additional UI-owned edit, so that
earlier combined run was not a terminal result for the latest shared checkout.
No model-quality or production-readiness inference follows from either test
result.

### Integrated verification update

E has since frozen the integrated A/B/C/D/E checkout and rerun the complete
Windows offline suite. The final recorded result is **1,499 passed, 0 failed,
0 skipped**, 14 warnings, 460.62 seconds; all **33 synthetic browser/API
scenarios** passed. The final snapshot fingerprints 216 source/test/config
files, with no post-run changes. Its SHA-256 is recorded in
`docs/concurrency/e-workflow-verification.json` and its run log is
`.pilot-work/workstream-e/lifecycle-2026-11-06/full-offline-final.txt`.
Dependency manifests have no Git diff, and `git diff --check` passed. This
supersedes the earlier statement that integrated validation was pending. Linux
container validation, actual inference/model quality, owner review of real
drafts, independent reviewer usefulness and production qualification remain
unproven. No publication or deployment occurred.
