# Actual v7 development diagnostic — first case passed, second failed

The authorized two-case batch is **closed at cq-p02's failure**. The two-case gate did not pass. No retry, warmup, tuning, case substitution or CQ1 run occurred within the batch. Both development cases were attempted once; one passed assistant checks, one failed.

| Case | Technical/source result | Actual execution | Persistent state |
|---|---|---|---|
| cq-p01 | Passed: both exact source-supported claims, correct rates/periods/bases, neutral title, no fallback | 2 main calls; 1 NeMo `PASSED`; 55.375 application seconds / 71.891 wall seconds | Revision 1, `needs_review`; reopened read-only; zero reviews/exports |
| cq-p02 | Failed: source sentence copied into `gap_anchor`, which must belong to the question | 1 mapper call; no composer or NeMo; 16.015 application seconds / 17.344 wall seconds | Failed, revision 0, no draft |

The operator wall-clock envelope includes CLI startup/preparation and limits each owned case process tree to 180 seconds. Neither case timed out; the forced-termination path was not exercised. Client/backend cancellation is not established by these normal completions. This is one synthetic development batch, not sustained latency or production evidence.

## What cq-p01 establishes

The actual composer kept Canada/observed demand growth/5.7%/2016 in u1 and Japan/projected demand growth/2.6% annually/through2036 in u2. Raw and final claims were complete for this supplied question, with no relative-level comparison or application fallback. NeMo passed the final text, and the parent persisted revision1 with unit/subtask/source/corpus provenance. Reopening SQLite read-only confirmed the exact draft and zero human reviews or exports.

This demonstrates current-revision post-safety persistence for this case. It does not prove the cause of the older v4 publication failure. The mapper's global geography was unresolved, so the title was already neutral; the new partial-label-suppression branch remains demonstrated by offline replay/tests rather than this actual mapper choice. Owner source/wording acceptance is still pending. The source records are explicitly synthetic, not official Canada/Japan electricity statistics.

## Confirmed cq-p02 failure

The wind evidence was retrieved and selected. The price branch correctly returned missing. The mapper chose `partial`, but set this gap anchor:

> In Denmark, wind supplied 29% of total electricity generation in 2015.

The question is:

> Describe wind generation in Denmark in 2015 and provide Denmark retail electricity prices yesterday.

That source sentence is not a substring of the question and identifies the known evidence rather than the unresolved price request. The response is normal, complete JSON with `done_reason=stop`; it parsed the generated schema, then failed the existing question-membership validator. Exact fixed-response replay raises **`Evidence mapping gap anchor is not in the question`**, before composition. No invalid mapping was converted into abstention, repaired, or used to discard the supported wind fact.

This is a wrong-domain partial-anchor generation failure plus a free-text gap field in the decoder contract. Retrieval succeeded for the available fact. There is no evidence here of truncation, schema extraction omission, GPU memory exhaustion, inherent open-source-model incapacity or a need for hosted inference. The guard correctly prevented an invalid partial answer from proceeding.

## Usage and preservation

Three actual main requests and one NeMo invocation. Known completed main usage: **1,806 input + 401 output = 2,207 tokens**. NeMo internal request/token counts, historical interrupted backend usage and monetary/hardware costs remain incompletely measured. Per-response usage and normal finish metadata are retained in `v7-diagnostic-findings.json`.

`executed-source-snapshot-v7/` preserves all128frozeninputs, the contract/grant and operator envelope; its manifest hashes the original actual output files. `cq-p02-offline-replay.json` confirms rejection with zero new model calls. Original success/failure records, owner-pending fields and the earlier failed attempts remain unchanged. No stored approval/export, source-CSV rating or owner identity was created.

## Next step and human review

Prepare a bounded concurrent-only question-span decoding contract before another model allowance. It must retain arbitrary requested subparts, preserve supported partial facts, keep canonical component IDs/branch bindings and leave the sequential parser/validators unchanged. Do not merely add a source-specific prompt example or fill the failed output's anchor after generation. See `partial-anchor-contract-proposal.md`.

Human source/wording review can assess cq-p01's valid claims; their wording matches the already-pending composer-only packet. Do not request repeated scoring of cq-p02's technical rejection. Approval/export would require the separate exact stored revision workflow and is not authorized by this diagnostic. CQ1 remains **0/20 attempted**. Actual partial-answer reliability, a passing current two-case gate, required qualification adjudication and production readiness remain unestablished.
