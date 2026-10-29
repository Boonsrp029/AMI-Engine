# v1.51 mapper lifecycle timeout — 29 October 2026

**Technical gate failed; budget closed.** The owner authorized one r06 mapper call, followed only after technical/source checks passed by one full r06 workflow. The mapper process reached its invocation marker but exceeded the 60-second parent deadline. The parent killed its owned child and waited for exit. No complete response, parsed mapping, finish reason or token usage was retained; the conditional workflow never started. This is not a new source-quality assessment or evidence that the count repair succeeded or failed semantically.

## Retained evidence and diagnosis

`mapper-only-r06-v151/progress.json` records one mapper invocation marker and matches the frozen input/schema. `process-result.json` records timeout, return code 1, unknown in-flight usage and no attempt hash. There is no finalized `attempt.json`; no synthetic response or zero-token result was substituted. No NeMo, composer, Ragas, hosted inference or twenty-case run occurred. Unused allowance cannot fund a retry.

File timestamps place the progress marker approximately 23.76 seconds after the start marker and the process-result record 36.27 seconds later. Thus a substantial part of the declared process deadline elapsed before the invocation marker. These are approximate file-time boundaries, not instrumented monotonic stage measurements or a measure of server generation duration.

A separate **no-inference import probe** measured 20.04 seconds to import `src.pilot.engine`. It did not construct an engine/model or call NeMo. The probe is consistent with material framework startup cost but is a different, cached observation and does not reconstruct the failed worker. It cannot explain the remaining service delay by itself.

A read-only post-timeout `/api/ps` observation listed the expected model/digest resident in VRAM. Residency is not in-flight request status or cancellation proof. GPU memory/utilization was sampled afterward; it does not establish memory pressure during the failure. No completed service response or correlated server request ID establishes cold loading, queueing, schema compilation, GPU exhaustion or another backend cause. Do not attribute this timeout to inherent open-source-model incapacity or recommend larger hardware from this evidence.

## Next technical action

Instrument bootstrap, identity checks, input preparation, invocation and finalization with persisted monotonic stage timings. Keep the total process deadline explicit and retain a failure artifact before hard termination where possible. Do not silently increase the deadline or add a warm-up generation.

The existing mapper-only child imports the entire engine, including dependencies unnecessary for its single service call. Prepare a lightweight diagnostic transport using the already frozen actual-engine messages/schema and unchanged model options, with offline request-parity checks. Revalidate returned data through the actual engine before any workflow transition. Clearly declare preparation/validation versus timed service-process boundaries and obtain a new bounded grant before live use. This is a private diagnostic improvement; an application/framework migration or model change is not justified by the timeout.

Backend cancellation remains an operational qualification gap. A terminated client process and resident model list do not prove the server stopped the request. Do not restart the old attempt or kill a shared model service to conceal that uncertainty.

## Preserved result boundaries

The [offline repair](entity-count-coverage-2026-10-29.md) retains 826 Windows / 825 Linux tests plus one Windows-only skip, 15 existing warnings, clean dependency checks, and no-inference recovery. Code/model/settings/dependencies were unchanged during this attempt. The earlier [v1.50 r06 source failure](diagnostic-v150-findings.md) remains the actual evidence-selection failure; this timeout does not resolve it.

The [r05 owner adjudication](../pilot/owner-review-v150-2026-10-29.md) and separate owner-provided baht revision remain intact, with claim 2 unchanged and warnings waived only for that reviewed candidate. No stored approval/export was created. There is nothing new to ask the owner to score for r06 because no response is available.

The full Goal remains incomplete: actual quality, independent reviewer use, current remote CI, real container inference/cancellation, scoped security/operations/soak and authorized Databricks deployment/rollback remain open. Local passing tests and this one timeout are not production qualification.

## Local artifacts

Ignored directory `reports/workflow_pilot/production-readiness-2026-10-27/resume-v10/` retains the authorized final-v2 contract, mapper input/schema/progress, process result, empty stdout/stderr, timeout observation, GPU sample, import probe/profile and `mapper-only-r06-v151/summary.json`. Input/progress/process hashes and unavailable usage are explicit. The final mapper input matched its frozen contract; no report overwrote an original generated output or owner judgment.
