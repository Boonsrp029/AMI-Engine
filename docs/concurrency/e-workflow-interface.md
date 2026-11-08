# E — opt-in workflow interface

This extends the earlier read-only progress interface. The sequential workflow remains selected by default. The new browser selector requires an explicit server capability and explicit reviewer selection; enabling the progress panel alone never submits bounded work.

## Implementation passes and ownership

| Pass | Current behavior | Change | Evidence required |
|---|---|---|---|
| Selection/admission | Browser submits only sequential requests | Capability-gated bounded selection; synchronous submit lock | Fixed HTTP browser checks prove default, selection, unavailable capability and duplicate-click fencing |
| Confirmation recovery | Request identity exists only in page memory | Persist only opaque request identity/workflow in tab storage; reconcile through authenticated lookup | Lost-before/lost-after admission, reconnect and refresh; no automatic POST on load |
| Truthful progress | Persisted snapshot drives parent and branch states | Also expose technically completed searches with missing/conflicting evidence; disable actions on older snapshots | All state families, partial consequences, equal/lower watermarks and local-edit preservation |
| Complete lifecycle | Read-only browser fixtures plus separate API checks | Browser exercises real API/SQLite, deterministic scheduler callbacks and exact-revision review/export | Request → branches → composition → safety → review → export; failure/retry/cancel/reconnect |

E owns `src/pilot/index.html`, `tests/browser/progress-interface.cjs`, `tests/browser/workflow-submission.cjs`, the real-fixture browser lifecycle test, and this document. A owns API/runtime/store, capability, request-key lookup and workflow-bound idempotency. D owns the real application fixture and cross-component lifecycle tests. The additive contract is a dependency, not permission for E to change shared APIs concurrently.

Changes are developed in `codex/e-workflow-selection` under the ignored local work directory. Only E-owned files are integrated after checking their baseline fingerprints. Dependencies, model settings, source corpus, historical outputs, owner judgments and cached approved exports are unchanged.

## Display contract

- Parent status is authoritative. Completed retrieval means neither draft readiness nor approval. Composition and safety remain separate, followed by `needs_review`; only exact-revision `approved` enables export.
- Branches show queued, waiting-on-dependency, running, completed, failed, cancelled or blocked, their required/optional nature, dependencies and safe reasons. Derived interruption is labeled.
- Counts use the currently persisted plan: “N of M subtasks completed.” There is no percentage, estimated time or implicit estimate of work remaining. A different attempt/plan replaces this denominator; it is never accumulated across retries.
- Missing evidence is a completed operation with an evidentiary limitation, not a technical failure. Conflicting evidence requires inspection. Required failures and optional incomplete coverage have different consequences.
- Reviewers retain original source inspection, PDF page labels, revision/audit history, local edits, support confirmation and exact-revision review/export. Empty-claim drafts cannot be approved/exported.

## Recovery contract

The browser consumes A's projection rather than reducing raw events again. One poll is in flight. Selection/request epochs fence late responses; lower event watermarks cannot replace current state or enable actions. Equal watermarks may contain a newer revision or review and are applied. Dirty revision/attempt conflicts require explicit reload; edits are retained until then.

URL state contains only selected run and display preference. Tab storage contains only pending opaque request key and selected workflow, never prompts, credentials, source text or draft contents. Refresh/reconnect performs authenticated lookup, never an automatic submit. A lost response keeps the same key. If no run exists, explicit resubmission uses the same key/body; after refresh the original question must be re-entered because it was not persisted. Server idempotency must bind query and workflow. Unreadable pending identity blocks new creation rather than silently generating a replacement key.

Authentication loss stops polling and disables mutations/export. Network failure preserves the last visible view and edits but marks them stale; bounded backoff follows. The selected run is reloaded from persisted state. A reconnect does not retry work; explicit retry retains attempt history.

## Acceptance and evidence boundaries

Fixed HTTP browser tests establish frontend contracts, not real persistence. The real API/SQLite fixture must separately prove the complete browser lifecycle using fixed callbacks and controlled gates. No real model, NeMo or hosted inference is needed. Offline tests do not establish semantic quality, independent reviewer usefulness, production readiness or target deployment.

