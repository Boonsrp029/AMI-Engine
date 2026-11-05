# Workstream A completion audit

Scope: one explicit analyst request with opt-in bounded independent read-only branches, followed by composition and safety. Sequential public entry points and review/export controls remain the default. This audit does not establish answer quality or production readiness.

## Requirements and authoritative checks

| Requirement | Implementation and verification |
|---|---|
| Shared contract delivered before scheduler | `contract-v1.md`, `contracts.py`, the retained contract-first checkpoint and `tests/test_subtask_contracts.py`: request/run/attempt identities, DAG, limits, source envelopes, statuses and terminal transitions. |
| Eligible independent branches overlap and dependencies wait | `scheduler.py`; barrier-controlled `test_overlap_caps_dependency_and_deterministic_aggregation`, `test_serial_cap_waits_for_first_branch_completion`, D's cap-one/cap-two SQLite overlap tests and dependency durability test. |
| Bounded work | Plan accepts 1–5 tasks and retrieval concurrency 1–2; `ModelAccess` serializes four main calls and one final safety invocation. Budget exhaustion and serialization tests use fixed callbacks. Existing shared-store runtime lease prevents whole-request overlap. No host-wide inference broker is claimed. |
| Deterministic aggregation | Plan order then adapter rank, exact source dedup with branch origins, source collision rejection; scheduler and D synthesis tests. Completion order never determines citation order. |
| Deadlines and cancellation | Monotonic parent/branch deadlines, cancellation tokens, parent-attempt fence, late-result rejection and owned-process watchdog/reap. Controlled clocks and spawned blocked workers verify these boundaries. External server-side computation cancellation remains unproven. |
| Required/optional and partial failure | Required failure blocks composition; optional failure produces explicit partial warnings. Failed ancestors block descendants. Completed missing/conflicting evidence is separate from technical failure. Contract, scheduler, SQLite and owned-runner tests cover these cases. |
| Truthful durable progress and recovery | `AttemptSink`, `progress_view`; atomic duplicate-event handling, terminal-state fencing, fresh retries, restart interruption and queued cancellation. Derived interrupted states are labeled; no invented progress percentage or automatic resume. |
| Composition before final safety, with retained lineage | `_handoff.py` and `runner.py` accept old dicts or unguarded C results. Validate accepted source/child identities, detach callback state, bind exact content before/after safety and verify the transported candidate in the parent. `test_subtask_typed_runner.py` covers real C projection, fallback attribution, safety mutation/rejection and publication races. |
| Exact-revision review/export | Existing Store APIs unchanged. Spawned typed/legacy paths plus D review/edit/export ordering tests require exact approval, invalidate after edits, preserve old candidate attribution and cached approved bytes. Empty-claim drafts cannot be approved/exported. |
| Preserve sequential behavior and dependency versions | Baseline SHA256 checks on nine engine/store/runtime/API/schema/requirements files; full offline suite and `pip check`. No existing public API or SQLite schema migration. |
| Documentation and integration ownership | Shared contract, `workstream-a.md`, and A–F ownership/interface table. B concrete adapters, E browser activation, F release/CI and G reviewer/operational qualification remain separate scopes. |

## Evidence status

Final integrated source snapshot: `3ebb6b5a9fa7e2e5312821b893261e5d04abf9516da8c5b89b2c6d15b9d8defb` (233 selected files). Source-overlay image: `sha256:0fa37873fc04ea7b7b45ff31af59db50b41fc4236c07611ab2d925019b3a5c48`. Dependencies come from the existing cached v1.69 base; no clean-install or remote-CI claim.

The integrated snapshot passed **1,440 Windows tests** and **1,439 Linux tests plus one Windows-only skip**, with no failures or deselections. `pip check` found no broken requirements; the nine monitored sequential runtime/API/schema/dependency files retain their baseline hashes. `git diff --check` passes. These are offline structural/lifecycle results, not fresh generation or production qualification. Local manifests and logs are in `.pilot-work/subtasks-a/verified-snapshot-v6-identity.json`, `full-windows-v6-process.json`, `full-windows-v6.txt` and `linux-v6/`. Previous snapshot-v4 passes remain historical baseline evidence and do not validate the new handoff.

No LLM generation, Ragas, hosted inference, Databricks work, publication, deployment or reviewer contact occurred. Synthetic source-support and safety responses prove wiring, not semantic model effectiveness. No new draft is owner-approved by these tests. Manual source review remains required for future real outputs and exact-revision approval/export.

## Subsequent E API integration

The counts and nine-file baseline comparison above belong to the completed A orchestration snapshot. A subsequent, separately requested read-only progress endpoint intentionally changes `api.py`, `_identity.py`, `store.py` and the progress projection. The stored run representation and mutation/approval/export behavior are retained; `Store.get()` now reads under one explicit SQLite transaction. Its contract, validation scope and source snapshot are recorded in [E's API handoff](e-api-handoff.md). E's newer browser files require E's combined validation; the earlier A snapshot does not qualify that UI revision.
