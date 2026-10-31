# v1.55 consumed-case offline replay — 2026-10-30

The owner requested offline execution before authorizing fresh r03–r05 generation. This pass uses unchanged v1.55 with retained model responses. It makes **zero new model, NeMo, Ragas or hosted-inference calls**. It does not consume or activate the proposed three-case generation allowance.

## Method and evidence

The existing `scripts/_composer_capture.py` helper replays the two retained tool turns and mapper response, parses the retained composer response against the current schema, and runs the real retrieval, mapping, scope, composition and citation validation. It stops before the safety node; no safety verdict is fabricated. Socket connections are prohibited during replay imports and execution. Each case receives one replay, with the clock fixed to 2026-10-30. Retained response bytes are not edited or repaired.

The ignored local evidence directory is `reports/workflow_pilot/production-readiness-2026-10-27/resume-v31/`. It contains the before-hash snapshot, individual replay records, source assessments, test and dependency logs, and final integrity checks. The historical attempts remain in their original locations:

| Case | Retained response | Current deterministic result | Remaining limitation |
|---|---|---|---|
| r03 | `resume-v8/development-v149/attempt-r03.json` | Passes validation; draft and all cited source records exactly match the historical result. | Owner's earlier request for explicit Thailand wording remains. The causal explanation is retained through a disclosed source-excerpt fallback. |
| r04 | `resume-v8/development-v149/attempt-r04.json` | Passes validation; draft and all cited source records exactly match the historical result. | Owner's earlier country-wording request remains. Monthly seasonal adjustment and the quarterly distinction are preserved; source-excerpt fallback remains visible. |
| r05 | `resume-v9/development-v150/attempt-r05.json` | Passes validation; draft and all cited source records exactly match the historical result. | Historical wording still lacks the owner-requested 2023/2024 baht comparison and semiconductor/advanced-electronics drivers. Structural validity does not satisfy that editorial completeness request. |

For r03, the pinned BOT December report's units 4 and 13 support headline-inflation causes and stable core inflation respectively; heading units 0 and 5 establish the monthly period. For r04, unit 9 supplies the monthly investment passage and unit 14 the quarterly comparison. BOT records are HTML paragraphs, not PDF pages. For r05, BOI PDF index 0 / PDF page 1 supplies application value and drivers; index 1 / PDF page 2 supplies project counts and the 2023 value comparator. The replay's cited source records are identical to those previously assessed. This is a source-identity and retained-content check, not an independent re-evaluation of actual generation.

The previous source assessments and owner judgments remain authoritative historical records. No new numerical human ratings, owner acceptance, database approval, export or warning waiver is inferred. The source extraction's existing replacement character in r03 is retained byte-for-byte; this pass does not silently edit a pinned corpus.

## Interpretation and next action

The replays demonstrate that the latest structural change does not reject these three saved successful mapper/composer responses. They do **not** demonstrate that the current local model will select the same evidence, generate valid responses, include the requested wording, or pass NeMo on a fresh run. The application-owned project-count change in v1.55 principally addresses r06; r03–r05 do not exercise that binary count-comparison path. Its synthetic tests remain separate evidence.

No application, dependency, prompt, model-setting, retrieval or frozen benchmark change was made. Fresh r03–r05 diagnostics remain subject to a new direct grant under the prepared protocol: once per case, at most 12 main-model calls and three NeMo invocations total, 180 seconds per case, with source/completeness inspection and stopping at the first failure. The owner's reply requesting offline work is **not** that grant. No held-out twenty-case run is authorized here.

Human review is not needed to repeat the existing judgments on these identical saved drafts. Any new generated wording needs source/completeness review before it can be called owner-accepted; exporting still requires approval of the exact stored revision. Independent reviewer sessions and production rollout acceptance remain separate, pending gates.

Validation results and the exact next step are recorded in the local final integrity report and handoff. The full Goal remains incomplete: offline plumbing checks cannot establish the fresh-quality, independent-use, deployment or sustained-operation gates.
