# D integration suite â€” implementation checkpoint

D owns tests/integration/subtasks/test_subtasks_execution_integration.py. No A runtime/store/persistence source is edited by D. Generation remains held; workers are deterministic and databases are temporary.

The suite joins real run_plan, AttemptSink and Store. Event-gated workers cover actual overlap/caps1and2, reversed completion with stable aggregation, durable dependency ordering, required/optional failures, cancelled/recovered stale attempts, duplicate submissions, deadline-boundary completion, corpus mismatch, review/edit races and cached export invalidation.

Initial run:7passed/3failed. One failure was an invalid too-short synthetic request key, corrected without altering production validation. Two contract failures are reported to A through this artifact:

1. AttemptSink writes repeated identical Progress deliveries twice. Contract requires durable idempotency.
2. AttemptSink accepts running after a completed child and progress_view shows the reopened state. Contract forbids terminal transitions.

Keep these assertions failing until the A-owned adapter enforces deduplication and state/ordinal/child-attempt checks transactionally. Do not xfail, skip or weaken them. D does not change shared persistence source while A owns it.

Remaining D work: controlled process termination/restart, queued cancellation in new path, uncooperative-thread containment, publication/transaction linearization windows, sink failures, aggregate collisions and C-boundary integration. Existing sequential owner-death/fencing tests remain regressions and do not alone prove the new integrated path.

Offline tests cannot prove real-model quality, server-side cancellation, GPU capacity, backend outage behavior or sustained latency/load. No synthetic guard is credited as a real NeMo pass. Model runs, deployment, reviewer sessions and publication require their separate grants.


## Expanded executable evidence

The expanded scheduler/persistence/recovery run completed16passed/2failed140.44sec. A separate C-boundary run passed5tests70.22sec. These are separate snapshots, not a single green combined run. New coverage includes actual spawned coordinator termination/recovery/explicit retry with preserved cached approved history, queued branch cancellation, sink outage, cross-branch source collision, C numeric/source binding rejection, actual guard-callback rejection and cancellation inside the guard before publication. All callbacks are fixed synthetic code; no real NeMo or model is invoked.

A added runner.run_stored_plan while D was working. Next D pass must connect its owned-process execution boundary to the D fixtures and include explicit retry/late publication and model-access bounds. Existing A runner module tests complement but do not replace D cross-component checks. The full offline suite remains in progress; source drift is recorded because A–C are evolving concurrently. A revision-consistent full-suite pass is still required.
