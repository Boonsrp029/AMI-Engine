# Qualified subject views and mapped numeric alignment — 28 October 2026

**Subsequent execution:** the [v1.49 gated diagnostic](diagnostic-v149-findings.md) failed at r05 after two mapper checks and r03/r04 passed. It exposed a currency-adjacent numeric-parser false rejection and independent evidence-selection/completeness failures. The offline record below describes the repair before that execution.

Prompt `analyst-pilot-v1.49`, mapper `requested-evidence-v34`. This offline repair follows the [v1.48 source-quality failure](diagnostic-v148-findings.md). Actual v1.49 selection and complete answer quality remain unverified; no new model or NeMo call is part of this pass.

## Observed cause and change

The required r05 view treated the bare word “investment” as a sufficiently specific financial subject. It promoted an institutional contact header or Hong Kong-specific paragraph ahead of the total-value passage. The mapper's short answers were numerically correct, but its quotations did not support those numbers. Composition copied the chosen header and unrelated FDI facts, and NeMo allowed the grounded but unhelpful answer.

The financial-subject view now requires a qualified subject such as private/public investment or headline/core inflation. Bare investment, consumption and inflation mentions remain untyped rather than creating compulsory evidence. The shared focus helper applies this boundary consistently; other period-based view paths retain their eligible candidates without a bare-topic primary-record preference. No source text or retrieval ranking changes, and no untyped passage is converted into missing evidence automatically. Qualified lexical identity is still not general semantic proof.

After selected evidence and reporting-period context have been validated, each supported/partial mapper short answer is checked for numeric compatibility with **its own selected quotations**. Another component's evidence or an unselected source cannot justify its numbers. Only an already established, literal component period may be excluded from this numeric comparison; the question alone does not establish a date. A mismatch raises a mapping failure before composition or NeMo. There is no reassignment of IDs, deduplication, repair call or fabricated abstention.

This reuses the existing numeric parsing. Positive tests showed that applying stricter final-claim unit-pair checks to short mapper summaries would reject legitimate implied units; the added check therefore stays numeric. Existing final-claim measure/unit/quantity/subject checks remain unchanged. Numeric compatibility does not prove relevance, causal support, denominator identity, unit conversion or completeness; matching numbers in an unrelated passage can still pass this necessary check. Model/source-quality gates and human review remain required.

## Evidence and validation

The synthetic contract and before-state hashes were pinned before implementation in ignored `resume-v8/contract-v1.json` and `baseline.json`. New tests cover bare institutional words, preserved qualified views, source/component isolation, supported partial and unresolved states, established period binding, the semantic limitation, and engine behavior. Invalid numeric mappings stop after three workflow calls with no composer/NeMo call; valid mappings still compose and pass through final guardrails.

A controlled replay of the unchanged failed r05 selection now rejects both mapper components and creates no compulsory bare-topic view. It makes zero model/NeMo calls and does not produce a fresh answer. Fixed-response checks also validate the proposed fixture/schema plumbing without creating actual model results or authorization.

Final offline suite: **745 Windows tests; 744 Linux tests plus one Windows-only skip; 15 existing warnings**. Intermediate runs and an initially overstrict positive-test failure remain retained. Image `ami-pilot:qualification-f1e6e6826fa4611d`, ID `sha256:8d7f8e42937f14ac5a28ab1347903b7c3e7faa6977ec705d376a49cdc6871593`, matches sanitized context `f1e6e6826fa4611d527cfc28b910d308402d4bff305b3445ce4f38b5b1180833`. Its no-inference recovery check preserves all four cached exports and keeps empty d06 blocked. Logs, replay, source/build manifests and integrity evidence are in `reports/workflow_pilot/production-readiness-2026-10-27/resume-v8/`.

Public APIs, `Draft`, SQLite schema, model/settings, source data, library versions, four-call workflow ceiling, final NeMo and exact-revision approval controls remain unchanged. Prompt instructions were not tuned. The new necessary-check event/failure and metadata versions identify this functional repair. No commit, push, hosted inference, Ragas, external deployment or reviewer contact occurred.

## Next gate and human checkpoint

The [gated v1.49 diagnostic](gated-diagnostics-proposal-v149.md) is proposed separately. It first tests application value/count/growth with contact and FDI distractors, then unavailable realized-investment evidence. Only if both mapper checks pass technical and assistant source-quality gates may the same-generator consumed workflow cases run. No twenty-case evaluation is included.

The [owner's r03/r04 adjudication](../pilot/owner-review-v147-2026-10-28.md) and country-clarified editorial candidates remain unchanged. Their factual review need not be repeated; exact changed-candidate acceptance remains pending if those briefs are to be accepted/exported. New generated content requires source review except where exact draft and cited-source identity legitimately links to existing adjudication. Known technical/source failures need engineering diagnosis, not repeated manual scoring. Independent usage, portfolio completion and production qualification remain open.