Human source review remains necessary for real generated drafts and approval applies only to the exact revision inspected. No manual factual scoring is required for synthetic fixtures. Publication, deployment, actual inference and external reviewer sessions remain separate authorization scopes.

Status: the scoped E engineering Goal is complete. E-owned changes are integrated after the baseline UI fingerprint check. All 33 final browser scenarios pass: 16 persisted-progress frontend checks, seven fixed-HTTP submission/recovery checks and ten real API/SQLite/owned-runner lifecycle checks using fixed callbacks. The last group includes actual authentication failure/reconnect and a genuinely admitted POST whose response is dropped, followed by real request-key lookup after refresh without another submission. Confirmation of a new request also requires explicit consent before discarding current review edits. A's SQLite lookup and default-constructor compatibility fixes are included.

The final combined Windows offline suite terminated successfully: **1,499 passed, 14 existing warnings, 460.62 seconds**, zero failures/skips/deselections. The 216-file source/test/config snapshot has no changed, added or deleted files after validation. All four dependency/constraint manifests have no Git diff, and `git diff --check` passes. Results and snapshot identity are in [structured verification](e-workflow-verification.json). Local detailed logs, synthetic database, screenshot and source hashes are under `.pilot-work/workstream-e/lifecycle-2026-11-06/`. No current Linux, remote-CI, real-inference or production qualification is inferred from this Windows result.

The first combined run is retained as **1,498 passed / one failed**. It caught the default runtime factory receiving an unnecessary new keyword argument while bounded execution was disabled. A preserved the original three-argument default call; the existing regression test was retained. This failed run remains historical evidence and is superseded only by the explicit final result, not relabeled as a success.

| E acceptance gate | Final evidence |
|---|---|
| Sequential default / explicit bounded selection | Real default sequential route; capability-gated manual bounded plan; disabled capability tests |
| Truthful parent/branch states | Persisted dependency/running/queued/completed/failure/cancellation; separate composition/safety/review/approval; missing/conflicting evidence consequences |
| Refresh / reconnect / no duplicate creation | Actual admitted POST response loss → real lookup → refresh; no extra POST/run; actual 403 → reconnect; cached approved bytes retained |
| Local edits / stale state | Dirty edits and review inputs retained; late selection and lower/equal watermark checks; revision conflict requires explicit reload; new request confirmation cannot silently discard current review edits |
| Source / exact revision lifecycle | Source inspection and PDF pages 1/7; approve/export; edit invalidates; stale review/export rejected; reject then fresh approval; cached export byte equality |
| Scope limits | Fixed synthetic facts/callbacks only; no actual model/provider/NeMo/Ragas/Databricks calls, owner judgments, independent reviewer sessions, publication or external deployment |

## Run the synthetic checks

Use the existing bundled Node Playwright installation and Edge. No dependency install is required:

```powershell
$env:NODE_PATH='<existing Node modules containing playwright>'
node tests/browser/progress-interface.cjs
node tests/browser/workflow-submission.cjs
```

For the real HTTP/SQLite lifecycle, first start D's [isolated synthetic fixture](e-d-lifecycle-handoff.md). It supplies fixed callbacks and must never be substituted for production safety. In another terminal, use the same synthetic directory and localhost URL:

```powershell
$env:AMI_E_FIXTURE_ROOT='<absolute isolated synthetic directory>'
$env:AMI_E_BASE_URL='http://127.0.0.1:<fixture-port>'
node tests/browser/workflow-lifecycle.cjs
```

The lifecycle test refuses an unmarked fixture directory/non-localhost URL, reads only that fixture's synthetic bootstrap token and cancels remaining synthetic active work during cleanup. It exercises actual routes and stored states, not mocked progress projections. Controlled callbacks do not establish inference cancellation, model quality or backend performance. Stop the owned fixture server after testing.

Cancellation preserves the existing storage contract: the parent becomes `interrupted` with an explicit cancellation reason; its affected branches display `cancelled`. Do not rewrite persisted history merely to change a presentation label.
