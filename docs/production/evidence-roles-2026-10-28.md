# Evidence roles and requested-subject repair — 28 October 2026

This is an offline engineering continuation after the failed v1.36 qualification. Prompt `analyst-pilot-v1.43` / mapper `requested-evidence-v29` has **no new generated-output quality evidence or owner acceptance**. Earlier outputs, judgments, exports and frozen packages remain historical evidence. No Ragas, hosted inference or local model generation is included in this pass.

## Changes and scope

The nine predeclared synthetic development fixtures are now executable checks in `tests/fixtures/evidence_coverage_v1.json`, `tests/test_pilot_quantity_roles.py` and `tests/test_pilot_topics.py`. They preserve the frozen fixture bytes and cover the following narrow contracts:

| Observed risk | Implemented check | Limit |
|---|---|---|
| A percentage token is present but has the wrong role | Parse literal percentage subjects and denominators; reject established FDI-subtotal, growth/level and value/count mismatches | Unrecognized grammar, aliases and implicit denominators remain unknown. This is not a semantic ratio solver. |
| Project count and money values exchanged | Validate declared value/unit pairs, preserving decimal sign and scale | Limited unit vocabulary; no exchange-rate calculation or general conversion. Source-provided approximate currency equivalents remain allowed. |
| Wrong financial subject fills an answer | Distinguish literal investment/consumption/inflation and explicit private/public/headline/core qualifiers | No general financial ontology. Synonyms such as capital formation remain unverified. |
| Category detail lacks a repeated private/public qualifier | Resolve a unique quotation's generic measure to a preceding specific subject within 800 characters of the same record | Never cross blank paragraphs, source IDs or a different measure. PDF extraction may have normalized paragraph boundaries; this is record-local provenance, not a guarantee of discourse meaning. |
| Definition substituted for cause | Reject selected definition-only evidence for a literal causal request; prefer matching explicit explanatory spans when available | A cause marker does not prove a causal interpretation. Mixed or unrecognized language still needs inspection. |
| One subject omitted from a compound answer | Reject a fully supported compound mapping when known subjects demonstrably leave another requested subject uncovered | Partial states remain valid; unknown evidence prevents this narrow conclusion. This does not prove complete answers or comparisons. |
| Only one period selected for a monthly/quarterly comparison | Reuse the existing literal retrieval-facet grammar to offer separate matching period/subject views and reject known one-sided supported mappings | Only this declared comparison grammar and pinned contexts are understood. Partial answers survive; unknown provenance is not made into missing evidence. Selected sides do not prove correct directions or complete category explanations. |

Before the mapper call, source-derived evidence views offer recognized requested subjects, comparison periods and unambiguous explicit ratios. Existing profile and contrast-view contracts retain priority. Missing/conflicting outputs remain possible; classifiers do not manufacture missing information or repair malformed model output. After mapping, known mismatches fail explicitly before composition, with `mapped_percentage_roles`, `mapped_requested_subjects` and `mapped_comparison_coverage` diagnostics. Final claim projection also checks literal numeric roles and known subject substitutions.

Public APIs, `Draft`, SQLite schema, model/context/completion settings, four main-call ceiling, final NeMo validation and exact-revision approval/export controls are unchanged. Requirements and constraints remain unchanged. No new model repair, fallback framework or extra inference call was introduced. Existing selected-evidence composition fallbacks retain their contracts.

## Retained-response findings

The retained r06 selected country-share span fails the requested FDI-share-of-all denominator check. A separate isolated development check identifies the already-retrieved explicit total-share span. That check exposed a parser defect: a heading ending in “Year-on-Year” contaminated the following ratio numerator. A narrowly matched heading-tail repair and positive/negative regressions now preserve the following FDI role. The original response, wrong-period failure and failed parser diagnostic remain untouched.

The saved r04 mapping also fails the requested-subject check for one component and the comparison check for its absent monthly side. r03's known period failure is handled by the [source-context pass](context-and-retrieval-2026-10-28.md), not proven correct by a topic match. r05 remains compatible with the narrow subject vocabulary: that is **not** acceptance of its wrong geographic/date interpretation. Unknown or compatible results do not establish overall correctness.

Raw engineering evidence is in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v3/quantity-v1/`, `topics-v1/` and `comparison-v1/`. Derived replays are explicitly assistant-authored and make zero model calls. Initial import failures, a mistaken test-file command, and failing antecedent regression checks are retained alongside their corrected runs. An initial inline comparison replay used Windows' default text encoding and correctly failed the pinned-content check; explicitly reading the unchanged UTF-8 evidence fixed that diagnostic without relaxing validation.

## Validation and next quality gate

Targeted current checks: 25 quantity tests, 24 subject/lifecycle tests and seven comparison tests pass. The comparison integration run passed 91 tests. The intermediate v1.42 checkpoint passed 600 Windows tests /599 Linux tests plus one Windows-only skip, and its no-inference recovery check passed. The final v1.43 checkpoint passes **607 Windows tests /606 Linux tests plus one Windows-only skip**, with 15 existing warnings, and the no-inference recovery check. Image `ami-pilot:qualification-9f5e3b51f3342249`, ID `sha256:ef5ae6d3e6a30f85b3e3b57a91398219cf7d487aafa8850b66ca21d2c1e38733`, matches sanitized build context `9f5e3b51f3342249f89b7769abc7bbcd3b8901e4e890db0731b3e12ebf74bc5c`. Four exact cached exports survive restart and empty d06 remains blocked. Both dependency checks pass without changes; remote CI and real container inference remain unverified. These synthetic checks establish contracts, not answer quality or production qualification.

Before more inference, inspect the exact packaged source identity and prepare one new bounded diagnostic authorization, as [proposed separately](diagnostic-proposal-v143.md). The consumed generation budget is closed. The proposed v3 twenty-case package remains frozen and unattempted; its changed answerable topic mix requires review before being used for final qualification. Do not tune against its replacement reference facts or report a matched improvement over consumed cases.

Remaining technical risks include complete monthly/quarterly comparisons, reconstruction of split source passages, semantic relevance, geographic meaning and dated-observation gaps outside the narrow price rule. Production gates in the [readiness matrix](readiness.md) remain open.

## Human checkpoints

No human scoring is needed for schema failures, rejected mappings, parser regressions or these fixed-response tests. New technically valid generated drafts will need source-grounded owner review before they can be called owner-accepted. Review claim meaning, requested coverage, dates, measures, denominators and gaps; a valid span ID alone is insufficient. Approval/export still requires the exact draft revision, and empty drafts remain ineligible. An independent reviewer session must be arranged by the owner before any independent-usefulness claim. No reviewer was contacted.
