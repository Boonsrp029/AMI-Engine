# Qualification continuation — 2026-10-27

Assistant-authored engineering assessment. Owner acceptance of new generated outputs remains pending. Historical owner decisions and evaluation records are unchanged.

## Actual run and stop conditions

The first resumed preflight pair (`resume-v1/preflight-v3`) produced a supported p01 response. p02 failed after one model call while atomically replacing its progress file: `PermissionError`. The retained exception lacks the Windows error code, so its exact external cause is unknown. Progress persistence now uses a unique temporary file and bounded replacement-only retries; permanent denial still fails explicitly and preserves the previous report. This does not retry inference. Synthetic and actual Windows sharing-lock tests pass.

The separately authorized fresh pair (`preflight-v4`) completed: p01 answered the synthetic quantities and cause; p02 abstained on the unavailable audited observation. Together they used seven workflow calls and one final policy invocation. Assistant source/contract checks passed, permitting the authorized held-out run with the same generator and package identity. This was not owner adjudication.

The held-out run (`heldout-v1`) stopped after two cases, using seven workflow calls and one final policy invocation:

- **r01:** technically completed, but omitted several available export-category movements. The final policy allowed it; that did not establish completeness. Its assessable output is retained in a separate review packet.
- **r02:** failed before composition because the mapper attributed a period to unrelated selected passages. Retrieval had returned foreign-exchange, meeting-date and investment material rather than the tourism paragraph. Scope validation rejected the mapping. The raw response ended normally; the evidence does not establish GPU exhaustion or a general open-source-model limitation.
- **r03–r20:** 18 cases unattempted. No 20-case score or release-quality pass exists.

The model-only source-policy diagnostic's earlier 5/6 result also remains failed: a wrong date was allowed. A narrow deterministic period backstop now supplements the policy; it is not a general entailment judge. See [temporal limits](temporal-backstop.md).

## Focused repairs, offline evidence

The unprofiled analyst retriever now fuses original intent with the planner query, normalizes limited English forms, and handles tourism receipts/revenue vocabulary. Calendar-only matches cannot supply evidence. Original text, identifiers, tie order and the lower-level raw BM25 retriever are preserved. The older corpus-pinned profile retains its existing behavior. A retrieval-only replay of consumed r02 ranks its correct tourism paragraph first; no model ran.

For explicit export-category requests asking about opposite directions, source selection can require a numbered declining list and an explicit contrasting increasing passage from the same retrieved record. It activates only for the literal grammar with one unambiguous matching record; unrelated, split-record or ambiguous evidence uses normal mapping. Empty unresolved selections remain possible. Existing validators still check quotations, scope and citations. This is not a general multipart-retrieval solution.

For requested categories, products, groups, markets, sectors, measures or factors, synthesis checks explicit numbered labels and `such as` lists in selected evidence. Missing literal items trigger the existing bounded extractive fallback, with a specific diagnostic reason. Synonyms can trigger a conservative excerpt; unselected facts and unmarked lists remain outside the check. Unsupported numbers/measures still fail normal validation. No additional model call or approval is added. Prompt identity is `analyst-pilot-v1.31`.

Targeted coverage tests: **41 passed**. An offline replay using deliberately incomplete synthetic summaries against consumed r01 sources retained both exact selected passages. Neither fixed-response tests nor replays establish actual generation quality.

## Revised frozen pool and next generation gate

