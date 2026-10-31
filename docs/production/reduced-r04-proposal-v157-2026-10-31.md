# Proposed reduced r04 diagnostic — v1.57

**Prepared, not executed; a new direct grant is required.** The v1.55 three-case allowance closed at r04's first failure. The subsequent supported-gap and literal-direction repairs passed 1,070 Windows / 1,069 Linux tests, one platform-specific skip, and recovery checks, but no real-model quality check has run on v1.57.

## Frozen scope and budget

Use the consumed r04 question and pinned v2 corpus. The mapper-only phase replays the retained two tool turns through actual current retrieval/preparation. It freezes the exact current schema/messages and makes no new planning calls. It does not inject a reference answer into the model request.

1. **One local mapper request:** 95 seconds total, with at most 60 seconds for the lightweight service worker, 30 for offline engine validation and five for orchestration. Preserve raw response, parsing, finish reason, usage and errors. No composition or NeMo in this phase.
2. **Only if technical and assistant source/completeness checks pass:** one full r04 workflow, at most 180 seconds and four main calls plus one NeMo invocation. A hash-bound source gate is required; transition is not automatic.

Combined ceiling: **five main-model calls and one NeMo invocation**, one attempt per phase. Stop at the first technical/source/completeness failure and close unused allowance. No retries, warmup inference, tuning during the run, other cases, Ragas, hosted inference, twenty-case evaluation, approval/export, commit/push, deployment or reviewer contact.

The model remains `ami-llama3.1:8b-4k`, digest `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`, context 4096, completion limit 900 and temperature zero. Prompt/workflow version is `analyst-pilot-v1.57`, mapping `requested-evidence-v38`. Frozen mapper `as_of` is 2026-10-31; a conditional full workflow records its actual date. This absolute historical question is a diagnostic, not a matched latency comparison.

Contract SHA256: `dfbe703d0af2fe260c3b5c6800fb3e7e819384fced1452616493d2aa7f1dcb12`.

The ignored local proposal is `reports/workflow_pilot/production-readiness-2026-10-27/resume-v47/diagnostic-proposal-v157/`. It binds the generator, model, package/source files, original failed attempt, capture helper, conditional runner, native request, expected identity and fixed fixtures. Altered code or input invalidates it. Execution output directories and authorization file are absent.

## Acceptance before further spending

- Both requested comparison slots must be correctly mapped, with empty supported gaps and known span identifiers.
- The monthly aggregate must remain stable after seasonal adjustment. Preserve machinery/equipment and vehicle increases, construction decline and its permitted-area cause, with supported activities rather than one-word direction labels alone.
- The quarterly answer must retain declines in vehicle and construction investment, without substituting monthly movements.
- Source selection and interpretation must both support the requested measure and period. No invented quantity, forecast substitution or unsupported geographical claim is accepted. Unknown machine geography and unhelpful warnings remain explicit review limitations, not silently waived.
- A conditional final draft must retain both periods, supported categories/causes and resolving citations, and pass the existing final NeMo check. Schema success or NeMo alone is insufficient.

If a mapper answer is terse or contradictory despite valid selected spans, report that failure instead of treating a future composer or editorial correction as proof it passed this preflight.

## Offline evidence and limits

Fixed-response checks passed the manually authored valid fixture and rejected both the wrong-aggregate fixture and original invalid-gap response. SDK/native JSON request values match using mocked HTTP only. Both execution entry points reject a missing authorization before creating run outputs. A synthetic service response passed actual engine validation in a separately supervised offline child within the 30-second limit (about 2.53 seconds here). This is not a guarantee under every host condition.

The initial direct validation harness omitted its required output directory and failed before engine validation. The harness setup was corrected using the existing supervisor; no application/transport code was changed. Both plumbing and scope checks are retained under `resume-v47/`. There were zero model/NeMo calls, no authorization record and no real diagnostic outputs.

Backend cancellation and NeMo internal token usage remain incompletely measured. A timeout closes the allowance and requires diagnosis; do not infer cancellation or zero usage. Conditional workflow controls retain actual process deadlines and record partial/unknown usage.

## Manual review

No human scoring is needed for schema or engineering failures. If a new complete draft passes technical/source checks, it needs owner source/wording adjudication before being called owner-accepted. Stored export still requires exact-revision human approval. The earlier r03 packet is separate; no duplicate scoring is requested by preparing this diagnostic.
