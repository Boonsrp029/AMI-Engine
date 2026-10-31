# Allowlisted logging in the supported launcher

## Confirmed leak and repair

An actual localhost process using the supported launcher and a synthetic storage failure returned a generic HTTP 500, but the default Uvicorn error logger emitted the private exception message and raw traceback. Disabling access logs did not prevent error-log disclosure. The probe used an isolated synthetic database, a fixed local corpus and a fake engine with no model method; no owner data, credentials or inference were involved.

`python -m src.pilot.launch` now supplies a structured formatter for Uvicorn server records and asyncio warnings/errors. It emits a UTC timestamp, fixed severity/source/event labels and an allowlisted exception category when available. It never formats raw message arguments, exception messages, tracebacks, stack info, local variables, filenames, paths or arbitrary extra fields. Unknown messages/categories produce generic fixed labels. Access logging remains disabled; single-worker, host/port and event-loop behavior are unchanged.

This intentionally changes the supported launcher's server-console format for privacy. It does not change research outputs, request/response schemas, existing event/artifact formats, historical logs, prompts, retrieval, model settings, dependencies or MLflow/evaluation entry points. It does not install a root logger or change evaluation logging through this module's import.

## Operator interpretation

Records use `ami-server-event-v1`. Known startup/shutdown messages produce lifecycle codes. Unexpected ASGI errors produce `request_failed`, preserving an allowlisted category such as `RuntimeError` without its message. Other warning/error records retain severity with `server_warning` / `server_error`; an unknown exception is labeled `Exception`.

On an error, retain the event timestamp/code/category, check truthful readiness and inspect the authorized task history. Readiness is metadata about dependencies/storage/runtime, not a quality verdict. Reproduce unexplained failures with synthetic material before enabling any additional debugging. Do not restore raw provider bodies or request traces to shared logs as a diagnostic shortcut. Incident ownership, routing, alerts, log collection/access and retention still require target-specific configuration.

## Evidence and scope limits

The before/after native probe exercised the same synthetic failure through the actual Windows launcher. Both responses remained generic HTTP 500. Before the repair, the server log contained the synthetic private message and traceback; after, neither was present and a structured `request_failed` event with `RuntimeError` remained. Each probe was terminal after its parent cleaned up only that probe's own process. This is a controlled teardown, not a graceful-shutdown or outage-recovery measurement.

Fourteen targeted formatter/launcher tests passed, including unsafe message/argument/exception/extra-field handling, custom names, hostile stringification, severity/lifecycle preservation and launch configuration. Separate full-suite and local container results are retained in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v20/`.

Integrated results: **954 Windows passed / 953 Linux passed, one skipped**, 15 existing warnings per platform. Linux ran with networking disabled and current application/config hashes verified against the local source-overlay image. Actual container startup, readiness, validation-response redaction and restart/restoration checks pass; all four cached exports retain their hashes, the original backup remains unchanged and disposable storage is removed. These checks made no model/NeMo calls or new human decisions.

The guarantee is limited to records routed through the supported launcher's configured Uvicorn/asyncio handlers. Direct `uvicorn src.pilot.api:create_app --factory` bypasses this configuration. Third-party/root loggers, Python warnings, direct stdout/stderr writes, reverse proxies, host logs and retained research/review data are not covered by this formatter. Its code is not a substitute for target-level secret handling, logging/access/retention policy or injection qualification. Historical evidence is preserved, not rewritten.

No factual manual scoring is required for the synthetic technical checks. Owner source/wording adjudication of the earlier composer response, exact-revision approval before export, independent reviewer usefulness and rollout acceptance remain separate human checkpoints. No alerts are sent automatically.
