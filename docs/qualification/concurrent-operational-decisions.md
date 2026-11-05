# Operational decision packet — unresolved owner decisions

Prepared 5 November 2026. This is a decision worksheet, not an executable deployment exercise. Accepted historical targets come from the [release contract](../production/release-contract.md); [existing operational proposal](../production/operational-qualification-proposal-2026-11-02.md) supplies historical measurement/fault guidance. No real operations are authorized here.

| Topic | Retained baseline | Decision and required proof | Owner |
|---|---|---|---|
| Hosting | Local portfolio then existing Databricks staging | Name host/environment, access/TLS boundary, exact revision/image and rollback target | Owner + F |
| Model/retrieval | Local model serialized; reviewed app distinct from legacy PyFunc | Reachable model and index routes, auth, timeouts, source schema/identity/freshness; remote localhost is not desktop | Owner + A/B/C |
| Durable storage | SQLite review/history and cached exports | Storage, single-writer/lease scope, access/encryption, migration and failure recovery | Owner + A/F |
| Identities | Offline roles/attribution exist | Named accounts, custody, revocation, least privilege and access review; shared aliases are not independent authentication | Owner |
| Service hours | Supervised pilot | Availability/maintenance window and user fallback | Owner |
| Incident ownership | Unassigned | Primary/backup responders, escalation and acknowledgement target | Owner |
| Alerts | Stored flags are not delivered alerts | Approved destination, thresholds, dedup/resolution; retain actual delivery and acknowledgement receipts | Owner + F |
| Backup/retention | Daily backup, restore target <=30 minutes | Protected off-host destination, scheduler identity, encryption/access, retention/deletion, data-loss simulation and timed usable restore; RPO<=24h is proposed, not accepted | Owner + F |
| Queue policy | One active parent, two queued | Expiry, rejection and cancellation policy; distinguish parent queue from 1–2 concurrent read-only branches | Owner + A |
| Error budget | Not agreed | Numeric normal-workload allowance, population and missing-result policy; deliberate faults reported separately | Owner |
| Sustained workload | Prior proposal:30 warm requests/at least60min | Approve duration/count/wall-clock cap, shape, cold observations, source questions, inference/guard budgets and resource sampling | Owner + F/G |
| Latency/deadline | Warm execution p95<=120s; execution target<=180s | Separate enqueue/start/terminal, queue/execution/user wait and cleanup; five-second process join is not proven strict terminal bound | Owner + A/D/F |
| Branch/call budget | Contract caps:1–5 tasks, retrieval1–2, model1, parent main calls4 | Confirm shared accounting, required/optional policy and no per-branch budget multiplication; parent-local serialization is not a host-wide GPU broker. Declare other inference clients/loads or isolate the measurement window; NeMo internal work separately bounded/reported | Owner + A/C |
| Rollback/acceptance | No named qualified target | Known-good artifact/config, history preservation, exact restoration procedure and residual-risk signoff | Owner + F |

Record each decision as pending/proposed/accepted with approver, date and evidence reference. Planning defaults are never silently promoted to owner decisions. Changes to public APIs, hosting architecture, persistence model or dependency versions require separate reviewed migration proposals.

Only after technical and quality gates pass and these decisions are accepted should G/F freeze an exact exercise: artifact, target, identity/grants, workload, call/time/spend budgets, authorized fault impact, stop/abort conditions, restoration/rollback steps and evidence paths. Require a direct grant for execution. Security/integrity/critical quality failures stop work; insufficient samples or unobserved delivery/cancellation remain unqualified.
