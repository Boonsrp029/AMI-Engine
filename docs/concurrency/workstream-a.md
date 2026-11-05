# Bounded subtask orchestration: usage and acceptance evidence

Workstream A adds a private, opt-in programmatic path for independent read-only branches within **one** analyst request. The sequential browser workflow, `query_agent()`, `PilotEngine.run()`, public request/draft schemas, SQLite schema and dependency constraints retain their existing behavior. This is an engineering milestone, not model-quality or production qualification.

The shared [ami-subtasks-v1 contract](contract-v1.md) defines the interface for B–F. A caller provides an explicit validated plan; there is no model-based planner. Default retrieval concurrency is two (configurable to one), local model access remains serialized, and concurrent complete analyst requests are outside this scope.

## Integration interfaces and ownership

| Owner | Owned implementation / integration interface |
|---|---|
| A | `contracts.py`, `scheduler.py`, `persistence.py`, `_handoff.py`, `runner.py` under `src/pilot/subtasks`; integration owner for existing runtime/store/API changes if later required. No existing shared runtime file needed modification for this milestone. |
| B | Trusted read-only `operation(context) -> Result` adapter. Validate source membership against the pinned corpus, preserve original ranking and exact text, use `context.dependency_refs` and return the launched identities. |
| C | Trusted `compose(report, model_access) -> dict or SynthesisResult` and `safety(draft, sources) -> bool`. Every actual main-model request must pass through `model_access.main()`. Returning an unguarded C `SynthesisResult` opts into validated lineage persistence; a plain Draft retains the legacy behavior. |
| D | Cross-component integration tests under `tests/integration/subtasks`; A owns module-level tests. Disposable process-control primitives must not be reused after killing their owner. |
| E | Consume `progress_view(store.get(run_id))`. It projects only the latest parent attempt and labels derived interruption states. API/UI activation needs a separate integration change. Branch completion is not brief readiness or approval. |
| F | Package the integrated revision and its source hashes. Preserve the sequential default, persistent store and exact cached exports. A local source-overlay image does not establish a clean dependency installation or remote CI. |

Callbacks are trusted application code, not a sandbox. Retrieval adapters must not invoke models, write SQLite or bypass the pinned corpus. Source text cannot authorize new operations. Model-access accounting cannot constrain arbitrary Python that deliberately bypasses the supplied interface. Concrete live adapters and target-backend cancellation require separate verification.

## Programmatic use

Create the parent with the existing `Store.create(ResearchRequest(...), corpus_sha)` API. Construct `Plan(query=request.query, corpus_sha256=corpus_sha, subtasks=(...))`, using ordered IDs `s01` through `s05`. Dependencies refer to declared IDs and may point forward; cycles are rejected. Call:

```python
from src.pilot.subtasks.runner import run_stored_plan

if __name__ == '__main__':
    run_stored_plan(
        store, run_id, plan, corpus_path,
        operation=read_only_operation,
        compose=compose_with_validated_evidence,
        safety=check_final_draft,
    )
```

The example is an integration outline, not an executable model command. Supply importable, spawn-pickleable callbacks; do not define them inside this main guard. The operation receives immutable validated inputs, declared dependency results, child identity, deadline and cancellation context. Return `Result` with the same identities and dependency references. `tests/test_subtask_runner.py` contains complete synthetic callbacks and a runnable offline end-to-end example.

The stored runner claims the queued parent under the existing runtime lease. Independent branches overlap in one owned process; dependent branches wait for accepted results. Only the coordinator emits progress/results, and only the parent writes SQLite. Required technical failure stops composition; optional technical failure produces explicit missing-branch warnings. Valid missing/conflicting evidence remains a completed evidence outcome, not a technical error.

Results aggregate in plan order then adapter rank; exact duplicates preserve all branch origins, while identity collisions fail. No evidence is silently truncated. Nonempty drafts pass the supplied final safety check. A draft is saved only after clean worker exit, current-attempt checks and corpus verification. Approval/export still requires human approval of the exact stored revision through the existing lifecycle. A draft with empty claims cannot be approved/exported.

Cancellation and deadlines fence late results. The owned child is stopped and reaped; an external inference/retrieval service might still be computing. Direct `scheduler.run_plan()` uses cooperative threads and must not be used as a hard backend-termination boundary. Restart retains history and requires explicit retry with a fresh attempt; no mid-branch recovery or automatic retry is provided.

## Acceptance checks