Before retrieval tuning, a revised package was frozen under `data/external/release_qualification_2026_10_27_v2/frozen-v2`. It retains the 18 unattempted questions and replaces consumed r01/r02 with r21/r22, using newly pinned public BOT January 2025 material. Manifest SHA-256: `f28098dc9e43ce2048f154f9b3e59c5fd99ea9c67d682e97ec2179131925aa20`. The public specification and source lock are under `data/pilot/release-2026-10-27-v2/`. The new source is the [official BOT release](https://www.bot.or.th/en/news-and-media/news/news-20250228.html).

The cases share documents and source families with development; they are held out from output inspection/tuning, not an independently sampled statistical benchmark or proof of training-data novelty. The old overlap check measures overlap with the original development case file only. Preserve the explicit retained/new/consumed provenance.

The owner subsequently authorized p01/p02 plus consumed r01/r02 as development diagnostics, with at most 16 main calls/four NeMo invocations, and a conditional 20-case run. All four completed under prompt v1.31, using **15 main calls, three NeMo invocations, 11,424 known input tokens and 1,398 known output tokens**. NeMo internal tokens and monetary cost remain unknown.

The two synthetic preflights passed their narrow assistant checks. Consumed r01 retained its category details, including the previously omitted movements; its geographic/period warnings remain unresolved. Consumed **r02 failed source-quality acceptance**: it retrieved and selected the correct receipts-cause passage, then composed repeated origin-market facts in its place. The permissive lexical cause check accepted overlapping subject words without preserving the causal relationship. The final model policy allowed the incomplete draft. Therefore **zero revised held-out cases ran**; the conditional budget was not unlocked. Raw outputs and unsuccessful findings remain in `preflight-v5`, `consumed-development-v1` and `v2-diagnostic-findings.json`.

The subsequent offline repair conservatively falls back to a selected excerpt when explicit causal terms are lost, rather than treating shared subject words as sufficient. A saved-response replay retains the missing receipts explanation, but also retains duplicate evidence across request slots. Prompt v1.32 is **not validated by new model generation**. This literal safeguard can preserve source wording for synonyms; it is not general causal entailment. No further generation is authorized under the consumed diagnostic budget, and no improved score or owner acceptance is claimed.

An actual Linux suite also exposed concurrent polling/reaping of the same owned process during cancellation. The dispatcher lifecycle probe now shares the cancellation/shutdown lock; a controlled race test holds one probe while cancellation starts. The original Linux failure is retained. Current packaging must be rebuilt/tested before attributing Linux success to this repair. Opt-in [local identity controls](identity.md) are a separate offline engineering pass; the default supervised bootstrap remains available.

## Human review

Engineering failures, schema/quotation problems and automated-test failures do not require manual scoring. Any new technically valid generated outputs require source-grounded owner adjudication before being called owner-accepted. Exact-revision approval is still necessary before export; empty drafts remain unapprovable. The owner arranges an independent reviewer session before external usefulness can be claimed. Neither the owner nor assistant audit substitutes for that session.

All raw evidence is separate in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v1/`. No historical output, owner rating, approved export or requirements file was overwritten. No commit, push, external deployment or reviewer contact occurred. Portfolio-complete and production-qualified remain unmet milestones.

## Current v1.36 checkpoint

The later v1.34 run passed p01/p02 and consumed r01, but r02 repeated two evidence units under different request components and dropped a seasonal-adjustment qualifier in one paraphrase. Its 15 workflow calls/three NeMo invocations remain a failed development gate, with zero v2 held-out attempts.

The current repair shares identical evidence before composition, validates every original component after projection, and retains explicit source measure qualifiers through bounded extractive fallback. Windows: 503 passed; Linux: 502 passed, one Windows-only skip; both retain 15 dependency warnings. The v1.36 image/recovery smoke passed with zero inference and unchanged cached exports. See [repair details](shared-composition-evidence.md) and [model identity](model-content-identity.md).

The owner authorized one new p01/p02 plus consumed r01/r02 set, at most 16 workflow calls/four NeMo invocations, and only on all four passing a conditional 20-case run of at most 80 total workflow model calls and 20 NeMo invocations. One attempt/case, 180 seconds, pinned local digest, no retries/Ragas/hosted inference. Actual assessments remain pending; earlier failures and owner judgments remain unchanged.

Current outcome: the separately authorized v1.36 development gate passed all four checks, unlocking the frozen v2 set. That run stopped on r06 mapping validation after four attempts; three returned drafts had scope/coverage failures and sixteen cases were unattempted. The qualification gate FAILED. See [complete findings and next repair gate](qualification-v2-findings.md). Earlier checkpoints above remain historical; no retry or new approval/export occurred.
