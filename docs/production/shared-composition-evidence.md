# Share identical evidence before composition

The digest-pinned v1.34 development run completed with clean process exits and matching identities. It used 15 workflow calls and three NeMo invocations (11,478 known input tokens; 1,402 known output tokens; internal NeMo tokens/cost unknown). p01/p02 passed narrow synthetic checks and r01 retained the requested category details/reporting period. **r02 failed the no-duplicate-claims criterion** despite retaining its causal facts: the composer independently paraphrased evidence repeated under two requested components. One paraphrase also omitted the seasonal-adjustment qualifier. The conditional 20-case set did not run. This failure remains in `resume-v2/diagnostics-v1-findings.json`.

## Structural repair

Before composition, identical ordered `(source_id, exact quotation)` units with matching established scope and ordered scope-citation proofs now share a representative. The prompt supplies that evidence once and retains all original unit/component IDs as provenance. The response schema permits representative IDs only. Aliases, unknown links and repeated output units fail explicitly; no repair call is added.

Projection reuses the representative body for each originating unit and runs every original component's validation. Omitted representatives still receive the existing bounded extractive fallback for every origin. Only after those checks does exact public-claim collapse run. Different quotations, overlapping spans, citation order, established scope or citation proofs do not receive semantic-equivalence guesses. This does not establish entailment or guarantee absence of all semantic redundancy.

An offline projection using the frozen r02 mapping supplies two composition units rather than four. Its serialized payload measures 906 UTF-8 bytes versus 1,746 before; this is not a measured token/latency improvement or a fresh generated-answer result. Synthetic tests exercise representative/alias rejection, all-origin validation, omissions, distinct evidence and scope/citation boundaries. The sharing checkpoint passed 493 offline Windows tests.

## Preserve explicit measure qualifiers

The next small pass retains explicit seasonal-adjustment status, unadjusted status and gold exclusion when present in selected quotations. Recognized aliases are narrow lexical equivalents; absent/negated qualifiers trigger the same exact-source fallback. Qualifiers come from supplied evidence, not invented requirements for a question. Diagnostic reasons identify the omitted qualifier for every affected origin. These checks are not a general financial-measure or negation classifier.

The qualifier pass passed 56 targeted tests and the integrated Windows suite passed 503 tests. Prompt identity is `analyst-pilot-v1.36`. Public `Draft`, dependencies/model settings, graph boundaries, four workflow-call ceiling, final NeMo check, approval/export lifecycle and frozen inputs/outputs remain unchanged. The private composition schema now uses representative units; old raw responses containing alias claims must remain historical rather than being silently treated as current-model replies.

The owner has now authorized a fresh four-case diagnostic set and conditional 20-case run after current Linux/container checks; new actual outputs still require source inspection before unlocking that conditional gate. All earlier failures remain failures; no human rating, approval, export or external use is created by this code or its synthetic tests.

Current outcome: the separately authorized v1.36 development gate passed all four checks, unlocking the frozen v2 set. That run stopped on r06 mapping validation after four attempts; three returned drafts had scope/coverage failures and sixteen cases were unattempted. The qualification gate FAILED. See [complete findings and next repair gate](qualification-v2-findings.md). Earlier checkpoints above remain historical; no retry or new approval/export occurred.
