# Shared subtask contract: ami-subtasks-v1

Status: executable contract published before scheduler implementation. No model execution or browser activation is enabled by this package.

The caller supplies a validated explicit Plan for one analyst request. Plan identity is SHA256 of canonical validated JSON (including resource policy, ordered tasks, query and corpus hash), without timestamps. Existing run/parent-attempt UUIDs are retained; each child execution has its own UUID. Task IDs follow declared order s01ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“s05. Forward dependencies are allowed, cycles and unknown IDs are rejected.

## Execution rules

- One to five read-only retrieve/inspect_sources branches. Default concurrency two, configurable down to one. Local model concurrency one and parent-wide main-call ceiling four. No LLM planner or branch inference.
- Parent execution deadline at most180seconds; branch deadline defaults30seconds from branch start and is capped by remaining parent time. Dependency waiting consumes parent time. The existing owned-process boundary remains the hard stop; threads must cooperate and cannot promise backend cancellation.
- States: queued, waiting_on_dependency, running, completed, failed, cancelled, blocked. Terminal transitions cannot be revised. Duplicate event delivery must be deduplicated by the persistence adapter, never interpreted as a new transition.
- Every event/result carries parent/child identity and pinned corpus hash. Coordinator ordinal is per parent attempt; SQLite's existing global event sequence remains the durable replay order. Times are timezone-aware; elapsed/deadline accounting uses monotonic clocks.
- Completed evidence/missing/conflicting outcomes are distinct from technical failure. Missing can retain context records but cannot assert support. Conflicting is a structural label requiring source support, not a proof of contradiction.
- Required technical failure/timeout/blocked dependency prevents final drafting; stop admission and cancel other work. Optional failure permits aggregation only after required branches complete, with explicit missing-branch records. Failed dependencies block their descendants, even when the failed ancestor is optional.
- Parent cancellation fences all further publication, including buffered completion. Retain already published evidence. No automatic retry; explicit retry creates new parent/child attempts and reruns the plan. Restart marks unfinished work interrupted/cancelled; durable mid-branch continuation is deferred.

## Result and aggregation boundary

Sources retain exact content, SHA256, source ID, corpus ID, role, URL/title, publication and zero-based PDF locator. Unknown dates/locators remain unknown. Result order is plan order then original adapter ranking, independent of completion order. Deduplicate only identical records; source-ID/content/corpus or metadata collisions fail explicitly. Preserve every source's originating subtask IDs in the aggregate. Never silently truncate evidence to fit composition.

Workers receive isolated validated operation inputs plus declared dependency results and cancellation/deadline context. They return Results; they never write SQLite or emit unfiltered diagnostics. The coordinator validates returned parent/child/plan/corpus identity before publishing. Source content cannot authorize new operations. B validates inspected IDs against the pinned corpus. C validates semantic support and composition coverage: structural contract validity alone is insufficient.

## Ownership and delivery

| Owner | Modules / boundary |
|---|---|
| A | src/pilot/subtasks/contracts.py, future scheduler.py, aggregation.py and persistence.py; sole integrator of existing shared runtime/worker/store/API/config |
| B | Retrieval/inspection adapters and module tests; consume Subtask/Identity and return Result |
| C | Compose aggregate evidence with branch provenance and missing-branch records; preserve public Draft/safety contracts |
| D | Cross-component barrier-driven integration tests, failure/restart/cancellation/approval races |
| E | UI files; consume persisted progress projection; browser/API activation separately reviewed |
| F | Packaging and CI; verify integrated source and preserved sequential default |

Delivery sequence: contract/types/fixtures first; bounded coordinator second; deterministic aggregate third; attempt-fenced single-writer persistence fourth; opt-in programmatic runner fifth; combined tests last. Existing query_agent(), PilotEngine.run(), ResearchRequest, Draft and sequential browser runtime stay unchanged. No new database table, public endpoint, dependency, source ranking or inference allowance is introduced by this contract milestone.

## Qualification boundaries

