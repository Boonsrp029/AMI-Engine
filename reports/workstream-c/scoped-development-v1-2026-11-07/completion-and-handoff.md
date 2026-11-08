# Scoped v1 actual development diagnostic — 7 November 2026

The two-case allowance is closed after cq-p02 failed. The quality gate did not pass. CQ1 remains 0/20 attempted. No retries, hosted inference, Ragas, Databricks, commits, pushes, deployment or approval/export occurred.

| Case | Actual result | Calls | Safety | Retained outcome |
|---|---|---:|---|---|
| cq-p01 | Assistant technical/source/completeness pass; owner acceptance pending | 2 main | 1 NeMo passed | revision 1 needs_review; zero reviews/exports; neutral title after logged partial-country suppression |
| cq-p02 | Technical failure at composition | 2 main | 0 NeMo | failed, revision 0, no draft |

## Confirmed cause

Source: “In Denmark, wind supplied 29% of total electricity generation in 2015.”

Raw composer: “In 2015, wind supplied 29% of total electricity generation in Denmark.”

The literal denominator regex in `src/pilot/subtasks/_relationships.py` captures through punctuation. It compares “total electricity generation in 2015” against “total electricity generation in Denmark” and raises `Composed percentage denominator differs from selected evidence`. Country and year remain in the sentence, but their relocation changes the regex capture. The socket-blocked replay reproduces this with retained raw responses and zero inference. This establishes a conservative validation boundary failure; it does not establish general model reliability or safely authorize relaxing relationship checks.

Mapping selected the correct wind span and partial state. No current-price claim or final gap disclosure was published because validation failed before safety/persistence. Their end-to-end behavior remains unverified.

## Evidence and accounting

See `batch-summary.json`, both raw stage records, both results, case wall-clock records, `cq-p01-source-assessment.json`, and `cq-p02-offline-replay.json`. The executed input snapshot preserves all contract-pinned files and records match status. Actual batch: four main calls, one NeMo wrapper; known main usage 2,304 input + 487 output = 2,791 tokens. NeMo internal usage remains unknown. Existing failures and owner records are unchanged.

## Exact next step after resume

Prepare offline synthetic regressions using different facts for trailing country/year reordering and real denominator substitutions. Propose the bounded validator contract change explicitly; retain strict negative tests for measure, number, country, year, denominator and forecast substitutions. No runtime repair was made in this diagnostic pass. Do not regenerate under the closed allowance; obtain a fresh specific grant after concrete offline preparation.

Manual review: cq-p01 is assessable but not owner-accepted. No manual rescoring is requested for cq-p02’s technical failure. Stored approval/export remains separate.

Paused under the standing quota instruction: five-hour 44% remaining; weekly 10% remaining. No active generation process remains. `git diff --check` passed with existing line-ending warnings. No new broad test run was needed for report-only diagnosis.