| Requirement | Evidence / test location |
|---|---|
| Independent work overlaps; cap one/two enforced; dependencies wait | Barrier/event-driven tests in `tests/test_subtask_scheduler.py` and D execution/owned-runner integration tests. No sleep-based latency claim. |
| Stable order, source origins and collision rejection | Scheduler aggregation tests and C synthesis integration tests; different completion orders do not change plan/rank order. |
| Required/optional failure and missing evidence remain distinct | Contract, scheduler, persistence and owned-runner tests. |
| Parent/branch deadlines and late-result fencing | Controlled-clock scheduler tests; cancellation/deadline spawned-worker tests; D recovery integration. |
| Duplicate submissions/events and fresh retries preserve history | Existing Store idempotency, atomic AttemptSink tests and D concurrent event-redelivery tests. |
| Model access serialized and bounded | Fixed callbacks exercise four main calls, one guard invocation and attempted-call persistence; zero real model calls. |
| Safety and exact-revision approval/export preserved | Real temporary SQLite, safety rejection, review/edit races, stale revision rejection and cached export byte checks. Synthetic review decisions are not owner acceptance. |
| Sequential APIs and dependencies preserved | Baseline hashes cover nine existing engine/store/runtime/API/schema/requirements files; whole offline suite checks integrated behavior. |

The frozen scheduler baseline passed **1,400 Windows tests** and **1,399 Linux tests plus one Windows-only skip**, with no deselections. Source context: `847e48815008355db2bcbb8ef46689ab3015dc69b32b0b39868c23a4898c6068`; local source-overlay image: `sha256:73313f4abd100257812195150fd5979630df9b1d84d14527c6710d49d807dd99`. Linux networking was disabled; reviewer databases and credentials were not mounted. This is cached-base source-overlay evidence, not a clean dependency installation or remote CI.

D's subsequently added four review/export transaction-order tests passed separately on Windows and Linux. An initial test-fixture defect and the canceled-process Event cleanup hang are retained in earlier logs; the final baseline includes D's repaired cancellation test. `pip check` found no broken requirements, nine monitored existing runtime/API/schema/dependency files retained their hashes, and `git diff --check` passed.

The C-to-A lineage handoff is implemented and verified through the real spawned runner. Typed callbacks retain claim/evidence-unit provenance, raw/fallback diagnostics and source/child identities. Legacy dictionary callbacks remain supported. The parent verifies exact-content fingerprints and records an explicitly unapproved candidate before attempt-fenced revision publication. Final safety is invoked once; mutation/rejection/stale-attempt checks prevent publication. Empty claims retain the zero-guard/no-approval policy.

The integrated snapshot passed **1,440 Windows tests** and **1,439 Linux tests plus one Windows-only skip**, with no failures or deselections. `pip check` found no broken requirements; the nine monitored sequential runtime/API/schema/dependency files retain their baseline hashes. `git diff --check` passes. These are offline structural/lifecycle results, not fresh generation or production qualification.

See the requirement-by-requirement [completion audit](completion-audit-a.md) and [integration record](a-c-integration-pass.md). Final context: `3ebb6b5a9fa7e2e5312821b893261e5d04abf9516da8c5b89b2c6d15b9d8defb`; source-overlay image: `sha256:0fa37873fc04ea7b7b45ff31af59db50b41fc4236c07611ab2d925019b3a5c48`. Final logs/manifests are under `.pilot-work/subtasks-a/`: `full-windows-v6.txt`, `full-windows-v6-process.json`, `linux-v6/result.json`, `linux-v6/linux-pytest.txt`, `verified-snapshot-v6-identity.json` and `preservation-v6.json`. The earlier snapshot-v4 counts above are historical baseline evidence. Cached source-overlay tests are not clean installation or remote CI.

Run the module and cross-component checks with the existing project environment:

```powershell
.venv-release-check/Scripts/python.exe -m pytest -q tests/test_subtask_contracts.py tests/test_subtask_scheduler.py tests/test_subtask_persistence.py tests/test_subtask_runner.py tests/test_subtask_handoff.py tests/test_subtask_typed_runner.py tests/test_subtask_synthesis.py tests/integration/subtasks --basetemp .pytest-tmp/subtasks-review
.venv-release-check/Scripts/python.exe -m pytest -q --basetemp .pytest-tmp/subtasks-full
.venv-release-check/Scripts/python.exe -m pip check
git diff --check
```

Use a distinct empty `--basetemp` per concurrent test invocation. The retained full-suite snapshot excludes secrets, review databases, virtualenvs, external datasets and Git metadata. Linux validation uses `scripts/check_linux_container.py`, which verifies source/config hashes against the intended image before pytest and disables container networking. It requires an existing image matching that snapshot; source-overlay evidence is not a replacement for F's clean packaging qualification.

## Limits and subsequent work

No new model generation, Ragas, hosted inference, live Databricks work, browser activation, publication or deployment is included. Real-model source selection/composition quality, B/C live adapter wiring, E progress UI, F exact-release packaging/CI, independent reviewer usefulness and G target-environment security/recovery/load evidence remain separate gates. Existing failed generations and owner judgments remain historical evidence; concurrent retrieval does not repair their answer quality.

Manual review is needed for new generated claims before calling them owner-accepted and for exact-revision approval/export. No human scoring of these synthetic scheduler checks is needed. No such generation or approval is requested by this engineering milestone.

