# Decision requested: mapper answer authorship

**Proposed private-contract migration; not approved or integrated.** Runtime remains v1.59 / mapping v39. No new inference budget is requested by this decision.

## Problem and evidence

The consumed r04 v1.58 mapper selected the appropriate monthly and quarterly evidence, interpreted both aggregate directions correctly, but omitted a monthly category and supporting explanations. The declared completeness gate failed and the conditional workflow did not run. v1.59 strengthens a separate projection fallback; it does not cure that mapper omission or change the failed result.

The current composer already reads full selected quotations rather than the mapper's shortened answer. Nevertheless, the current mapper contract requires a complete model-written `short_answer`; its output also participates in pre-composition direction, number and scope checks. Simply deleting this requirement or proceeding to composition would change the contract to pass an earlier failure. That is not proposed as a repair of the old run.

## Alternatives

| Option | Benefit | Cost and limitation |
|---|---|---|
| Keep complete model-written mapper answers | Preserves current private semantics; can paraphrase and summarize | Current local generation has omitted requested details despite selecting evidence. More reminders have no demonstrated benefit; any new model/settings proposal is separate. |
| **Selection-only mapper plus explicit application extracts (recommended)** | Avoids a second lossy paraphrase before the composer; exact selected text remains traceable | Changes private answer authorship and prospective diagnostic semantics. Extracts can be verbose, irrelevant or incomplete if selection is wrong. Strict size/scope checks can reject more requests. |
| Remove the mapper, merge stages, add repair calls or change model/framework | Could redistribute work | Changes architecture, budgets or settings and requires a separate migration. Outside this focused proposal. |

The recommendation addresses a redundant generative obligation, not the whole quality problem. It is not a claim that extraction guarantees factual support, relevance, complete retrieval or a good final brief.

## Concrete proposed contract

1. Introduce an explicitly distinct private selection-only wire format. It contains component IDs, states, required evidence selections and scope/gap fields; **no model-written answer field is permitted**. Malformed legacy responses are not adapted or repaired into it.
2. Keep the existing legacy selection schema, required `short_answer` field and lower-level import/API behavior available for compatibility. The runtime must explicitly choose the new version; neither missing old fields nor old diagnostic permissions activate it.
3. Resolve selected span IDs against the current retrieved catalog and original source identity, offsets, hashes and quotation checks. Only then compile the selected quotations, in selection order, into an application-authored extract. Log its origin, selected span IDs and source provenance separately from raw model output.
4. Keep the internal EvidenceMap answer field required. Populate it under the **new explicit application-extract contract**, rather than pretending it was generated or silently correcting the old answer. The extract includes every selected quotation without semantic rewriting or unrequested facts from other records.
5. Preserve states: supported/partial require evidence; missing uses empty evidence and extract; conflicting preserves the evidence and empty answer. Invalid states, IDs, duplicates, anchors or source commands fail explicitly. Missing facts are not fabricated, and malformed selections never become a valid abstention.
6. Keep the existing 800-character internal answer bound. A selection whose complete extract exceeds it fails; it is not truncated, summarized, silently split or partially discarded. Extending that bound or changing public claim limits is a separate decision.
7. Retain subject/period/measure/scenario checks, unknown-scope warnings, direction-conflict rejection, numeric validation, composition over full quotations, v1.59 fallback, final NeMo and exact-revision human approval. Direction/numeric checks on extracts become necessary source-consistency checks, not proof that the model reasoned correctly. Final composed assertions still need their existing checks.
8. Preserve public Draft/API, SQLite schema, legacy agent, dependencies, model/settings, retrieval and the four-main-call ceiling. No new model stage, judge, repair loop, automatic approval or export is added.

Dynamic request schemas should reuse existing canonical IDs and evidence-view restrictions with an explicit new component type. Existing default schema helpers and legacy callers remain compatible. Update runtime-specific fixed-response fixtures as an intentional migration, keeping independent tests that legacy omission still fails; do not delete tests merely to conceal the changed semantics.

## Offline prototype and limits

An unintegrated helper under `.pilot-work/production-readiness/prototype-extractive-mapper-contract.py` requires a separately versioned selection-only input and rejects an old answer field. For the experiment only, a derived selection-only record was manually constructed from retained r04 selections. Its compiled extracts retain the monthly category/causal details and pass the current engine's necessary mapper gates before composition. This is a **counterfactual conversion**, not a new-wire model response, a corrected historical attempt, a full draft or a quality success.

Ten negative controls rejected unknown or duplicate spans, missing status, unsupported state/evidence combinations, a supported gap, instruction-like source text, excessive extract length and the forbidden old answer field. Missing/partial compiler states were checked separately. Exact anchor semantics and full provenance remain engine responsibilities; the prototype alone does not establish them.

A limited length audit of consumed r03/r05 mappings and the derived r04 conversion found eight extracts between 82 and 529 characters, below 800. This does not establish compatibility for all questions or reserved qualification cases. Longer multi-span selections remain a real rejection risk.

The prototype does not solve wrong-but-valid span selection, incomplete source coverage, ambiguous causal meaning, irrelevant contextual text or unknown geography. It does not establish that the local model can produce the proposed wire reliably. The current actual failure and all owner judgments remain unchanged.

## Prospective validation and qualification

If adopted, implement and test the new explicit contract offline first: wire separation, full provenance resolution, required/invalid states, source safety, exact length failure, legacy compatibility, scope/anchor checks, composition and fallback, final safety and approval/export. Repeat appropriate full offline/container/recovery and protected-evidence checks.

Then prepare a new frozen model diagnostic and request its own bounded allowance. Evaluate selection relevance, coverage and compiled facts under the new contract, followed by final draft correctness/completeness if conditionally authorized. The requested facts and final quality thresholds stay intact. The earlier model-written-answer preflight remains a failure under its original contract; no historical benchmark is rescored to manufacture improvement.

Neither this decision nor offline integration authorizes inference, Ragas, publication, deployment, reviewer contact, approval/export or the twenty-case qualification set. Actual source-selection quality, new generated drafts, independent reviewer usefulness and deployment qualification remain separate gates.

## Decision and human review

**Approve offline implementation of the selection-only/app-extractive mapper contract**, or retain the model-written-answer contract. This decision is needed because the earlier instruction made model-written answers mandatory and prohibited filling omitted mapper fields. The recommendation changes that obligation explicitly and prospectively, rather than quietly overriding it.

This is a design decision, not factual adjudication. No human scoring is requested for prototype fixtures. New assessable final drafts will still require owner source-support and wording review, and exports require approval of the exact stored revision.

Detailed ignored prototype evidence is in `reports/workflow_pilot/production-readiness-2026-10-27/resume-v59/`. Current runtime checks remain the v1.59 offline checkpoint: 1,097 Windows / 1,096 Linux tests plus one platform skip, 15 warnings per platform. Those suites were not rerun for an unintegrated prototype.
