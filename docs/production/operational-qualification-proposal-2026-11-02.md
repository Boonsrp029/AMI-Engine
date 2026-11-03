# Operational qualification proposal — 2 November 2026

**Planning only; no workload, deployment, notification, scheduler or inference is authorized by this document.** This closes a specification gap, not an operational gate. Run the development and fresh-quality gates first. Keep local portfolio qualification separate from subsequent qualification in the owner's existing Databricks staging environment.

## Current implementation versus required evidence

| Area | Current inspected implementation | What still needs demonstration |
|---|---|---|
| Admission | The application constructs `Store(..., queue_limit=2)`; queued capacity is checked in a transaction. Direct `Store` construction can omit that limit. The default runtime owns one child and dispatches one attempt at a time. | Concurrent submissions through the intended deployment must establish one active and at most two waiting, correct capacity rejection, idempotency and no duplicate inference. Do not infer exact active/queued timing from sequential submissions or an unbounded direct-store fixture. |
| Execution bound | `Runtime` starts a monotonic deadline before worker launch, caps it at 180 seconds and fences persistence by attempt. Stopping an owned process includes a join allowance of up to five seconds; this is not proof of a strict 180-second terminal-response bound. | Measure through process exit and terminal persistence. Observe actual inference-server behavior after client cancellation; killing a client does not prove model computation stopped. |
| Queue time | Successful result metadata includes queue wait separately from execution. There is no declared queue-expiry acceptance target. | Record enqueue/start/terminal times externally for every submitted request, including failed and rejected work. Owner must decide whether queue expiry is required and at what bound. No inferred 180-second total user-wait guarantee. |
| Health | `/health` and `/ready` exist; readiness includes dispatcher health. | Neither endpoint proves source relevance, useful answers, policy correctness or model-server cancellation. Exercise readiness during the named failures. |
| Telemetry | [Stored telemetry report](operational-report.md) has bounded read-only aggregation, partial token accounting and report flags. | A live observation stream, meaningful thresholds, delivery, acknowledgement, incident assignment and deduplication need configuration and an exercised alert. Flags in a JSON file are not delivered alerts. |
| Recovery | [Backup/restore](recovery.md), manifest verification and [freshness checking](backup-freshness-2026-10-30.md) exist. Local and container restore mechanics are recorded. | Daily scheduled execution, protected off-host destination, credentials/access, retention, loss window and target-environment recovery within 30 minutes. A small cached-export drill does not demonstrate an outage RTO. |
| Identity | [Principal roles](identity.md) and exact-revision approval/export controls exist; bootstrap mode is shared/local. | Named reviewer credentials, custody, access revocation, hosting TLS/identity boundary, least privilege and attribution must be qualified for the actual deployment. Do not treat historical shared aliases as authenticated identities. |

Inspected sources: `src/pilot/_runtime.py`, `src/pilot/store.py`, `src/pilot/api.py`, `scripts/pilot_backup.py`, `scripts/pilot_operational_report.py`. This proposal changes none of them.

## Accepted targets and decisions still required

The [release contract](release-contract.md) records 1–3 public-data reviewers, one active workflow, two queued requests, warm execution p95 at most 120 seconds, a 180-second execution deadline including policy work, daily backups and restoration within 30 minutes. They are targets, not achieved measurements.

Before authorizing an operational run, the owner must accept:

1. Named environment, exact build/source identity and source/model prerequisites; local success cannot qualify Databricks staging.
2. Service hours, incident owner and fallback contact, an authorized alert destination and acknowledgement target.
3. Backup destination, access and encryption boundary, retention period, scheduling account and an explicit recovery-point target. At most 24 hours is the proposed interpretation of daily backups, not evidence of achieved RPO.
4. Queue-expiry policy, error-rate allowance, workload duration/request count and an explicit new model/time budget. These have not been agreed merely by accepting p95/deadline targets.
5. Rollback destination and residual-risk acceptance. Operator rollback or restoration must not overwrite preserved production history automatically.

**Proposed baseline workload for review:** 30 ordinary warm requests during at least 60 minutes, a separate cold-start observation, and a separately budgeted fault sequence. Start at most one new ordinary request after the prior terminal outcome; keep overload probes separate so deliberate failures cannot be counted as normal successes or silently removed from error denominators. Extend duration if 30 requests do not finish in 60 minutes; stop at the explicitly authorized wall-clock cap and report insufficient samples rather than retry. These values are proposals, not accepted SLOs or an execution grant.

