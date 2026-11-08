# E/D real-app synthetic lifecycle fixture — SERVER READY

Date: 6 November 2026. A's [workflow API handoff](e-workflow-api-handoff.md) governs creation, capability, identity and queue behavior. D's fixture uses that real API, real SQLite and the real owned-process runner. It does not substitute browser routes or fabricate progress snapshots. All source records and callback responses are synthetic. Actual model/provider/Ragas/NeMo calls are **zero**.

## Ownership and files

D owns only:

- tests/integration/subtasks/e_browser_fixture.py
- tests/integration/subtasks/test_e_workflow_lifecycle.py
- tests/fixtures/workers/e_lifecycle_worker.py
- this handoff

A owns API/runtime/store/schema and executor integration. E owns index.html/Playwright/UI tests. D's isolated branch is codex/d-e-lifecycle at .pilot-work/e-d-lifecycle/checkout. D-owned files are also copied deliberately to the integration checkout so E can launch the server against A's current code. Do not overwrite A/E changes with the older worktree source.

## Startup and token

Run from the repository root, selecting a fresh ignored directory and a free localhost port:

```powershell
$env:AMI_E_FIXTURE_ROOT = (Join-Path (Get-Location) '.pilot-work/e-browser-local')
.\.venv-release-check\Scripts\python.exe -m uvicorn e_browser_fixture:create_fixture_app --app-dir tests/integration/subtasks --factory --host 127.0.0.1 --port 8769
```

Use the existing environment; install/upgrade nothing. Stop that owned server with normal termination after testing. No production service is launched or upgraded. Use a dedicated synthetic directory; the fixture refuses mismatched corpus bytes and unmarked pre-existing synthetic.sqlite3 files. It refuses AMI_PILOT_IDENTITY_FILE rather than loading actual reviewer identities.

The directory contains synthetic-corpus.json, synthetic.sqlite3, fixture-kind.txt, controls/ and session.json. The latter holds the current random supervised-bootstrap token as `{token, synthetic_only:true, actual_provider_calls:0}`. Read it only from this local test directory, never print unrelated environment/credential files. Wait for `/health` to respond before browser use. The real home page injects that same session token into the normal bootstrap UI. On each restart a fresh token is written; reconnect/refresh must use the new session.

Factory arguments for pytest: `create_fixture_app(tmp_path)`. The normal production create_app has **no** fixture control routes. The fixture explicitly supplies OwnedSubtaskExecutor with fixed Operation/Composer/Safety, then replaces only the real dispatcher's sequential worker callback with a fixed IPC worker. This makes an accidental default sequential submission safe and synthetic; the default UI workflow still remains sequential.

## Real workflow routes

Use A's routes without modifications:

- GET /api/session: bounded_subtasks capability true; its mode is owned_runner because the real owned runner executes fixed callbacks.
- POST /api/runs: normal sequential route, fixed synthetic worker here.
- POST /api/runs/subtasks: explicit client plan, as documented by A. Use 180.0-second branch timeout in browser test payloads if pauses at gates might exceed the normal 30-second default. Overall deadline remains at most 180 seconds.
- GET /api/runs/by-request/{key}: real lookup, no duplicate POST on refresh.
- GET /api/runs/{id}/progress, /api/runs/{id}, /api/runs: real stored state.
- Existing cancel/retry/draft/review/export routes keep their real validation and permissions.

Every API/control call needs `X-Pilot-Token` with the current fixture session token. Same host/origin rules apply. Synthetic source IDs fiction-1 through fiction-5 resolve to the prepared corpus; source pages are zero-based 0 / 6 for UI/export PDF pages 1 / 7. All facts are fictional district observations, not financial evidence. Plans may use s01–s05 and dependencies; fixed operations select the matching numbered source. No retrieval-algorithm quality is claimed.

## Test-only control protocol

These routes exist only in this fixture app. They neither create runs nor write production progress events.

`GET /__fixture/runs/{run_id}` returns:

```json
{"attempt_id":"<latest attempt or null>","entered":["s01","s02"],"released":[]}
```

`POST /__fixture/runs/{run_id}/release` body:

```json
{"stage":"s01","fail":false}
```

