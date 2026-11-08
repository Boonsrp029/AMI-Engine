# C corpus-backed integration pass

## Current behavior and ownership

B supplies LocalBM25Adapter for a pinned single-file corpus. A owns runner.py, _handoff.py and persistence; those files already accept C project_report results and perform final safety and fenced publication. C owns synthesis.py and tests/test_subtask_corpus_synthesis.py. No shared runner edits are planned. B/D changes are not implicitly authorized by this work.

## Small passes

1. Exercise actual adapter results through the existing aggregate, typed C projection, spawned safety and Store, using temporary synthetic corpus records distinct from consumed r07. Targeted tests precede broad checks.
2. Test strict per-unit facts, scope and attribution; diagnose any accepted substitutions before proposing narrow C validation changes. No semantic success claim from parsing.
3. Cover completed missing evidence versus required technical failure, safety rejection, cancellation and late publication. Retain existing exact-revision approval/export and cached export checks.
4. Revalidate affected integration; broaden only after the contract and targeted tests stabilize. Record exact evidence and preservation hashes.

## Decisions and limits

Required technical failure continues to block composition; completed missing results may yield supported partial answers with explicit branch gaps. No model-based conflict detector or factual guarantee is introduced. Raw model responses, source fallback and editorial changes remain distinct. Generation is held; dependency/public API changes and runner contract changes require separate proposals to their owners.

## Human review

Fixed-response engineering checks need no semantic acceptance from the owner. New actual generated outputs require a separate purpose/scope/budget grant and later review. No generation or deployment is part of this pass.

## Explicit C composition-contract tightening

The corpus probe demonstrated a wrong-country assertion could reach needs_review with a synthetic accepting guard. The new private `_relationships.py` gate binds source locatives such as “In Canada” and percentage “of ...” denominator phrases to each selected unit. Explicit source locations must remain in the assertion; competing explicit locatives reject. Percentage-denominator pairs require exact whitespace/case-normalized bounded phrases. Aliases, translations, conversions and denominator paraphrases are not inferred or automatically repaired. This is stricter opt-in C behavior, not a change to the public Draft schema or sequential workflow.

This gate is a necessary lexical check, not a universal geography classifier, entailment judge or proof that a model interpreted evidence correctly. Implicit geography and relationships not explicitly expressed by these constructions still require source review. Numeric/period/measure checks remain active; no validator was relaxed. Historical failed probes remain preserved.

## Final offline evidence

The integrated suite passed **1,487 tests with 15 warnings in 422.52 seconds**, with no drift across 183 pinned source/test/config files. The retained geography failure remains historical evidence; repaired tests reject the substitution. Corpus-backed projection, fallback attribution, identity/provenance failures, safety rejection, cancellation, exact-revision approval and cached-export behavior passed. Reserved package and original r07 hashes, dependencies and A/B boundaries were verified after the suite. Evidence: `reports/workstream-c/corpus-integration-2026-11-06/completion-audit.md`. No actual model-quality improvement is claimed.
