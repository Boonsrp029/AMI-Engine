# Investment-category retention — v1.59

This is bounded runtime hardening backed by synthetic offline checks, not a passed generation-quality gate. The actual v1.58 mapper failure remains unchanged and its inference allowance is closed.

## Observed hole and repair

An offline counterexample used a complete fixed mapper answer and a deliberately incomplete fixed composer answer. The selected quotation described stable public investment, increased rail-equipment and vehicle investment, and declining construction with explanations. The composer omitted the vehicle category and explanations. Projection accepted it without fallback because the request used “which categories explain”, while the existing causal/list checks covered other wordings and explicit list markers.

`src/pilot/_investment_coverage.py` adds a private literal-retention check. When a question explicitly requests which/what investment categories, it examines selected quotations that uniquely identify the requested public/private investment subject. It recognizes explicit “Investment in [category] increased/declined/…” clauses and compares their terms with the composed text. An omission invokes the existing logged source-excerpt fallback in `_composition.project`; it does not insert a guessed answer or add an inference call.

The diagnostic reason is `requested_investment_categories_absent_from_synthesis`. The fallback remains limited to 800 characters and must pass the existing citation, scope, period, measure and number checks. Selected known instruction-like content is rejected rather than restored. Final NeMo and exact-revision human approval remain required.

## Boundaries

This conservative lexical check is not semantic entailment or a guarantee of completeness. Synonyms may trigger fallback. Rearranged words can preserve terms without preserving their relationships, so term retention is not proof of correct reasoning. Unrecognized prose, ambiguous/mixed subjects, generic category antecedents and explicit periods not matching the established literal period remain outside its grammar. It does not discover omitted corpus records or repair retrieval. Existing upstream source/period checks remain necessary.

The composer continues to receive selected source quotations, not mapper summaries. Mapper answers and their preflight completeness obligations are unchanged. A future composer or extractive fallback cannot retroactively pass the failed mapper diagnostic. The lower-level `project_draft` API and its compatibility behavior remain unchanged.

Workflow version is `analyst-pilot-v1.59`; mapping remains `requested-evidence-v39`. Public Draft/API, SQLite schema, retrieval, legacy graph, model settings, library versions, four-call ceiling and approval/export lifecycle are unchanged. No new model budget exists.

## Validation evidence

Synthetic regressions cover unnumbered categories and causes, complete retention, unrelated/mixed subjects, explicit incompatible or unresolved periods, absent qualified antecedents, source commands, partial-answer preservation, recorded fallback reasons, citations and the extractive length limit. Fixed-response workflow tests verify that restored text reaches final safety validation and fails closed when that validation rejects it. The exact prior synthetic counterexample now activates the logged source fallback, with the original counterexample file preserved.

Full suites passed: **1,097 Windows tests** and **1,096 Linux tests plus one platform-specific skip**, with 15 warnings per platform. All 22 new synthetic regression tests passed, including the actual fixed-response workflow safety checks. The immutable local image is `sha256:0c096d10353f116c5320dba921eca065c5d1d3388f0aaa9c36d5bb264b569cd0`. These are offline engineering results, not model-quality scores. The source-only container uses existing dependency layers, with no package installation. Restart/recovery checks preserve the four cached approved exports and the original read-only backup without new model calls or human decisions. Detailed integrity is recorded in the local `resume-v58/final-integrity.json`.

No owner scoring is needed for these engineering fixtures. New assessable generated drafts require factual/wording review. Independent usefulness, fresh qualification and actual production deployment remain separate incomplete gates.

Detailed ignored evidence: `reports/workflow_pilot/production-readiness-2026-10-27/resume-v57/` (counterexample/audit) and `resume-v58/` (repair/validation). Historical reports and actual failed attempts are unchanged.
