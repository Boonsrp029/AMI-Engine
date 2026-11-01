# Financial span boundary repair — 1 November 2026

This is an offline engineering pass after the [consumed v1.60 failure](consumed-v160-findings-2026-11-01.md). It repairs source-span boundaries, not the full financial-comparison workflow. No new model or NeMo calls are authorized or performed by this pass.

## Behavior and change

Previously the source catalog split at every period followed by whitespace. In retained r05 evidence, this ended a financial quote at an approximation abbreviation and separated its currency and sector continuation. Both pieces existed in the retrieved source; the mapper selected only the first.

The span builder now recognizes the explicit abbreviations `ca.`, `approx.`, `e.g.` and `i.e.` as continuations within a paragraph. It retains exact source substrings, Python character offsets and content-bound span IDs. Ordinary punctuation and unknown abbreviations retain their prior behavior. The existing 600-character quote limit remains authoritative, so long sentences can still require multiple selections. No records are joined and no text is inferred, normalized or added to quotations.

Runtime identity is **v1.61 / mapping v41**, distinguishing the changed catalog from v1.60. The wire remains `source-selection-v1`. Public APIs, legacy schema, graph, model/settings, dependency versions, retrieval ranking, approval controls and cached exports retain their contracts. The existing Docker Desktop service is not automatically replaced by this validation image.

## Evidence and limits

Six of sixteen new synthetic tests failed before the repair. Tests cover abbreviation continuations, punctuation, paragraph boundaries, unknown abbreviations, Unicode, exact offsets, stable identity, distinct source records, long spans and application extract resolution. The final targeted set passed 78 tests.

An offline replay of r05's retained retrieved record now produces a single exact **520-character** span containing its baht value, USD equivalent and sector explanation. This is a catalog replay, not new selection, composition, model-quality evidence or owner acceptance. The original failed attempt and its hash-bound gate remain unchanged.

The first full suites exposed six stale prompt-version assertions; those assertions were updated for the intentional identity change. Windows additionally recorded a synthetic next-job deadline failure while the suites ran concurrently. The recorded worker exceeded its two-second test deadline. The targeted recovery checks and final serial suites passed without changing runtime deadlines or weakening assertions. Final Windows result: **1,154 passed, 15 warnings**; Linux: **1,153 passed, one skipped, 15 warnings**. `pip check` found no broken requirements. Container restart/recovery passed; four cached approved exports remained byte-identical, and the source backup remained unchanged. No new human review decisions were created.

Local evidence: `reports/workflow_pilot/production-readiness-2026-10-27/resume-v75/`. Failed runs are retained beside final checks. The source-only image uses existing installed dependencies; it is not evidence of a fresh package installation or remote CI.

## Remaining work and human review

The r05 quality gate remains failed. Complete requested current/base-year evidence selection and retention of selected financial comparison facts still require repair. Do not calculate a missing baseline from rounded growth, silently insert unselected evidence, or count this span replay as a corrected generated answer. A source span satisfying multiple roles must not be required twice by the decoder.

No human review is required for synthetic boundary checks. The new r03 exact-output semantic/wording review remains pending separately; no prior acceptance transfers to it. Stored draft approval/export and independent reviewer usefulness remain separate human checkpoints. Fresh quality and actual production qualification remain incomplete under the full [Goal](../production-readiness-goal.md).
