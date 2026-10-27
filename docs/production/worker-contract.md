# Owned worker execution contract

Implementation pass: keep the LangGraph/NeMo workflow, public draft/review contracts, dependency versions and SQLite schema. Replace the default analyst application's thread execution with one owned child process. Existing injected test engines and explicit inline tests retain their controlled execution path and are not evidence of production deadlines.

- One application instance owns the database's OS runtime lock. It acquires the lock before startup recovery; a second instance must fail before modifying task state.
- SQLite remains the authoritative two-slot waiting queue. The dispatcher polls it; no unbounded in-memory submission queue is introduced. A claimed attempt gets a fresh identifier in existing event history.
- A 180-second monotonic deadline starts before process launch and includes imports, generation, composition, NeMo and native cleanup. Queue wait is measured separately.
- The child receives only the request, pinned corpus path/hash and its deadline. It cannot write review storage. It sends bounded structured events and one result; no raw provider errors or credentials enter API history.
- Parent persistence verifies the current attempt and running state within the write transaction. Cancellation, failure or retry prevents an earlier attempt from saving events/drafts. A result is not accepted until the child exits cleanly and corpus identity remains pinned.
- Active cancellation kills and reaps only the owned process. Queued cancellation interrupts the persisted task without model calls. Shutdown interrupts outstanding work; no automatic retry or approval occurs. A local watchdog exits if the owner process dies or its deadline expires.
- Additive `POST /api/runs/{id}/cancel` uses the existing local authorization boundary. Approved/completed drafts cannot be canceled into a retryable state. This is not a multi-user production identity design.
- Retain partial stage/usage observations on failure. In-flight model work and guardrail internal tokens remain unknown when interrupted. Terminating a client does not prove that an external inference server stopped computing; actual provider behavior requires separate live qualification.

Offline acceptance: synthetic successful/empty/failed jobs; model/policy-stage hangs; process exit after a candidate result; oversized/malformed messages; cancellation and duplicate retries; late-result fencing; changed corpora; restart/second-instance rejection; approval/export lifecycle. Use spawned synthetic workers, not new inference. Separate real deadline/process evidence from simulated policy quality.

The single-instance runtime is an implementation choice for the accepted small pilot, not a distributed queue or scaling claim. Deployment identity, alert delivery, sustained load and actual backend cancellation remain independent gates.
