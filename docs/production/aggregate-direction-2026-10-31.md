# Requested aggregate direction check — 31 October 2026

The [consumed r04 failure](consumed-regressions-v155-2026-10-31.md) selected the correct monthly passage but summarized the aggregate as declining because a subcategory declined. The [supported-gap repair](supported-gap-contract-2026-10-31.md) addresses its separate invalid gap field. This pass adds an independent, narrow direction check; it does not repair invalid model text or establish that the model will now answer correctly.

## Scope and behavior

For the existing canonical monthly/quarterly comparison grammar, the checker uses the application's requested subject, compatible evidence for that period, and the existing declared financial-topic vocabulary. It recognizes a limited set of direct direction predicates attached to that exact qualified subject, then compares them with an explicit same-subject answer or a bare direction answer.

An opposite movement attached to a subcategory does not replace the aggregate's predicate. A known aggregate disagreement or conflicting selected aggregate directions rejects the supported/partial mapping before composition. The diagnostic event records the subject and source/answer directions; it does not label semantic support as proven. No automatic answer correction, retry, extra model call or retrieved evidence is added.

Unrecognized subjects, category-qualified requests, unresolved measure qualifiers, unknown period compatibility, negation outside the grammar, forecast markers and source instructions do not establish an observed direction. They remain unknown to this check. Unknown does not become a general rejection or semantic approval; existing scope/source/citation checks and human review still apply. Directions are not inherited between monthly and quarterly slots.

This is literal English pattern recognition for the declared subjects, not an ontology, general entailment judge or complete financial-measure validator. Complex qualifiers, indirect prose, growth versus level, causal completeness and other wording can remain outside its coverage. A valid span identity alone still does not establish interpretation.

The workflow version is `analyst-pilot-v1.57`; the mapper schema remains `requested-evidence-v38`. Public APIs, Draft shape, storage, model settings, four-call ceiling, dependencies, retrieval ranking and approval/export rules are unchanged. An explicitly contradictory mapping now fails instead of proceeding to composition. The previous v1.55 generation allowance remains closed.

## Evidence

Synthetic fixtures were recorded before implementation, using different facts and periods. Tests cover opposite aggregate/category movements, direct qualified subjects, synonyms, period-slot isolation, conflicting evidence, negation/forecast/command text, unknown subjects and unresolved measure qualifiers. A source-qualifier counterexample found that a real-valued source could be treated as an unqualified aggregate; the final refinement leaves that case unknown. The initial results and counterexample remain retained separately.

The final focused set passed **41 tests**. An isolated replay of the original r04 answers and selected spans rejects the monthly `down` answer against a `flat` aggregate while retaining the quarterly `down` match. This reconstructs only comparison-assessment inputs; it is **not** a valid repaired mapper response, new draft, model call or successful workflow. The full original r04 response remains invalid under the supported-gap rule.

Final validation passed **1,070 Windows / 1,069 Linux tests**, with one Windows-only skip on Linux and 15 existing warnings per platform. Container restore/restart preserved all four cached exports byte-for-byte without model calls or new review decisions. Complete evidence is retained under ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v46/`. Earlier and final validation outputs are kept separately. The final image is a source overlay on the existing dependency image, not a fresh installation. Cached approvals/exports, historical judgments, failed attempts and frozen qualification cases remain unchanged.

## Remaining qualification

Offline rejection of an observed error does not demonstrate useful real-model output. A separately frozen and authorized reduced diagnostic is required before another workflow or held-out batch. First assess mapper validity **and** source/completeness on retained development evidence; stop on failure. Do not treat removing invalid gap text or applying a hand correction as a new generation success.

No factual human scoring is required for this engineering check. The earlier new r03 wording still awaits owner acceptance if that status is desired. Any future assessable generated draft needs source review, and stored exports still require exact-revision human approval. No generation, Ragas, hosted inference, external deployment, commit/push or reviewer contact occurred during this pass.
