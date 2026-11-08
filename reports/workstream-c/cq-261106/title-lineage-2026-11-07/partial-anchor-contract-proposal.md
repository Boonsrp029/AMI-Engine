# Proposed private question-span contract for unresolved anchors

**Proposal only; no source/prompt change or new model allowance is activated here.** The v7 failure remains failed. C owns the concurrent mapper schema/resolution/tests; D owns admission checks. A/B contracts, public Draft/API, source ranking, model/settings, dependencies and sequential request parsing remain unchanged.

## Observed contract gap

The concurrent schema constrains supported anchors to empty and missing anchors to the canonical question. Its partial/conflicting alternative leaves `gap_anchor` as free text. Actual cq-p02 copied the selected source sentence into that field. Parsing passed; exact question membership rejected. The instruction already says to copy only the unanswered requested fragment, so merely asserting that this instruction exists is not evidence of repair.

## Proposed design boundary

Move unresolved-anchor transcription into **application-resolved question-span selection**, analogous to source-span selection. Offer a bounded catalog derived only from the original question/canonical request text, with stable boundary identifiers and exact offsets. The model selects the unresolved span; application code resolves it verbatim and runs all existing validators. It must not infer which requested fact is missing from source/branch status or silently correct an invalid selection.

Prefer a general start/end-boundary representation over a few hardcoded development-case clauses. It must represent requested subparts within noun lists and imperative questions without changing canonical component IDs or branch bindings. A limited English conjunction splitter alone would narrow valid partial-answer scope and is insufficient. Explicitly decide Unicode, punctuation, boundary granularity and maximum-question behavior before implementation; retain supported partial answers without a generic whole-question gap substitution.

Selections outside the current request, reversed/empty boundaries, unknown IDs, malformed state and unsupported metadata must fail without retries/repair. Supported/missing/conflicting states keep their current semantic distinctions. Choosing a valid question span proves membership, not that the span is genuinely unanswered; source/completeness inspection remains necessary. Keep raw selections, resolved anchors, source evidence and fallback/editorial provenance distinct.

This is an explicit private mapper contract change. Specify its wire/version compatibility and preserve the public Draft and sequential mapper. Do not modify old outputs to fit a new schema or claim a newly constrained parser establishes semantic improvement.

## Reviewable offline passes

1. Prototype a source-free, bounded question-span catalog/selection schema using different synthetic facts. Freeze the accepted wire and exact projection into the existing anchor field. Compare representable fragments against the current contract; do not choose a narrower form just because cq-p02 is simple.
2. Test multipart, noun-list and imperative requests; Unicode/punctuation; canonical component isolation; exact extraction; invalid/reversed/out-of-range selection; supported partial facts, genuine absence and conflicts. Test that source text cannot become an anchor or authorize an action.
3. Integrate only the concurrent path, preserve schema/quotation/relationship validation, and replay old failures under their executed snapshot to retain the original diagnosis. Any new-wire parsing failure must not be mislabeled as proof the historical semantic defect was repaired.
4. Recount context and grammar with the unchanged4096/900limits. Avoid quadratic enumeration of all question substrings or a large duplicated character catalog. If representation does not fit the existing budget, fail explicitly and propose the resource/contract tradeoff rather than silently dropping coverage.
5. Run targeted/integrated offline checks. Prepare one new mapper-only actual preflight before proposing another workflow batch. No existing unused-call remainder can reopen the closed v7 allowance.

## Required actual and human evidence

A future preflight must independently produce the correct supported/missing split and a valid **unanswered** question span, not just syntactically legal IDs. Only a new explicit grant can fund it. Current two-case workflow qualification and fresh CQ1 evaluation still require their own applicable passing evidence and grants. Human semantic acceptance applies to assessable outputs; technical anchor failures need no manual rescoring.
