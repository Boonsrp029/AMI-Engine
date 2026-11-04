# AMI Engine agent guidelines

## Scope and purpose

These instructions apply throughout this repository unless a more specific
`AGENTS.md` applies. Current user instructions take precedence.

Support the planned pivot to bounded concurrent subtasks within the analyst
workflow. Preserve the existing sequential workflow while the new path is
developed and qualified. This file defines workstreams and acceptance criteria;
it does **not** activate Goals, authorize model runs, launch agents, or authorize
publication or deployment.

Inspect `README.md`, applicable local instructions, current source, tests and
retained evidence before relying on historical conclusions. Read
`docs/production/readiness.md` for qualification boundaries.

## Baseline and evidence boundaries

The following is a retained snapshot from 3 November 2026, not a promise about
the current checkout. Revalidate relevant evidence before reporting it as current.

- Analyst implementation: v1.69; mapping: v44.
- Retained offline results: 1,294 Windows passes; 1,293 Linux passes and one skip.
- The v1.68 batch passed two development preflights and stopped at r07.
- r07 is consumed development evidence. Nineteen qualification cases remained
  unattempted when that allowance closed.
- v1.69's effect on actual generation is unverified.
- Generation is held; previous inference allowances are closed. Require a new
  explicit applicable grant before further generation.
- Neither portfolio completion nor production qualification has been established.

Keep offline correctness, actual model quality, owner acceptance, independent
reviewer evidence and production qualification distinct. Do not credit corrected
or replayed answers as fresh generation successes. Do not count consumed cases
as unseen after tuning on their failures.

## Invariants and execution boundaries

- Preserve the core architecture, public APIs, sequential entry points,
  exact-revision approval/export controls and strict evidence validation.
- Preserve historical outputs, owner judgments, source snapshots, benchmark
  records and approved exports. Store new experiments separately.
- Keep all library versions, requirements and dependency constraints unchanged.
  Propose dependency changes, migrations and public API changes separately.
- Introduce concurrency through an opt-in path until its acceptance gates pass.
- Use fixed responses, deterministic workers and mocked services for offline
  validation. Do not infer model quality from those checks.
- Do not start LLM generation, Ragas, hosted inference or live Databricks work
  without explicit authorization covering its purpose, budget and scope.
- Do not commit, push, deploy, contact reviewers or send alerts automatically.
- Keep local LLM access serialized initially. Increasing inference concurrency
  requires an agreed resource/call budget and measured evidence.
- Treat concurrent complete analyst requests as a separate scope decision from
  parallel branches within one analyst request.
- Check the shared five-hour usage allowance before major passes and long
  validation. At 90% used, save work, results and an exact handoff, then pause
  under the standing user instruction. If usage cannot be observed, disclose
  that limitation; do not invent a reading.

## Coordination and planning

Separate workstreams are not automatic permission to spawn agents or chats.
Use parallel agents only when the user explicitly requests delegation or parallel
agent work. When multiple workers are authorized:

- Use isolated branches/worktrees and agree file ownership before editing.
- Workstream A publishes the shared contract before dependent implementation.
- Avoid simultaneous edits to shared runtime, schema, API or configuration files.
  Assign an integration owner for those files.
- Share interfaces and evidence paths, not copied mutable task state.
- Revalidate the integrated revision; separate green branches do not prove that
  their combination works.

For each implementation plan, provide:

1. Current behavior and source evidence.
2. Proposed changes and file ownership.
3. Dependencies on other workstreams.
4. Small reviewable implementation passes.
5. Acceptance checks and meaningful tests.
6. Risks, human decisions and separate migration tasks.

## A — Bounded subtask orchestration

### Planning brief

Design an opt-in workflow that decomposes one analyst request into bounded
independent subtasks, runs eligible work concurrently and aggregates results
before composition and safety.

Publish the shared contract first:

- Request, subtask and attempt identifiers.
- Dependency relationships and concurrency limits.
- Statuses and persisted progress events.
- Evidence/result envelopes and corpus identity.
- Deadlines, cancellation and retry rules.
- Required versus optional branches.
- Partial-result and failure policies.
- Deterministic aggregation.

Preserve sequential entry points. Propose retrieval concurrency limits for review
and identify module ownership and integration interfaces for B–F.

### Goal and acceptance

Implement the agreed bounded scheduler. Offline integration tests must prove
that independent branches overlap, dependent work waits, concurrency limits are
enforced, aggregation is deterministic and failed/cancelled attempts cannot
publish late results. Preserve review/export guarantees and document remaining
model-quality limitations.

## B — Parallel retrieval and evidence isolation

### Planning brief

Inspect local retrieval, source inspection, corpus identity and citation handling.
Define results that retain originating subtask, source identifiers, exact content,
dates, locators and retrieval diagnostics.

Plan bounded retrieval and inspection with duplicate sources, empty results,
conflicts, changed corpora and stable ordering. Do not change ranking algorithms
merely to introduce concurrency. Own retrieval adapters/tests and integrate
through A's contract.

