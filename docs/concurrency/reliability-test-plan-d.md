# D: bounded-subtask reliability strategy and evidence

Date: 5 November 2026. Offline reliability of A–C is separate from model quality and production qualification. The sequential browser workflow stays the default. See [shared contract](contract-v1.md), [A boundary](workstream-a.md) and [readiness](../production/readiness.md).

## Current behavior and ownership

Inspection covered repository instructions, README, readiness, contracts/scheduler/persistence/runner/synthesis, module tests and retained D logs. The opt-in path accepts explicit plans of one to five read-only branches, concurrency one or two, dependencies, required/optional policy and pinned corpus identity. Scheduling and aggregation preserve declared ordering. AttemptSink persists through the parent-attempt fence. The stored runner owns a spawned process; only its parent publishes final drafts after clean exit and corpus checks. C retains evidence-unit provenance through composition and safety. Review/export remains tied to exact revisions.

D owns integration tests, synthetic worker fixtures and this report. A owns contracts, scheduler, persistence, runner and shared Store/runtime/API. B owns retrieval adapters. C owns synthesis. Their module fixes remain their responsibility; D retains failing assertions. Dependencies are A's published contract and C's explicit composition boundary. B's actual corpus-membership guarantees still require its adapter tests: a synthetic envelope hash does not establish membership.

## Deterministic harness

- Workers signal entry, then wait for explicitly released gates. Two entry signals before either release prove overlap. Locked entry/exit counters prove caps. Never infer overlap from sleep duration.
- Reverse completion order and compare aggregate plan/ranking order. Dependent entry checks the upstream result is already durable.
- Inject a monotonic clock and advance to deadline boundaries. Finite wait timeouts are harness watchdogs, not latency benchmarks. Release gates in finally blocks and reap only owned processes.
- Control SQLite BEGIN IMMEDIATE acquisition to exercise both review/edit and export/edit transaction orders. Preserve revision-one export bytes when export wins; reject the old decision when edit wins.
- Use importable fixed-response spawned workers for termination and retry. Release gates use multiprocessing semaphores: a killed Event waiter can leave Event.set blocked in the harness. Entry notifications can remain Events. The bounded reproduction is retained locally.
- No LLM, real NeMo, Ragas, hosted inference or Databricks. Synthetic databases and sources never replace historical artifacts or judgments.

## Allocation and test oracles

| Concern | Owner module tests | D integration oracle |
|---|---|---|
| Overlap/caps | A scheduler limits and serialized runner model budget; B adapter resource isolation | Both branches enter before release; cap one/two enforced through real sink/Store and owned runner |
| Dependencies/order | A DAG/cycle/blocked-descendant tests; B rank/dedup; C binding lineage | Upstream completion durable before dependent entry; reversed finish preserves plan/rank order |
| Failure/partial | A required-stop/optional policy; C partial facts, gaps and conflicts | Required failure cannot draft; optional failure retains required evidence; sink outage and source collision cannot publish success |
| Queued/active cancellation | A tokens, admission and process cleanup | Queued branch never enters; active child reaped; buffered/late work cannot publish; prior history retained |
| Deadlines/fencing | A fake-clock branch/parent deadlines, physical-slot retention and runner hard deadline | Deadline-boundary result rejected before persistence; cancelled/recovered old attempt cannot publish |
| Duplicates/retry | A Store keys, plan registration and attempt identity | Same-key concurrent submission creates one run; redelivery writes once; altered ordinal/identity rejected; explicit retry gets fresh attempts |
| Termination/restart | A lease/watchdog/recovery | Kill coordinator at confirmed entry, recover, preserve approved history and explicitly retry; old result rejected |
| Changed corpus | B real membership/content/inspection; A pre/post execution hashes | Wrong result identity rejected; temporary corpus mutation prevents final draft |
| Composition/safety | C number/date/measure/denominator/scope, bindings, missing/conflicting outcomes and fallback | Real report through C; wrong number/cross-branch binding rejects; guard failure or cancellation inside guard prevents publication |
| Review/edit/approval/export | A/shared Store revision checks and export cache | Both SQLite transaction orders; old approval cannot approve revision two; cached bytes stable; edit requires fresh approval |

A module tests: tests/test_subtask_contracts.py, test_subtask_scheduler.py, test_subtask_persistence.py and test_subtask_runner.py. C: tests/test_subtask_synthesis.py. B should add corpus-backed adapter tests with its implementation. D does not count fake retrieval as B acceptance. Owner module tests cover fine-grained adversarial inputs; D owns lifecycle joins and cross-component races.

## D suite and commands

