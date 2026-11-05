# Concurrent qualification protocol v1 — preparation

Scope: one analyst request with bounded concurrent read-only subtasks. Keep sequential default, strict evidence validation and exact-revision approval/export controls. No concurrent complete-user-request expansion is authorized by this protocol.

## Ordered gates

| Gate | Evidence needed | Current disposition |
|---|---|---|
| Q0 Evidence freeze | Source revision/dirty manifest, image, environment, contract, model/settings, corpus/index, grant scope and assessment protocol | Pending exact integrated freeze |
| Q1 Engineering | A–F integrated tests and source-matched image, dependency consistency, sequential compatibility, branch overlap/caps, required/optional failure, cancellation/restart and review/export races | G verified A v6 selected source hashes/process/logs (1,440 Windows/1,439 Linux+1skip). Full intended reviewer-facing/release coverage remains partial |
| Q2 Actual answer quality | Authorized bounded development diagnostics, then predeclared fresh source-backed qualification; raw/fallback/editorial results distinct | Unmet; prior v1.68 failure retained; generation held |
| Q3 Independent usefulness | Owner-arranged actual sessions, task completion/timing/edits/unsupported/omitted facts and progress feedback | Owner confirmed no sessions arranged (5 November 2026) |
| Q4 Feedback improvement | Trace real independent finding to one implementation change and repeat affected checks | Pending Q3 |
| Q5 Operational authorization | Accepted decisions and exact named-target exercise after technical/quality gates | Pending; only decision worksheet prepared |
| Q6 Target operation | Actual security, data/model/serving identity, outages, saturation, cancellation, scheduled backup/restore, alert delivery/ack, rollback and sustained load | No qualifying target evidence |
| Q7 Residual-risk acceptance | Owner signoff referencing current evidence and scope | Pending owner action |

Q1 fixed responses do not satisfy Q2. Owner factual acceptance does not satisfy Q3. Local results do not qualify Databricks. Full qualification requires all applicable gates; preparation or pilot milestones cannot complete this Goal.

Retain existing numerical answer-quality thresholds unless explicitly revised:9/10 answerable,2/2 partial,4/4 missing,2/2 conflict,2/2 injection and zero critical unsupported/wrong-scope/date/unit/scenario claims. They are acceptance targets, not achieved scores. Reconcile scenario/denominator requirements with the frozen protocol. r07 is consumed; preserve remaining reserved facts and freeze any replacement/pool before future tuning/generation. Old inference grants are closed. A new protocol needs a purpose, case roster, model/guard/cost/time limits, stop rules and applicable direct grant; no authorization is supplied here.

## Evidence retention

Use a new ignored reports/qualification/<experiment-id>/ directory, with immutable inputs/raw outputs and separately versioned assessments. Retain contract/source/corpus/image hashes, authorization, per-parent/per-branch identities/events, process outcomes, timings, call/usage accounting, failures/unattempted cases, source findings, human records, deviations and final verdict. Parent and branch rates/latencies have distinct denominators. Do not expose credentials or raw participant identities in shared reports.

Measure submit/enqueue/start/terminal via monotonic observations, recording wall-clock provenance separately. Report all request outcomes; do not drop failures or missing telemetry. For complete measured populations, nearest-rank p95 is sorted element ceil(.95*n), one-based. Successful-only and all-terminal summaries must be labelled with denominators; unresolved requests/missing timing prevent a full SLO pass. Cold start/queue wait are separate from warm execution. Overlapping branch durations cannot be summed into parent elapsed time. Unknown NeMo usage, energy and monetary costs remain unknown.

G checks technical evidence structure, identities, lineage, calculations and preservation. Humans supply actual consent, factual/wording judgments, independent task observations and rollout acceptance. Exact stored-revision approval remains in the application. No CSV or JSON finding authorizes export.

## Maintenance

Refresh evidence matrix on an upstream revision, new run, reviewer finding, feedback change or owner decision. Append a dated change record; preserve former findings. Invalidate affected gates when identities/contracts change rather than carrying green results forward. If upstream files change during inspection, mark the snapshot provisional. Send no invitations/alerts and run no live exercise automatically.
