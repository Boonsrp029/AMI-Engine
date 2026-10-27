# Monthly reporting context and duplicate claims

The retained r02 diagnostic selected the correct causal passage but composed repeated origin-market facts. Literal cause preservation now falls back to the selected excerpt; exact duplicate public claims are collapsed only after every originating unit passes scope, numeric, measure and component checks. Text and ordered citations must both match. `public_claim_coverage` retains all unit/component origins; distinct wording or citation order remains separate. This is not semantic deduplication or an entailment judge.

The subsequent offline replay retained the causal passage but left the observation period unresolved. The consumed source's heading coordinates a month and quarter with one explicit year; the older literal month/year parser did not recognize that form. The fix preserves that distinction instead of treating publication as observation.

## Narrow source binding

`src/pilot/_report_context.py` operates after evidence mapping. It reads at most two additional original corpus records, each at most 600 characters, for one explicit requested period. It requires:

- Matching pinned corpus digest, document identifier, URL and publication metadata.
- Preparation-format HTML unit locators, with one unambiguous report heading and monthly section declaration.
- Explicit month/year, or an explicit shared year whose stated quarter contains that month.
- Every selected factual record inside that monthly section, before the next explicit section/quarter boundary.
- No selected forecast, conflicting explicit date, context command or citation-budget overflow.

Other document formats and unsupported/ambiguous heading forms keep the existing unresolved-scope behavior. No country is inferred from publisher, URL or question. This does not establish that every comparison or quantity within a paragraph shares the report period; source-grounded human review remains necessary.

The mapper receives the original evidence catalog. Context is added afterwards, with unchanged source IDs/text and a `reporting_context` event. Stored provenance includes exact heading offsets/hashes, section identity, factual IDs and the next boundary's identity/hash. Qualified claims cite the factual record and both context records. These are internal application-computed bindings, not client-supplied permissions or an accepted API input.

The temporal backstop recognizes the same narrow shared-year grammar in original source context. Its necessary date check does not replace the component/section binding or final NeMo policy. The legacy query API, ranking order, public `Draft`, SQLite schema, model/settings, two tool rounds and four main-call ceiling remain unchanged. This context pass introduced prompt identity `analyst-pilot-v1.34`; the current integrated prompt is v1.36.

## Evidence and limits

The deduplication checkpoint passed 456 offline Windows tests. The model-identity checkpoint subsequently passed 472; further targeted worker tests exercised digest mismatch before/after fixed responses. Report-context tests cover offsets, publication-only rejection, invalid month/quarter, wrong documents, forecasts, monthly versus quarterly sections, tampering, context quotas, and a fixed four-call workflow with final guard invocation. These are engineering checks, not model-quality scores.

An offline replay of consumed r01/r02 now records the reporting month/year and retains distinct claims, including the missing r02 cause. Geography remains unresolved. No new generation or human approval is implied. All raw diagnostic failures and historical judgments remain unchanged. The revised 20-case set is still unattempted at this checkpoint.

The next bounded proposal is one p01/p02 pair plus consumed r01/r02, at most 16 main calls/four NeMo invocations, one attempt per case and 180 seconds each. Only all four technically valid, source-supported results can unlock the separately agreed 20-case gates. The previous diagnostic budget is consumed; new authorization is required. No Ragas, hosted inference, automatic retry or reviewer contact.

The subsequent actual v1.34 development gate failed on repeated r02 claims and omitted seasonal wording. The [shared-evidence repair](shared-composition-evidence.md) addresses those observed defects. A fresh v1.36 diagnostic budget is authorized; previous successes cannot unlock the new generator.

Current outcome: the separately authorized v1.36 development gate passed all four checks, unlocking the frozen v2 set. That run stopped on r06 mapping validation after four attempts; three returned drafts had scope/coverage failures and sixteen cases were unattempted. The qualification gate FAILED. See [complete findings and next repair gate](qualification-v2-findings.md). Earlier checkpoints above remain historical; no retry or new approval/export occurred.
