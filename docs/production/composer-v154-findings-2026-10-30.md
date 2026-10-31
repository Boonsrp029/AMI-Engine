# r06 v1.54 composer diagnostic — failed, 30 October 2026

**The composer-only diagnostic failed. Its conditional full workflow did not run, and the generation allowance is closed.** The owner explicitly authorized the [frozen proposal](composer-diagnostic-v154-2026-10-30.md). The code, schema, model digest and source package matched the declared identities before execution. Historical responses, editorial judgments and the successful focused CI publication remain separate evidence.

## Actual result and bounded work

| Stage | Evidence |
|---|---|
| Transport | Completed one local request; model identity verified before/after; finish reason `stop` |
| JSON/schema parsing | Passed; three composed claims parsed |
| Composition validation | Failed with `ValueError`: `Draft project comparison omits or swaps requested entity/count facts` |
| Source/completeness assessment | Failed: the comparison omitted both counts and asserted the wrong winner |
| Conditional full workflow | Not started; its output directory remains absent |
| NeMo | Zero invocations; no safety verdict is claimed |
| Owner acceptance / stored approval / export | None created; no factual scoring requested for the technical rejection |

Exactly **one** main model call used **960 input + 140 output = 1,100 known tokens**. The service phase took 23.375 seconds, offline validation 25.109 seconds, and the complete diagnostic 49.594 seconds, within the 60/30/95-second limits. The model reported about 13.229 seconds of loading within about 16.947 seconds of service work. These are single-attempt measurements, not a sustained or warm-latency benchmark. No retries, Ragas, hosted inference, additional workflow or twenty-case run occurred. The remaining four-call ceiling cannot be reused after this failure.

## Claim assessment against pinned evidence

The consumed question requests FDI's share of 2024 application value, the source leading by value, and whether Singapore or China had more projects, with clear percentage denominators. Sources are the unchanged BOI release published 13 January 2025, units `BOI_2024:unit:1:2` and `BOI_2024:unit:1:3`, PDF index 1 / reader-facing PDF page 2.

| Component | Raw result | Assistant finding |
|---|---|---|
| Share of total application value | Correctly states FDI represented 73% in 2024 | Supported; the 73% share is distinct from 25% year-on-year growth |
| Leading source by value | Names Singapore and retains 357.5 billion baht / 43% context, plus 305 projects | The selected evidence supports these figures; a final projected draft was not accepted |
| Project-count comparison | Says Singapore had more projects than China, without either count | Contradicted: evidence assigns Singapore 305 and China 810. China has more projects; the numerical difference is 505, a direct calculation rather than a model/source quotation |

Application values are not realized investment. The source's FDI ranking and project-count comparison are different measures. The raw response's wrong conclusion is consistent with conflating nearby ranking language with counts, but the model's internal reason cannot be established from its output.

## Diagnosis and protection behavior

One **offline fixed-response replay**, making zero model/NeMo calls, reproduced the same composition exception. The count-preservation check runs before winner validation and rejected the missing operands. Independent source inspection additionally establishes that the stated winner is wrong. This is not credited as a successful answer or repaired after the fact.

There was no observed transport timeout, context/completion exhaustion, malformed JSON or model-identity mismatch: the request completed normally with 960 recorded input and 140 output tokens against the pinned 4,096-context / 900-completion settings. No GPU-memory error was recorded. Those observations do not prove hardware can never constrain another request, nor establish an inherent open-source-model limitation. No paid model switch is justified by this single diagnostic alone.

The validator protected the output boundary: no final public `Draft` was returned and the final NeMo stage was not entered. This demonstrates rejection of this bad composition, not reliable generation or complete safety qualification. The unchanged earlier editorial acceptance does not approve the new raw output.

## Next engineering action and human checkpoints

Before seeking another generation budget, prepare an offline change that stops relying on free-form composition to infer recognized literal count comparisons. Use only validated, same-period source operands and keep measure/identity distinctions explicit. Evaluate a small deterministic rendering path for this narrow operation; preserve rejection or unresolved status for ambiguous counts, inconsistent periods, wrong measures, unsupported scope and malicious text. Do not silently turn an incorrect model claim into an accepted answer. This proposed functional change is not implemented in this diagnostic pass.

Validate independent synthetic entities/counts and saved failure replay before proposing new model calls. Keep the public schema, four-call ceiling, source citations and final safety/approval controls; declare any change in composition responsibilities explicitly. Do not hardcode BOI figures, tune against fresh held-out facts or claim general semantic correctness from these checks.

**Manual review now:** none required for this rejected technical output. A future assessable generated draft still needs owner source/completeness review before owner acceptance, and approval of the exact stored revision before export. Independent reviewer usefulness remains pending.

Raw response/stream, parsed fields, timings, usage, source locators and failed hash-tied source gate are under ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v23/composer-only-r06-v154/`. Authorization, pre-run preservation snapshot, zero-call cause replay, assessment and budget closure are separately retained in `resume-v27/`. No application/API/prompt/schema/library/source/owner-history changes were made. No commit, push, deployment or reviewer contact occurred.

The full Goal remains incomplete. The [focused CI fix is green](ci-publication-2026-10-30.md); fresh quality, the intended newer release revision's remote CI, independent use and operational/Databricks qualification remain open.
