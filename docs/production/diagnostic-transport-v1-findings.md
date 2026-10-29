# r06 transport-v1 result — 29 October 2026

**Source/completeness gate failed; allowance closed.** The newly authorized lightweight mapper completed once, parsed and passed the then-current v1.51 engine validation. It selected both requested count passages but falsely classified them as conflicting. The conditional r06 workflow did not start. There was no retry, NeMo, Ragas, hosted inference, twenty-case run, approval or export.

| Layer | Actual result |
|---|---|
| Transport and process | Completed; model identity checked before/after; no timeout; terminal response retained |
| Parsing and engine validation | Passed under the recorded v1.51 generator; this did not establish semantic correctness |
| Evidence selection | FDI-share and leading-source passages selected; both Singapore/China project-count passages selected |
| Source/completeness | **Failed:** the requested project comparison was labeled `conflicting` with an empty answer, despite consistent counts for different entities |
| Full draft / guardrails | Not run because the mapper source gate failed |
| Owner acceptance | No new draft to adjudicate; no repeated owner scoring requested for this failed development mapping |

## Retained response and source check

The mapper answered `73%` for FDI's share of total 2024 application value and `Singapore` for the leading source by value. Their selected spans establish the percentage denominator and Singapore's value of 357.5 billion baht / 43% of FDI applications. These terse mapper answers are not a final reviewed brief.

For the third component it selected `s_a403e15f7eb38d5f` from `BOI_2024:unit:1:2` (Singapore: 305 projects) and `s_235e6b4a789691ac` from `BOI_2024:unit:1:3` (China: 810 projects), then returned `status: conflicting`, `short_answer: ""`. Both passages are from the pinned BOI release, zero-based page index 1 / PDF page 2. China has more projects than Singapore; differing values for different entities are the requested comparison, not contradictory observations. The selected China passage's “second largest” refers to application value, not the count ranking. Source: [BOI release, 13 January 2025](https://osos.boi.go.th/article_attach/PR4_2568EN.pdf), frozen local snapshot.

## Timing, usage and diagnosis

The complete two-phase diagnostic took 20.984 seconds: service child 16.328 seconds, separate offline engine validation 4.453 seconds, plus orchestration. Native metadata reports 9.702 seconds total service duration, including 5.329 seconds loading, 1.200 seconds prompt evaluation and 3.143 seconds generation. Known usage: 2,496 input + 142 output = 2,638 tokens; finish reason `stop`. This is one observed request, not a sustained latency benchmark or a matched improvement comparison with the earlier timeout.

The lighter worker retained the response, NDJSON, stages, finish metadata and usage. It solved the diagnostic's observability problem for this successful request, not general service/cancellation qualification. Backend cancellation was not exercised. The former timeout remains separately retained.

The confirmed validation gap is that `_entity_comparison.validate_mapping_comparisons()` skipped `conflicting` components. A model-generated false-conflict state therefore bypassed the literal count-consistency check. Correctly retrieved and selected evidence rules out a retrieval omission in this attempt. There is no output-limit truncation or GPU error in the retained response, and no basis for attributing this specific failure to hardware capacity or an inherent open-source-model limitation.

## Next action and preservation

The [v1.52 repair](false-conflict-repair-2026-10-29.md) rejects this unsupported literal-conflict state without rewriting it into an answer, preserves genuinely ambiguous contexts, clarifies the mapper instruction and extends elliptical-comparison checks. It needs new actual-model evidence under a [new bounded protocol](diagnostic-proposal-v152.md); unused allowance from transport-v1 is closed.

Ignored evidence is under `reports/workflow_pilot/production-readiness-2026-10-27/resume-v11/`: direct authorization, frozen input/request, `mapper-only-r06-transport-v1/{service,validation,summary.json,source-gate.json}`, and `actual-diagnostic-result.json`. All 266 source-manifest hashes and 207 pre-run evidence hashes matched immediately after the attempt. Original judgments, corpus, dependencies and approved exports were preserved. New outputs remain assistant-assessed development evidence, not owner acceptance or production proof.