### Goal and acceptance

Demonstrate independent retrieval overlap, deterministic ranking and merging,
correct duplicate/conflict handling and isolation between subtasks. Every result
must retain pinned corpus identity and resolvable provenance. Preserve existing
retrieval APIs and ranking behavior unless a separate change is reviewed.

## C — Evidence aggregation and composition correctness

### Planning brief

Plan synthesis that preserves number, period, geography, measure, denominator
and observation/forecast relationships across subtask evidence.

Use consumed r07 for diagnosis and different facts for synthetic regressions.
Inspect unit mapping, composition cues, fallback disclosures and strict validation.
Define how missing or failed branches affect the brief. Preserve supported partial
answers and specific evidence gaps. Distinguish raw composition, application
fallback and editorial correction. Propose composition-contract changes explicitly.

### Goal and acceptance

Integrate composition with A/B's results while retaining evidence-unit and subtask
provenance. Tests must reject cross-unit number/date/measure substitutions, expose
missing required branches and preserve safety and approval controls. Actual model
improvement requires a separately authorized diagnostic. Preserve the original
r07 failure and reserved evaluation facts.

## D — Concurrency, failure and recovery verification

### Planning brief

Use deterministic workers and controlled barriers instead of timing-sensitive
sleep assertions. Cover:

- Actual overlap, caps and dependency ordering.
- Deterministic aggregation, branch failure and partial completion.
- Queued/active cancellation, deadlines and late-result fencing.
- Duplicate submissions and explicit retries.
- Termination, restart and changed corpus identity.
- Review, edit, approval and export races.

Allocate module tests to their implementation owners; D owns cross-component
integration tests. Document what offline workers cannot prove about inference
backend cancellation or performance.

### Goal and acceptance

Build tests that detect capacity violations, duplicate work, late publication,
corrupted history and stale approvals. Keep existing tests green without weakening
validation. Record unresolved real-backend cancellation and load questions.

## E — Subtask progress and reviewer interface

### Planning brief

Display the parent task and its subtasks using A's persisted events. Cover queued,
waiting-on-dependency, running, completed, failed and cancelled states. Distinguish
branch completion from final brief readiness and expose partial-result consequences.

Avoid invented completion percentages. Any percentage needs an explicit denominator
and a policy for dynamically added subtasks. Preserve source inspection, revision
history and exact-revision review/export. Plan reconnect, stale-event and refresh
behavior. Own UI files and coordinate API changes with A.

### Goal and acceptance

Verify truthful states and stable reconnect/refresh behavior with synthetic
browser/API checks. Completed retrieval must never appear as an approved or
complete analyst brief. Preserve revision approval/export controls.

## F — Reproducible packaging, CI and integration

### Planning brief

Inspect the full Docker recipe, source-overlay evidence, environment prerequisites
and CI boundaries. Plan builds of the intended revision with durable review storage,
excluded secrets and immutable source/image identifiers. Cover sequential default
and opt-in concurrent modes. Integrate after A–E's interfaces stabilize and prepare
publication changes without committing or pushing automatically.

### Goal and acceptance

Verify dependency consistency, public entry points, non-root startup, explicit
model/corpus prerequisites, offline tests, persistent restart and byte-identical
cached approved exports. Produce runnable instructions and exact artifact identities.
Remote CI remains pending until authorized publication and actual success for the
reviewed revision. Distinguish cached builds from clean installation evidence.

## G — Human usefulness and operational qualification

### Planning brief

Use existing reviewer materials and release contracts. Prepare tasks and measures
for completion, total checking/correction time, unsupported or omitted facts,
edits, usefulness and the value of progress visibility.

Prepare decisions for hosting, model/retrieval connectivity, durable storage,
identities, service hours, incident ownership, alert delivery, backup/retention,
queue policy, error budget and sustained workload. Keep owner acceptance,
independent reviewer evidence and target-environment qualification distinct.
Do not arrange sessions, send alerts or deploy automatically.

### Goal and acceptance

Maintain the qualification protocol and evidence matrix. Once the owner arranges
sessions, record actual observations without invented ratings or time savings.
Implement one justified feedback improvement and repeat its affected checks.

After technical and quality gates pass, prepare the exact operational/deployment
exercise for authorization. Full qualification requires real reviewer evidence,
named-environment security/recovery/alert/rollback/load results and owner acceptance
of residual risks. Report unmet gates explicitly until then.

## Integration sequence

1. A publishes the shared contract and file-ownership map.
2. Authorized workers on A, B, C and D use isolated worktrees against that contract.
3. E integrates stable progress events; F prepares packaging and integration.
4. Integrate compatible changes deliberately and run the combined offline suite.
5. Freeze a concrete diagnostic and obtain its specific generation budget/grant.
6. Qualify fresh outputs and conduct owner-arranged independent reviewer tasks.
7. Complete F/G release and operational evidence under separate publication and
   deployment authorization.

A working concurrency implementation is an engineering milestone. Answer-quality
qualification and production qualification require their own evidence.