Do not allocate live calls until fresh quality passes. Use public development fixtures for operational repeatability; never tune against reserved held-out answers. Budget normal requests, any warmup, fault probes, NeMo invocations and in-flight work separately before execution. Do not borrow the pending r05 diagnostic allowance.

## Measurement and pass rules to freeze before execution

- Pin Git revision plus dirty-source manifest if applicable, image digest, OS/runtime, model digest/settings, prompt/mapping versions, corpus/index revision and freshness. A mutable image tag or an older green CI run is insufficient.
- For each submission, record a safe request/attempt identifier, workload class, cold/warm designation, enqueue/start/terminal monotonic observations, terminal status, response status, main-call usage and unavailable NeMo/cost fields. Do not place raw prompts, sources, credentials or reviewer identities in shared telemetry.
- Measure end-to-end user wait, queue wait and execution separately. Report sample counts, failures, missing telemetry and p50/p95 for the declared populations. Never silently exclude failed/timeout requests to make a successful-only p95 satisfy the gate.
- Calculate nearest-rank p95 as sorted observation number `ceil(0.95 * n)` with one-based indexing; at n=30 this is observation 29. Report all observations and the small-sample limitation. A synthetic worker latency result is not live inference latency.
- Require no accepted run exceeding the execution deadline, no late draft saved after cancellation/failure, no unauthorized approval/export, no missing audit history, no source-identity mismatch and no capacity-bound violation. Report normal-run failures and deliberate fault outcomes separately. The allowed normal error rate still requires owner agreement; no error threshold is invented here.
- Capture actual host/container GPU, memory, CPU and disk observations where available, including observation intervals and missing periods. Known main tokens are partial; unknown provider-internal, energy and monetary costs remain unknown.
- A failed safety, integrity or source-quality gate stops generation. Insufficient samples, unobserved cancellation or absent alert acknowledgement are **unqualified**, not passes. No automatic retry or relaxed acceptance after seeing the results.

## Fault sequence to authorize separately

| Probe | Evidence needed |
|---|---|
| Saturation and duplicate submission | Record simultaneous requests and responses, queue states, idempotency keys and started attempts; verify capacity rejection causes no model call and duplicate keys create no second run. |
| Queued/active cancellation | Queued cancellation starts no inference. Active cancellation terminates/reaps the owned process and prevents late persistence. Independently observe inference-server activity; if unavailable, backend cancellation remains unverified. |
| Model/guardrail outage | Controlled unavailability produces a safe terminal failure without automatic retry, approval or raw exception leakage. Preserve partial usage and unknown in-flight work. |
| Application termination/restart | Use disposable target storage or an explicitly authorized protected snapshot. Verify interruption, audit history, no duplicate work and preserved cached exports; never kill an unrelated service. |
| Changed corpus/partial result | Change only an authorized disposable copy. No result from an unpinned corpus or stale attempt may be accepted. Preserve original corpus hashes. |
| Backup/restore | Verify the latest scheduled snapshot, simulate declared data loss in isolated storage, time operator start through usable restored application, compare history/export hashes and empty/unapproved/outdated export blocks. Keep failed storage and original snapshot unchanged. |
| Alert and rollback | Generate one controlled condition; record delivery and acknowledgement at the authorized destination, responsible operator, deduplication and resolution. Roll back the exact named artifact/config in staging, verify identity and history, and retain evidence of both revisions. |

Fault injection against real model/server resources requires its own explicit impact and call allowance. Offline fault tests already present do not authorize destructive service operations or replace this named-environment evidence.

## Evidence package and human review

Use a new ignored directory for each run. Retain the frozen contract, authorization, safe per-request observations, immutable identities, raw terminal outcomes, metrics calculation, fault evidence, backup manifests, alert receipts and a requirement-by-requirement verdict. Do not overwrite source-quality reports, owner CSV/history or approved exports.

Engineering can validate calculations, identities, bounds and recovery mechanics without new human scores. Humans must agree the outstanding operational decisions, check new factual drafts before owner acceptance, conduct at least one independent task session and accept the residual risks of the exact deployment before rollout. Approval/export remains an exact stored-revision action. No reviewer invitation or alert is sent by preparing this protocol.

The pending [r05 diagnostic](reduced-r05-proposal-v162-2026-11-02.md) tests a consumed quality defect only. It does not authorize this operational workload or establish portfolio completion or production readiness. The full [Goal](../production-readiness-goal.md) remains incomplete.
