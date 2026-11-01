# Proposed reduced r04 diagnostic — v1.58

**Prepared, not executed. A new direct grant is required.** The v1.57 diagnostic failed and its whole allowance closed. The [v1.58 contract alignment](mapper-answer-order-2026-11-01.md) passes offline checks but has no real-model quality evidence.

## Scope and budget

Use the consumed r04 historical question and pinned v2 corpus with unchanged model digest, context 4096, completion limit 900 and temperature zero. Replay the two retained tool turns through current retrieval/preparation for the mapper-only phase. References and manually authored expected answers are not inserted into the model request.

1. One local mapper request, **95 seconds overall**: at most 60 for the service, 30 for offline engine validation and five for orchestration.
2. Only if technical, source-support **and completeness** checks all pass: one full r04 workflow, **180 seconds maximum**, with at most four main-model calls and one final NeMo invocation. The assistant must record a hash-bound source gate before this transition; it is not automatic.

Combined maximum: **five main-model calls and one NeMo invocation**, once per phase. Stop at the first failure and close unused allowance. No retries, warmup inference, tuning during the batch, other cases, Ragas, hosted inference, twenty-case run, approval/export, publication, deployment or reviewer contact. Unknown partial usage/cancellation stays unknown on timeout, never assumed zero.

Model: `ami-llama3.1:8b-4k`; digest `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`. Generator: `53ccabc6be7b8c0f57c6cd782aedf1286b182dc66245b5f4f6ce7e485b104891`. Workflow `analyst-pilot-v1.58`, mapping `requested-evidence-v39`.

The mapper's frozen `as_of` remains 2026-10-31 intentionally for this absolute historical question. A conditional full workflow records its actual execution date. This is not a matched latency or unseen qualification experiment.

## Acceptance — unchanged substantive gate

- Both canonical comparison requests must be mapped, with valid selected spans and empty supported gaps.
- The monthly aggregate must be stable after seasonal adjustment. Retain the supported machinery/equipment and vehicle increases, the construction decline and permitted-area explanation, and requested supporting activities. A correct one-word direction is insufficient.
- The quarterly answer must retain falling vehicle and construction investment without substituting monthly movements.
- Directions, periods, measures and selected evidence must agree. Correct source selection alone is insufficient. Unsupported geography, observation/forecast substitutions and invented quantities fail the gate. Unknown geography remains an explicit limitation, not silently waived.
- A conditional final draft must preserve the two periods and supported explanations, resolve citations, and pass the existing final safety check. Parsing or NeMo success alone cannot establish answer quality.

## Concrete artifacts and offline verification

The ignored proposal is `reports/workflow_pilot/production-readiness-2026-10-27/resume-v55/diagnostic-proposal-v158/`. Its contract binds the actual schema/messages, native request, generator/model/package identity, source files, retained failure, transport and both private execution helpers.

Contract SHA256: `2f06006b1cfd43afa13af1a3f347810fcf41312da46380ffa244abd40ae46368`.

Authorization and both real output directories are absent. The earlier v1.57 authorization is not reused. Installed SDK request values equal the native diagnostic request under mocked HTTP. Hand-authored positive/negative fixtures passed or failed the intended engine gates. A clearly labeled synthetic service response passed the separately supervised offline validation process in about 2.52 seconds, within 30 seconds. Both execution entry points reject absent authorization before creating real-run output directories. These are plumbing checks, not model-quality evidence or guarantees under every host condition.

Application code is unchanged from the 1,075-test Windows / 1,074-test Linux offline checkpoint; the latter has one platform skip. Preparing this protocol does not require repeating those unchanged suites. No inference occurred in preparation.

## Human checkpoint

Reply **Authorize reduced r04 v1.58 diagnostic** to grant only this budget. Technical failures need no repeated human scoring. A new assessable draft needs owner source-support and wording review before owner acceptance, and exact stored-revision approval remains separate before export. Independent usefulness and production qualification remain pending.
