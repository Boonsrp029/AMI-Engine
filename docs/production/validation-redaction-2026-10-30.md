# Redact rejected input from validation responses

## Confirmed issue and scoped change

A synthetic localhost request containing an email-shaped question was correctly rejected with HTTP 422 and created no task. FastAPI's default validation response nevertheless returned the rejected value in `detail[].input` and included exception context. Extra-field errors also reflect user-provided field names through their locations. Blocking storage alone did not prevent reflection in an HTTP response or downstream response capture.

The application now handles `RequestValidationError` using a private formatter. It retains HTTP 422 and the `detail` list, with `type`, `loc` and `msg` entries. Messages and types come from fixed application allowlists. Locations retain known public field names and list indexes; unknown names become `field`. Rejected values, raw messages, exception context and arbitrary keys are omitted. Malformed JSON is handled through the same boundary.

This is an intentional security change to validation-error content: callers must not rely on the former `input` or `ctx` fields or dynamic Pydantic message text. Request schemas, accepted values, endpoints, authentication, successful responses, prompts, models, retrieval, review/export rules and dependency versions are unchanged. It does not require a framework migration.

## Validation and preservation

Eight new synthetic cases cover rejected email/number values, extra keys, invalid request keys, malformed JSON, nested/list locations, missing fields, authentication denial, exception context and objects that must never be stringified. The targeted set, including existing pilot behavior checks, passed **29 tests**. Invalid requests create no runs; no model or policy calls are made by the reproduction or new tests.

Full offline results: **920 Windows passed; 919 Linux passed, one skipped**, 15 existing warnings per platform. Linux used a network-disabled source overlay on the verified dependency image, with current application hashes checked before testing. The actual local container smoke passed validation-response redaction, non-root startup, unavailable-model readiness, interruption/restart recovery and all four cached-export hash checks. Its disposable volume was removed, and the original backup hash was unchanged. No model generation or new human decisions occurred.

Separate evidence is retained in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v18/`. `baseline-finding.json` records the pre-repair reflection without saving genuine personal data. The original owner records, source snapshots, frozen outputs and approved exports are protected by hashes.

The container smoke check now sends a synthetic rejected question and verifies its value is absent from the 422 response, then performs the existing startup, readiness, interruption/restart and cached-export checks. It uses a verified read-only backup and disposable storage. This does not create a new human approval or qualify actual model inference.

## Limits and human review

This repair covers request-validation HTTP responses. It is not evidence that all server/dependency logs, debug tooling, reverse proxies, host files or retained research/review content are free of personal or secret data. Access logs remain disabled in the supported launcher; production logging/retention/access controls still need target-specific review and qualification. Public-data-only use remains required.

No manual factual adjudication is needed for these synthetic technical checks. Owner source/wording review of the earlier composer output remains pending and separate. Exact-revision approval is still required before brief export; independent reviewer sessions and deployment rollout acceptance remain human checkpoints.