Allowed stages: s01–s05, composition, safety. `fail` defaults false. Unknown stages/extra fields return 422; missing token 403; no current running attempt 409. To force a branch failure, release that branch with `fail:true`. To force fixed composition/safety failure, use the corresponding stage. Control responses are synchronization diagnostics; assertions about displayed state must use the real progress endpoint. Worker entry can precede parent persistence of its queued event, so wait for the durable phase/state too.

Each gate is scoped to run ID **and latest attempt ID**. A retry cannot inherit old releases/failures. The runner's real attempt/corpus/approval fences remain active. Gates are released explicitly; no elapsed-time assertion is used. Watchdog timeouts only fail a hung test.

Suggested happy path:

1. Submit a two-branch explicit plan through the browser. Confirm both branch entries and real running states.
2. Release s02 then s01; for a larger plan release each configured branch, respecting observed dependencies as needed.
3. Wait for composition entry and its durable composition phase. All retrieval branches can be completed while the parent is still running, with no draft/export.
4. Release composition. Wait for safety entry and durable safety phase; draft still unavailable.
5. Release safety. Wait for parent needs_review, inspect source records, edit/review/approve/export through normal UI.

`model_calls=1` / `guardrail_invocations=1` count the fixed callbacks through real stage instrumentation, **not actual inference**. Fixed sequential worker reports zero. No semantic safety qualification is implied.

## Failure, cancellation and restart

- Fail s01, observe real failed parent and blocked/cancelled work, no draft/export. Explicit retry uses the persisted plan, fresh parent/child identities and fresh gates.
- Cancel a running or queued task through the real cancel route. Wait for stored interruption and owned-child cleanup; never release an old gate expecting it to revive work. Retry only by explicit user action.
- Stop the owned uvicorn server normally while a branch is blocked, then restart the same command/root. The real runtime shuts down/reaps owned work and recovers unfinished history. Refresh/reconnect with the new token; no automatic retry. Use the normal Retry control to create a new attempt.
- Previously approved exports must remain byte-identical after restart. Editing creates a new unapproved revision; old decisions and current export are blocked until that exact revision is approved.
- Abrupt OS termination/owner-death is covered by earlier D process tests, not newly claimed by these clean lifespan restart checks. Reaping a client does not establish inference-server cancellation.

## Verification and remaining work

`.pilot-work/e-d-lifecycle/http-full.txt`: **4 passed**, one existing FastAPI/Starlette deprecation warning, 33.38 seconds. Covers authenticated test controls/attempt isolation; real HTTP bounded creation + simultaneous duplicate POST; workflow/plan conflicts + request lookup; actual owned runner stages; current-revision review/edit/approval/export and cached bytes after restart; required failure/retry/cancel/restart. The programmatic runner test also checks a dependent branch and both transaction lifecycle decisions through the real review API.

Active-shutdown/restart test also passed: server-ready.txt records **5 passed**, one existing warning, 33.40 seconds. It closes the real app lifespan with a blocked branch, verifies interrupted/draftless recovery without automatic retry, then explicitly retries with fresh identities. Final focused run is terminal and passed: **28 tests**, one existing FastAPI/Starlette warning, 68.67 seconds. It includes all six D lifecycle tests plus A creation/progress API tests; log final-targeted.txt. The sixth D check confirms the default sequential request executes the fixed IPC worker with zero model-call count and no subtask plan. E still owns real browser/selection/reconnect/refresh/download acceptance and the combined final offline suite. D's focused passes are not a combined-release, model-quality, human-usefulness or production qualification claim. No generation, dependency changes, commits, pushes, deployment or reviewer contact.


## Localhost startup smoke and handoff status

The documented uvicorn factory command was exercised through a real localhost TCP connection using a temporary free port. `/health`, authenticated `/api/session` and denial of unauthenticated fixture controls passed. The owned server was terminated/reaped afterward. Evidence: `.pilot-work/e-d-lifecycle/server-smoke/result.json` and server.txt. This is a startup/HTTP smoke, not E's browser acceptance.

**D status: fixture and six lifecycle tests ready for E integration.** E must still complete its browser-driven UI/selection/refresh/lost-response/download checks and freeze/run the combined release suite. No final combined Windows/Linux release count is claimed by D for these newer A/E changes. Source identities captured after the focused pass are recorded as post-run observations, not a before/after frozen-source proof. All four dependency/constraint manifests match D's baseline.
