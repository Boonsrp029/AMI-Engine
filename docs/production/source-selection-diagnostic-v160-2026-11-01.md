# Proposed source-selection diagnostic — r04 / v1.60

**Prepared, not executed. A new inference grant is required.** The owner approved the [selection-only contract migration](source-selection-migration-2026-11-01.md) for offline implementation only. Working Docker, metadata readiness and that design choice do not authorize generation. The original v1.58 diagnostic remains failed under its original contract.

## New prospective target

Test whether the unchanged local model can produce the new `source-selection-v1` wire and select relevant, complete evidence. Application-authored extracts must retain the selected facts with valid provenance. This replaces the mapper's model-written-paraphrase obligation **prospectively**, not the requested factual coverage or the final draft quality thresholds.

Use consumed r04 and the pinned v2 corpus. The mapper-only phase replays two retained tool turns through actual current retrieval/preparation, freezing current schema/messages. No reference answer or prototype extract is inserted into the model request. This is a development diagnostic, not an unseen case or matched before/after benchmark.

## Scope and budget

1. **One local mapper request**, 95 seconds overall: at most 60 service, 30 offline engine validation and five orchestration. Preserve raw output, parsing, finish reason, selected evidence, application-extract provenance, usage, timing and errors. No composition or NeMo in this phase.
2. **Only if technical, source-support and completeness checks all pass:** one full r04 workflow, at most 180 seconds, four main-model calls and one final NeMo invocation. A hash-bound assistant source gate is required before transition; it is not automatic.

Combined ceiling: **five main-model calls and one NeMo invocation**, once per phase. Stop at the first failure and close unused allowance. No retries, warmup inference, prompt tuning during the batch, other cases, Ragas, hosted inference, twenty-case run, approval/export, publication, deployment or reviewer contact. Partial usage/cancellation remains unknown on timeout, not assumed zero. NeMo internal usage remains separately reported and incompletely measured.

The model remains `ami-llama3.1:8b-4k`, digest `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`, context 4096, completion limit 900 and temperature zero. Workflow is `analyst-pilot-v1.60`, mapping `requested-evidence-v40`, generator `3478741b789fe359b6a84f4a970e30893a33254115c3abaaf11d9b38394f4d01`.

Frozen mapper `as_of` is intentionally 2026-10-31 for this absolute historical question. A conditional full workflow records its actual date. No latency generalization follows from one run.

## Acceptance

- Strict new-wire parsing: correct version, all canonical components, valid states/gaps and selected span IDs, with no model-written answer field.
- Every application extract must resolve original source hashes/offsets, preserve all selected quotations without truncation and fit the unchanged 800-character bound. Its application authorship must be explicit. Provenance alone is not factual support.
- Monthly evidence/extracts must establish a stable seasonally adjusted aggregate, increased machinery/equipment and vehicle investment, declining construction and the permitted-area explanation, with the requested supporting activities.
- Quarterly evidence/extracts must retain declining vehicle and construction investment without substituting monthly movements or another measure.
- Assistant source review must confirm relevance and requested-fact coverage. Unknown geography remains explicit; it is not inferred from the question or silently waived.
- A conditional final draft must preserve both periods and supported categories/causes, resolve citations and pass final NeMo. Schema or NeMo success alone is insufficient. Owner source/wording acceptance remains separate.

## Concrete preparation and offline checks

The ignored proposal is `reports/workflow_pilot/production-readiness-2026-10-27/resume-v65/diagnostic-proposal-v160/`. The contract binds the current compiler, generator, model/package/source identity, new-wire schema/messages, native request, retained failures and both private execution helpers.

Contract SHA256: `72999b5ea4286f2b4eb7fcffa63f7e3d25127b0df2f6758c36ad68b792b45a4b`.

A hand-authored valid new-wire fixture reaches application extraction. Legacy wire, unknown span, wrong comparison evidence, missing status and invalid supported-gap fixtures are rejected. SDK/native request values match under mocked HTTP; no real request is sent. Both execution entry points reject absent authorization before creating real-run output directories. A clearly labeled synthetic service response passed the separately supervised actual engine-validation child in about 2.55 seconds, within 30 seconds. This is not a guarantee under every host condition or real-model quality evidence.

The initial dependent inspection ran before the original freeze process completed and could not find its contract file. The original process was awaited to terminal success, then its existing artifacts were checked without regenerating them. This preparation-order error occurred before any inference or runtime change and is retained in the local evidence.

The runtime remains unchanged from the v1.60 full offline checkpoint (1,133 Windows / 1,132 Linux tests plus one platform skip, 15 warnings each). The subsequent host startup repair has five separate targeted tests. Preparing this protocol does not repeat unchanged full suites.

## Human checkpoint

Reply **Authorize reduced r04 v1.60 diagnostic** to grant only this run. Engineering failures need no repeated human scoring. New assessable final drafts require owner factual-support and wording review; stored export still requires exact-revision approval. Independent reviewer usefulness and the full production qualification remain incomplete.
