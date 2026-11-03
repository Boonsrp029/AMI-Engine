# Unit-local source cues — offline v1.69, 3 November 2026

**Offline checks passed; actual model improvement is unverified.** The [v1.68 batch](qualification-v168-findings-2026-11-03.md) remains failed at consumed r07 and its allowance remains closed. This change adds input guidance; it does not change the validator or reinterpret the failed answer as correct.

## Bounded change

The existing financial `required_literal_coverage` checklist did not apply to r07's nonfinancial percentage/forecast units. Those units had correct quotations but no compact unit-local rate/period cues. The raw composer copied the historical claim into its forecast slot. The strict per-unit numeric validator rejected it before a final draft or NeMo.

For percentage-bearing units without that financial checklist, the private composition payload now adds **source_literal_cues** derived only from each unit's selected quotations: exact percentage spellings, four-digit numeric tokens, and a short fixed vocabulary of quoted modality/rate words. The model is instructed to compose each unit from its own evidence, retain observation/forecast and annual/cumulative distinctions, and avoid copying a previous unit's claim across different rates or periods.

The cues **do not classify factual roles**. Four-digit tokens may be counts rather than years; a forecast word may be negated. Questions, as-of dates, mapper paraphrases and other units supply no cue values. Quotations remain the factual authority. Existing financial obligations are unchanged, and legacy calls without a question retain their old payload shape. There is no new framework, schema migration, model call, judge, repair loop or application-owned replacement answer.

Prompt is analyst-pilot-v1.69; mapping remains requested-evidence-v44 and source-selection wire remains v1. Public Draft/API, retrieval, model/settings, SQLite, guardrail and approval/export contracts, dependencies and historical evidence remain unchanged. The per-unit numeric/support validators and their failure behavior are untouched. The source cues are compact lexical guidance, not semantic proof or a guarantee against hallucination.

## Evidence

| Check | Actual offline result |
|---|---|
| Targeted composition/instruction tests | **34 passed** |
| Full Windows suite | **1,294 passed**, 15 existing warnings |
| Full Linux suite | **1,293 passed, one platform skip**, 15 existing warnings |
| No-inference recovery/restoration/restart | Passed; original backup read-only and four cached approved exports byte-identical |
| Private reduced-diagnostic admission tests | **25 passed**; failed/changed/unknown/synthetic evidence cannot admit a workflow |
| Retained bad r07 replay | Same exact numeric-validation rejection; zero actual model/NeMo calls |
| SDK request parity | JSON-value equality using mocked HTTP; no real network request |
| Separately labelled source-quote counterfactual | Actual engine composition validation passes; synthetic/fixed-response evidence, not model quality or owner acceptance |
| Socket-blocked offline validation subprocess | Passed in 9.52 seconds within its 30-second budget; no NeMo |

The new synthetic fixtures use different subjects, rates and dates from r07. They exercise source-local cues, punctuation/sign spelling, identifier/decimal boundaries, ignored question/as-of numbers, negative forecast wording, unchanged financial guidance, source-instruction rejection and strict rejection of wrong quantities/periods. Fixed responses establish contracts, not real-model quality.

The first targeted run found that the four-digit-token matcher dropped a token before sentence-final punctuation. Its boundary was corrected and tested without admitting decimal/identifier fragments. An initial offline validation rehearsal omitted its output directory; the corrected rehearsal uses the supervisor-created directory. Both failed preparation logs remain retained. Neither was a model retry.

The test image is a source-only overlay `ami-pilot:source-cues-v169`, immutable ID `sha256:934746ec47dcc64a1e85e28aa4ae717160dbdf54fd0f28805c03e94b07c8dd7f`, from verified full-recipe v1.68. Only three runtime source files are copied; the dependency environment is inherited unchanged. Tests use a sanitized read-only source snapshot with networking disabled. This is not a new full recipe, clean installation, remote CI, actual container inference or Desktop-service upgrade.

## Next gate and human checkpoint

A [reduced r07 diagnostic](reduced-r07-proposal-v169-2026-11-03.md) is prepared: one composer request over consumed fixed retrieval/mapping stages, followed by one complete workflow only if technical **and raw source/completeness** gates pass. It requires a new grant. No twenty-case run is proposed, and unused v1.68 calls cannot be reused.

No new human scoring is needed for these engineering checks or r07's technical failure. New valid actual wording needs source/completeness review before owner acceptance. Exact stored-revision approval/export, independent reviewer tasks and rollout acceptance remain separate. The nineteen reserved cases remain untouched; r07 cannot count as unseen after this repair. Fresh qualification and the full portfolio/production Goal remain incomplete.

Ignored evidence: `resume-v112/` contains baseline, failed/final tests, image/Linux/recovery and retained-response diagnosis; `resume-v113/` contains capture/parity/fixed counterfactuals, controller checks, prospective contract and offline rehearsal. No new model/NeMo calls, Ragas, hosted inference, corpus edits, original-judgment edits, commit, push, deployment or reviewer contact occurred.