Synthetic contract tests prove structural rules only. Scheduler overlap, deadlines, cancellation, persistence and review/export integration remain unfinished until executable integration evidence exists. v1.69 actual model quality and production readiness remain unqualified. Generation is held. Source/benchmark/owner artifacts and dependency versions must remain unchanged.


## Coordinator implementation checkpoint

The private scheduler.run_plan entrypoint now accepts a validated plan, existing parent IDs, a trusted read-only operation callback and a parent event sink. It returns a Report with plan-ordered results, stable aggregate sources/origins, missing branches and an explicit can_compose gate. Source role is per branch: identical source records can carry support in one branch and context in another, preserved in origins. Other source metadata mismatches fail aggregation.

All branch progress/results are emitted on the coordinator thread. A sink exception aborts execution and signals worker cancellation. Timed-out threads retain physical capacity until they exit; no replacement work is admitted merely because the logical status is failed. Late worker completion never emits a result. Threads cannot be force-killed: direct programmatic callers must supply cooperative bounded adapters, and production integration must retain the owned-process hard stop. Current tests prove fencing and status/deadline decisions, not actual backend termination.

Current evidence:31 targeted contract/coordinator tests pass, including actual barrier overlap, dependency/cap control, optional/required failure, parent cancellation, fake-clock deadlines, identity mismatch and source collision/deduplication. Persistence adapter, restart replay, composition/safety handoff, full offline integration and review/export race checks are pending. This checkpoint does not complete Workstream A or qualify model quality.


## Persistence integration checkpoint

AttemptSink registers exactly one plan per parent attempt in an immediate SQLite transaction, using the existing events table and current-attempt fence. Subsequent progress/results require the same plan/run/attempt/corpus identity; durable cancellation/restart closes the sink. The scheduler polls this fence before admitting/accepting work. No child thread receives database access.

progress_view is a read-only latest-attempt projection for E. After parent termination, unfinished branch states are shown as cancelled/interrupted with derived=true rather than fabricated persisted transition events. Earlier events remain untouched; retries have a fresh attempt and no automatic reuse. No schema migration or public endpoint is added.

Temporary real SQLite integration tests cover late completion after cancellation/restart, stale-attempt writes, explicit retry with fresh IDs, duplicate plan registration, current-revision review, approval invalidation after edits and byte-stable cached exports. These are synthetic test decisions, not new owner approvals. Programmatic composition/safety handoff and owned-process integration remain the next pass; this adapter alone does not enable concurrent browser requests or prove hard thread/backend termination.


## Opt-in owned-process runner

runner.run_stored_plan(store, run_id, plan, corpus_path, operation, compose, safety) is an internal explicit-plan entry point. It acquires the existing runtime lease, claims the queued parent, registers the plan and launches one owned child process. The child runs bounded branch threads, then hands an eligible Report to compose(report, model_access). Sources come from the aggregate, not from an unrestricted composer return value. Nonempty drafts must pass safety(draft, sources); empty abstentions retain the existing safety-skip policy. Optional technical failures append explicit partial-brief warnings. A required failure cannot reach composition.

Trusted adapters must route model-provider invocations through model_access.main(callback), which serializes and limits four main calls. The runner wraps the entire safety callback with the same lock and a one-invocation guard budget. Markers persist attempted calls even if the child fails. Arbitrary Python callbacks are trusted integration code, not sandboxed source tools; no default callback/model client is provided, and real generation still needs its own explicit grant. Source entailment and real NeMo effectiveness remain C/qualification responsibilities.

The parent verifies corpus bytes before and after execution, persists child events through the attempt fence and saves only a valid final draft after clean child exit. It reuses the existing owned-process stop and owner-death/deadline watchdog, preventing abandoned branch threads from escaping into a later parent request. Direct scheduler callers still have cooperative-thread limits; use the stored runner for the owned-process boundary. Process termination is not proof that an external inference server stopped computing.

Existing sequential entry points, API/SQLite schema and approval/export behavior stay unchanged. Spawned callback functions/objects must be importable and pickleable. Browser opt-in activation, concrete B/C production adapters, UI progress exposure, live model quality and deployment qualification remain separate workstreams.
