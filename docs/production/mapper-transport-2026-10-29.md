# Mapper diagnostic transport and lifecycle repair — 29 October 2026

**Offline engineering only; actual v1.51 answer quality remains unassessed.** The authorized mapper attempt [timed out](diagnostic-v151-findings.md) without a retained response. That grant is closed and its conditional r06 workflow did not run. This pass prepares a new diagnostic; it does not repeat the failed request or change application inference.

## What changed

`scripts/_mapper_transport.py` is a private standard-library worker for one pinned localhost Ollama streaming request. It avoids importing the engine, LangChain and NeMo merely to send the frozen mapper messages/schema. Tests capture the installed ChatOllama/Ollama request using mocked HTTP and compare JSON values: model, system/user messages, native schema, streaming, tools and context/completion/temperature. This establishes request-body value parity, not identical HTTP bytes/headers or equivalent model outcomes.

The worker retains raw NDJSON and partial text; records monotonic bootstrap, identity, request, headers, first-byte/chunk and completion/failure boundaries; and preserves unavailable token counts as unknown. It checks the pinned model before and after completion, limits response size, uses a fixed loopback endpoint without proxies/redirects, and never retries inference. A parent supervises only its own child. Client termination still does **not** prove backend cancellation.

`scripts/pilot_mapper_check.py` checks hashes and a new protocol-specific human grant before service execution. A completed service response is replayed in a separate bounded child through the installed parser and actual engine validation, using fixed tool turns and no additional inference. Malformed output is not repaired or replaced. The controller cannot start the full workflow; a separately gated local runner requires a hash-tied assistant source/completeness assessment first. Empty usage and failed/partial records remain retained.

The app generator remains `23d988179285c6f760826724cb82a3a06087189a20337efb439f1b7128e43d72`: prompt v1.51, mapper v36, retrieval v3, model/digest, 4096 context, 900 completion, temperature zero, four workflow calls and final NeMo remain unchanged. Public APIs, SQLite, dependencies, source packages, owner judgments and approved exports are preserved.

## Offline evidence and limits

Focused tests cover SDK request parity, Unicode/chunk assembly, raw errors, truncation, size/deadline/identity failures, unknown usage, no redirects/retries, lightweight imports, owned-child timeout, locked publication, authorization/protocol drift, phase gating and fixed-response parser replay. The full Windows/Linux results and source-integrity hashes are retained in the separate local `resume-v11` evidence directory.

Fixed replay through the **actual saved r06 input** accepts a supported mapping and rejects explicit wrong-winner wording and a regional-base passage substituted for project counts. An earlier synthetic replay found that the elliptical phrase “Singapore had more” without the project noun passes the literal mapping check. Both records are retained. The check is not a general entailment guarantee; a source assessor must reject a wrong comparison regardless of phrasing. This limitation is recorded rather than silently changing the application identity during a transport pass.

No actual model, NeMo, Ragas or hosted generation is used for these checks. A green offline suite is neither a fresh model-quality result nor production qualification. Existing image recovery evidence remains a no-inference result; backend cancellation, service latency, container inference and soak remain unqualified.

## Proposed next budget — requires a new grant

The local frozen protocol is `reports/workflow_pilot/production-readiness-2026-10-27/resume-v11/diagnostic-proposal-transport-v1/contract.json`. Default inspection performs no inference. Its hash and the exact human reply must match before execution; the old grant cannot authorize it.

1. One r06 mapper call: **95 seconds total**, explicitly split into a service child of at most 60 seconds, a separate offline engine-validation child of at most 30 seconds, and five seconds reserved for orchestration. This is a new total, not a reinterpretation of the previous 60-second process allowance. No warm-up generation.
2. Only after transport, actual engine validation and source/completeness checks pass: one r06 workflow, at most 180 seconds, four main calls and one NeMo invocation.
3. Combined ceiling: five main calls and one NeMo invocation. Stop at the first technical or source failure. No retries, Ragas, hosted inference, twenty-case set, approval/export, deployment or reviewer contact. Backend cancellation remains unverified if a request times out.

Source checks require FDI's 73% denominator to remain total 2024 application value; Singapore's leading value of 357.5 billion baht/43% of FDI applications; correctly attributed Singapore 305 and China 810 project counts with China having more; and application figures distinguished from completed investment. Source selection, response correctness and completeness remain separate gates. The observed elliptical-comparison limitation receives explicit inspection.

## Human checkpoints

No owner scoring is required for the timeout or synthetic replay failures. A new explicit generation allowance is needed for the proposed diagnostic. If a new assessable output is produced, source support, completeness and usefulness need owner review before it is called owner-accepted; export still requires approval of the exact saved revision. Independent usefulness and production rollout acceptance remain separate later human checkpoints.