| D file under tests/integration/subtasks/ | Cases | Boundary |
|---|---:|---|
| test_subtasks_execution_integration.py | 17 | Scheduler, sink, Store, identity/history and review/export |
| test_subtasks_recovery_integration.py | 4 | Process loss, queued cancel, sink outage and source collision |
| test_subtasks_synthesis_integration.py | 5 | Aggregate, C, synthetic guard and publication fence |
| test_subtasks_owned_runner_integration.py | 5 | Owned child, overlap, call budget, corpus change, cancel/retry |
| test_subtasks_review_linearization.py | 4 | Both transaction orders for review/edit and export/edit |

Total: 35. Fixed importable workers live in tests/fixtures/workers/subtask_integration_child.py.

```powershell
.\.venv-release-check\Scripts\python.exe -m pytest -q tests/integration/subtasks --basetemp .pytest-tmp/d-subtasks
.\.venv-release-check\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp/d-full
git diff --check
```

Use a fresh basetemp for a deliberate new run. Observation timeout does not justify restarting a running suite. Linux validation uses scripts/check_linux_container.py: sanitized read-only snapshot, network none, non-root image, no credentials or reviewer databases. A source-overlay image reuses dependencies; it is not clean installation or remote CI evidence.

## Small passes and retained evidence

1. Contract/source identity and real scheduler/sink/Store tests. D caught duplicate progress writes and terminal-child reopening. A repaired transactional delivery validation; D assertions stayed unchanged.
2. Controlled coordinator termination/restart, queued cancellation, sink failure and aggregation collisions.
3. C integration with branch provenance, fixed composition and guard failures.
4. Owned runner, call budgets, corpus mutation, active cancellation and explicit retry. Correct faulty Event release fixture to semaphore; retain failed run and bounded reproduction.
5. Both transaction orders for approval/edit and export/edit, combined regressions and source-hash checks.

Evidence is retained locally in reports/workflow_pilot/concurrency-d/. Earlier failures remain historical. semaphore-run.txt records 31 passing D cases; transaction-order-run.txt records four later passing cases. Initial Linux snapshot passed 1,399 tests, one skip and 15 warnings; source comparison found no changed existing files, but that snapshot excludes the four new tests. Final validation-summary.json records final results and identities; do not retroactively credit tests to earlier runs.

## Offline limitations and later qualification

Reaping a client process does not prove a server/GPU stopped computing or released memory. Barriers cannot establish backend queue fairness, token streaming, HTTP cancellation, provider retries, outage behavior, GPU capacity, sustained throughput or p95 latency. Fixed safety/composition responses do not prove entailment, relevant extraction, completeness, prompt-injection resistance or model quality. Local SQLite checks do not prove deployment-volume durability, distributed locking or multi-host transactions. Source-overlay tests do not prove fresh installation, remote CI, staging security, alerts, restore objectives or operational load.

Separately authorized work must measure actual backend cancellation/resource release, serialized inference under concurrent retrieval, server failures, sustained workload, deployed corpus consistency and reviewer usefulness. Preserve failed r07 and reserved facts. No new inference is authorized by this strategy.

## Acceptance and human decisions

D completion requires all 35 integration cases plus existing regressions passing on recorded source, with drift explained. No weakening validation, xfail or skip may hide a defect. Keep platform skips/warnings explicit. Existing defect regressions show detection of persistence errors; future mutation checks should remove caps/fences/idempotency/revision checks in an isolated copy and prove failure.

Deterministic failures require engineering diagnosis, not human scoring. Owner decisions remain necessary for changed resource/retry/partial policies, public API/schema migrations and real-backend budgets. Generated outputs require semantic review before owner acceptance; exact stored approval remains necessary for export. No tests authorize publication or deployment.

## Final validation checkpoint

- Windows full regression: **1,400 passed, 15 warnings**, 427.34 seconds. Four additive transaction-order cases then pass separately: **4 passed**, 16.93 seconds. Do not describe the earlier full-suite log as containing those four tests.
- Final Linux sanitized snapshot: **1,403 passed, one skipped, 15 warnings**, 79.21 seconds, including all 35 D cases. The existing platform skip remains explicit.
- Source comparison: no existing Windows snapshot file changed, and no file in the final Linux snapshot changed at reporting time. All four requirements/constraints manifests match the earlier Linux snapshot.
- Exact image: ami-pilot:d-integration-20261105, SHA256 9b2ad038d602bb03eada20ccffe5c2af2c248be3bf2e8f8f7a825b710ff323ec, user 10001:10001. Source-overlay build, network disabled during tests. No fresh dependency installation or remote CI claim.
- git diff --check passed; Git emitted line-ending conversion notices only. Historical failures and the sandbox Docker permission denial remain recorded separately.

D's offline integration milestone is complete for this snapshot. B's corpus-backed adapter qualification, real inference cancellation/load, semantic quality, UI activation and portfolio/production completion remain outside this milestone. No generation, dependency changes, publication or deployment was performed by D.
