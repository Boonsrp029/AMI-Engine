# Shared subtask contract: ami-subtasks-v1

Status: the private contract, scheduler, persistence adapter and opt-in owned-process runner are implemented, including C's typed composition-lineage handoff. Integrated Windows/Linux offline validation passes; no model execution or browser activation is enabled by this package. See [usage and acceptance evidence](workstream-a.md).

The caller supplies a validated explicit Plan for one analyst request. Plan identity is SHA256 of canonical validated JSON (including resource policy, ordered tasks, query and corpus hash), without timestamps. Existing run/parent-attempt UUIDs are retained; each child execution has its own UUID. Task IDs follow declared order s01 through s05. Forward dependencies are allowed, cycles and unknown IDs are rejected.

| Identifier | Meaning and lifetime |
|---|---|
| Existing `ResearchRequest.request_key` | Caller-supplied idempotency key handled by `Store.create`; unchanged request-key conflict rules. |
| `Identity.run_id` | Existing stored parent request UUID; stable across explicit retries. |
| `Identity.attempt_id` | Fresh parent execution UUID for every explicit retry; fences all child events and final publication. |
| `Plan.plan_id` | Canonical hash of the explicit plan and resource policy; stable for identical validated input. |
| `Subtask.subtask_id` | Declared plan position, `s01` through `s05`; not completion order. |
| `child_attempt_id` | Fresh UUID per launched branch attempt; propagated through progress, results and dependency references. |
| `corpus_sha256` / `content_sha256` | Exact corpus bytes / exact source-text UTF-8 bytes. B must verify source membership; a matching claimed hash alone does not prove it. |

Dependency references retain the upstream subtask ID, child attempt ID and hash of its validated serialized result. A worker cannot substitute another attempt's dependency result. Workers return evidence envelopes, never arbitrary mutable task state or authority to launch extra branches.

## Execution rules

- One to five read-only retrieve/inspect_sources branches. Default concurrency two, configurable down to one. Local model concurrency one and parent-wide main-call ceiling four. No LLM planner or branch inference.
- Parent execution deadline at most 180 seconds; branch deadline defaults 30 seconds from branch start and is capped by remaining parent time. Dependency waiting consumes parent time. The existing owned-process boundary remains the hard stop; threads must cooperate and cannot promise backend cancellation.
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
| A | src/pilot/subtasks/contracts.py, scheduler.py (including aggregation), persistence.py and runner.py; sole integrator of existing shared runtime/worker/store/API/config |
| B | Retrieval/inspection adapters and module tests; consume Subtask/Identity and return Result |
| C | Compose aggregate evidence with branch provenance and missing-branch records; preserve public Draft/safety contracts |
| D | Cross-component barrier-driven integration tests, failure/restart/cancellation/approval races |
| E | UI files; consume persisted progress projection; browser/API activation separately reviewed |
| F | Packaging and CI; verify integrated source and preserved sequential default |

Delivery sequence: contract/types/fixtures first; bounded coordinator second; deterministic aggregate third; attempt-fenced single-writer persistence fourth; opt-in programmatic runner fifth; combined tests last. Existing query_agent(), PilotEngine.run(), ResearchRequest, Draft and sequential browser runtime stay unchanged. No new database table, public endpoint, dependency, source ranking or inference allowance is introduced by this contract milestone.

## Qualification boundaries

Synthetic tests establish structural and lifecycle behavior only. Barrier-driven scheduler, real SQLite, spawned-worker and review/export checks are implemented. Final integrated evidence and exclusions are recorded in the usage and acceptance document; historical pass counts below are checkpoints, not current release qualification. v1.69 actual model quality and production readiness remain unqualified. Generation is held. Source/benchmark/owner artifacts and dependency versions must remain unchanged.


## Coordinator and persistence boundary

`scheduler.run_plan` validates each returned result against the actual launched parent/child/plan/corpus and declared dependency references. All progress/results are emitted by the coordinator. A sink failure aborts admission and signals cancellation. A timed-out thread retains physical capacity until it exits; direct scheduler callers need cooperative adapters. Late completion cannot publish.

`AttemptSink` registers one plan per parent attempt using the existing SQLite events table and current-attempt fence. Durable cancellation/restart closes the sink; the scheduler checks the fence before admitting or accepting work. No child thread writes the database. `progress_view` projects the latest attempt and explicitly labels derived interruption states. Prior history is retained and retries create fresh identities without automatic reuse.

## Opt-in owned-process runner

runner.run_stored_plan(store, run_id, plan, corpus_path, operation, compose, safety) is an internal explicit-plan entry point. It acquires the existing runtime lease, claims the queued parent, registers the plan and launches one owned child process. The child runs bounded branch threads, then hands an eligible Report to compose(report, model_access). Sources come from the aggregate, not from an unrestricted composer return value. Nonempty drafts must pass safety(draft, sources); empty abstentions retain the existing safety-skip policy. Optional technical failures append explicit partial-brief warnings. A required failure cannot reach composition.

Trusted adapters must route model-provider invocations through model_access.main(callback), which serializes and limits four main calls. The runner wraps the entire safety callback with the same lock and a one-invocation guard budget. Markers persist attempted calls even if the child fails. Arbitrary Python callbacks are trusted integration code, not sandboxed source tools; no default callback/model client is provided, and real generation still needs its own explicit grant. Source entailment and real NeMo effectiveness remain C/qualification responsibilities.

The parent verifies corpus bytes before and after execution, persists child events through the attempt fence and saves only a valid final draft after clean child exit. It reuses the existing owned-process stop and owner-death/deadline watchdog, preventing abandoned branch threads from escaping into a later parent request. Direct scheduler callers still have cooperative-thread limits; use the stored runner for the owned-process boundary. Process termination is not proof that an external inference server stopped computing.

Existing sequential entry points, API/SQLite schema and approval/export behavior stay unchanged. Spawned callback functions/objects must be importable and pickleable. Browser opt-in activation, concrete B/C production adapters, UI progress exposure, live model quality and deployment qualification remain separate workstreams.

## Durable event validation

Progress/result delivery is validated in an immediate SQLite transaction. Identical progress ordinals and identical completed-result redelivery are idempotent. Reused ordinals with changed payloads, changed child identity, out-of-order ordinals and reopened terminal states are rejected without adding history. A result requires its matching completed child. Parent-attempt fencing applies before duplicate acceptance, so a stale attempt cannot publish by replaying an old event.

Typed composition callbacks may return C's unguarded `SynthesisResult` instead of a dictionary. The runner validates lineage, binds exact draft/source/lineage content to final safety, and the parent persists the verified candidate and revision metrics through existing fences. A candidate is neither approval nor publication evidence. See the completion audit for current test scope.
