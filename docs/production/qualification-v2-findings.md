# Local qualification checkpoint — 2026-10-27

Assistant-authored assessment. Human factual adjudication is pending; no approvals, exports or human scores were created. **The qualification gate failed.** Portfolio completion and production qualification remain unmet.

## Artifact and authorization

Prompt `analyst-pilot-v1.36`, mapping `requested-evidence-v23`, Python 3.12.10, local Ollama 0.40.11, RTX 4060 with 8,188 MiB reported memory. Model content digest: `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`. Generation identity: `6105bd21a45153add2eab461cb9ea99097da3085671a1dc149c4b69013a26a6c`. Digest checks around calls are observations, not transactional server attestation.

Windows passed **503 offline tests**; the actual current image passed **502 Linux tests, one Windows-only skip**. Both retained 15 dependency warnings. Image `ami-pilot:qualification-a4c2334b2465513c`, ID `sha256:c41b5402837e175c637ccddd07727785f5783e4bebcee90bfd6ef349229e48a5`, passed its no-inference recovery smoke, preserving four exact approved exports and blocking empty d06. This is local dirty-checkout evidence, not remote GitHub CI or container inference proof.

The owner authorized one p01/p02 plus consumed r01/r02 diagnostic set, with a conditional 20-case run. One attempt per case, 180-second external process deadline, at most four workflow calls and one NeMo invocation per case; no retries, Ragas or hosted inference. No code, prompt, ranking or acceptance threshold changed during the run.

## Development gate

All four diagnostics passed their narrow assistant source checks, with clean process exits and matching identities:

| Case | Observed result and limit |
|---|---|
| p01 | Correct synthetic shipment increase, cost decrease and warehouse-capacity cause; unresolved cost period remained explicit. |
| p02 | Correct abstention on absent audited 2025 profit; no historical shipment forecast substituted. |
| r01, consumed | Monthly export direction, seasonal adjustment, gold exclusion and opposing categories retained. Exact excerpts supplied details omitted by composition. |
| r02, consumed | Two distinct claims retained tourist count/origin movements and revenue/long-haul-share cause, including seasonal adjustment. Previous paraphrased repeats were absent. |

The two consumed cases retain unresolved-geography and extractive-readability warnings. These results demonstrate the specific development repair; they are not unseen quality evidence or owner acceptance. Usage: **15 workflow calls, three NeMo invocations, 11,206 known input and 1,399 known output tokens**.

## Held-out gate and diagnosis

Four of the frozen 20 cases ran. Three returned drafts; r06 failed mapping validation and the supervisor stopped. **Sixteen cases were unattempted.** None of the three drafts met its complete, source-supported answer contract in this assistant assessment. Do not report a 20-case accuracy percentage or credit unattempted safety/abstention categories.

| Case | Finding | Failure path |
|---|---|---|
| r03: December inflation | **Critical period/support failure.** January fresh-food/core-inflation material and a quarterly antecedent fragment answered a December monthly question. The December summary retrieved by the same attempt says core inflation was stable. | Mapper selected wrong-context spans. The detailed December explanation was also absent from retrieval. Unresolved-period warnings did not prevent publication of inappropriate claims; NeMo returned `YES`. |
| r04: monthly/quarterly investment | **Incomplete and partly irrelevant.** Quarterly investment contraction was retained, but the requested monthly direction/categories were absent. Consumption, exports and overall-economy facts occupied the answer. | Request slots did not ensure coverage of each period/measure; supporting a quotation did not establish that it answered its assigned question. NeMo returned `YES`. |
| r05: BOI value/count | **Critical scope-label failure.** An industry phrase became geography; the release month became observation period. The source-provided approximate USD value and project counts were retained; omission of the baht equivalent alone is not a failed requirement, since the question did not prescribe currency. | Capitalization after “in” supplied an untyped geographic choice. A bare dateline passed the publication-cue heuristic. Scope propagation then added those labels to otherwise partly accurate facts. NeMo returned `YES`. |
| r06: FDI denominators/comparison | **Technical failure; no draft to score.** Mapper asserted a period absent from its selected quotation. Candidate also substituted Singapore's share of FDI for FDI's share of all applications and omitted requested comparisons. | Canonical request splitting left the multipart question as one slot. `validate_mapping()` correctly rejected the unestablished period before composition/NeMo. Preserve this validator; do not relax it or call this an abstention. |

Source locators: r03 uses `BOT_DEC2024:unit:4`, `:unit:13`, `:unit:14` and `BOT_JAN2025:unit:0/:unit:8`; r04 requires December monthly investment material and the distinct quarterly unit 14; r05/r06 use BOI PDF indexes 0–1, reader-facing pages 1–2. The rendered BOI pages confirm that 13 January 2025 is the release date, the investment observations concern 2024, and the two FDI percentage denominators differ. Source IDs, hashes, full local excerpts, rendered pages and exception locations are retained beside the attempts.

Held-out usage: **15 workflow calls, three NeMo invocations, 15,665 known input and 1,733 known output tokens**. All four processes finished within their deadlines; the failing mapper response ended normally. There is no retained OOM signal. These observations do not establish general GPU sufficiency or an inherent limitation of open-source models. NeMo internal tokens, hardware energy and monetary cost remain unknown.

## Next repair gate

1. Preserve this failed final-pool attempt. r03–r06 become consumed development evidence if used for tuning. Keep the sixteen untouched cases frozen and prepare replacement facts before tuning the next final qualification pool. Retain the original failure and denominators.
2. Replace untyped scope promotion with explicit provenance. Publication dates must remain separate from observation periods; an industry phrase cannot become a place solely through capitalization/prepositions. Validate each selected source's report/section period against its assigned requested component, with conservative failure on established incompatibility. Do not turn an unknown period into a false known date or hide a mismatch behind a warning.
3. Separate each requested measure/period/comparison and check evidence coverage before composition. Preserve supported partial answers, but do not fill missing requests with unrelated background. Complete source spans and retrieval coverage remain necessary: source identity and exact quotations alone cannot prove relevance or causality.
4. Use synthetic regression fixtures and saved-response replay first. Preserve four-call bounds, existing validator rejections, final guardrails and exact-revision approval/export behavior. A structural fail-closed check is not a semantic quality pass. Do not make case-ID-specific corrections or hardcode reference answers.
5. Only after a concrete offline-verified repair, propose a new bounded diagnostic budget. The current batch stopped; its remaining ceiling is not authorization to resume under a changed generator or retry failed cases. No Ragas or hosted inference is implied.

## Human checkpoints

No manual scoring is needed to diagnose r06 or these engineering failures. A local packet contains seven technically completed outputs: four development diagnostics and three unsuccessful held-out drafts, with unchanged text, source records and reference locators. Failed drafts are diagnostic evidence, not approval candidates. An owner may dispute this assistant assessment with source locators; no repeated numerical scoring is requested.

Any future output called owner-accepted still needs source-grounded human review. Export requires approval of that exact revision; empty drafts remain blocked. Independent usefulness requires an actual reviewer session arranged by the owner. Existing ratings, accepted drafts and cached exports remain unchanged.

Local evidence root: `reports/workflow_pilot/production-readiness-2026-10-27/resume-v2/`. Key records: `diagnostics-v2-findings.json`, `qualification-v2-findings.json`, `heldout-v2/summary.json`, and `qualification-review-v2/review-packet.md`. Detailed copyrighted source excerpts and rendered pages remain in ignored local storage.
