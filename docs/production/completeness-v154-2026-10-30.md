# Requested value context and explicit comparison conclusions

The [owner adjudication](../pilot/owner-review-composer-v153-2026-10-30.md) rejected the original r06 wording for the value ranking and project comparison, while confirming the underlying facts. The existing validators caught wrong quantities and contradictory winners, but accepted correct counts without an explicit conclusion and a value-ranking answer without its selected monetary context.

## Focused functional change

| Current behavior | Improvement | Validation |
|---|---|---|
| A by-value ranking can mention project count while dropping selected investment values/share context. | For a recognized by-value request with selected ranking language and known monetary units, use the existing extractive fallback if the response omits those selected monetary/percentage facts. No rank, amount, currency or scope is invented from the question. | Synthetic ranking/value cases, incorrect amount/scale rejection and a consumed-response replay. |
| Correct project counts can leave the winner implicit. | After the existing literal count checks, append the requested more/fewer conclusion from the two supported counts when absent; report equality for tied counts. Log the operands, source assignments and derivation separately from extraction. | Independent entities/counts, more/fewer/tie, partial/ambiguous/different-period evidence, incorrect winners and omission cases. |

The prompt version is `analyst-pilot-v1.54`; mapping stays `requested-evidence-v37`. The two instruction additions request the same context and explicit conclusion. Public schemas, source IDs, retrieval ranking, model/context/completion/temperature settings, four main-call ceiling, final NeMo check, SQLite schema, exact-revision review/export controls and dependency versions are unchanged. No model repair loop, judge, framework migration or hardcoded BOI answer is added.

The value check recognizes a limited English request pattern and existing baht/USD quantity parsing. It does not infer exchange rates or repair unknown currencies. Comparison derives only recognized two-entity project counts with supported, unambiguous selected roles; partial evidence does not acquire a winner. Existing mapping checks still enforce pinned-document and scope compatibility. Incorrect recognized values/count relations are rejected by the validators rather than repaired by these new omission checks. Existing separately traced period/extractive behavior is retained.

Extraction keeps the selected source wording; it is not a guarantee that the ranking's measurement basis is semantically unambiguous. Literal arithmetic likewise does not prove source truth, general entity resolution or entailment. The resulting text, relevance, scope and warnings still need source assessment and final safety/human review. The 800-character/five-claim limits remain; overly long fallback material fails explicitly rather than being silently truncated.

## Offline evidence

- **102 targeted tests passed**, including 19 independent synthetic cases for this change.
- Full suite: **975 Windows passed / 974 Linux passed, one skipped**, 15 existing warnings per platform. Linux used a network-disabled verified-dependency image with current application hashes checked.
- Container startup, truthful readiness, validation redaction, zero-call scope rejection and restart/restoration pass. Four cached exports retain their hashes; the original backup is unchanged and disposable storage was removed.
- A generator-free replay of the consumed r06 response retains the selected 357.5 billion baht/43% context and adds an explicit China-more-projects conclusion, with separate extraction/arithmetic provenance. The old response, failed gate and owner-reviewed editorial candidate remain untouched. This replay is not new generation, a new benchmark or owner acceptance of the new exact text.

The actual offline validator was also rehearsed against the retained response: **20.64 seconds wall time** inside its 30-second phase, zero model/NeMo calls. That is one local timing observation, not an SLO or a guarantee of future cold-start time. The existing local model tag's digest was checked through metadata only; no generation request occurred.

Evidence is retained under ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v23/`. The next proposed [bounded actual diagnostic](composer-diagnostic-v154-2026-10-30.md) needs a new direct grant. Previous allowances remain closed. No new human ratings, stored approvals, exports, commits, pushes, external deployments or reviewer contact are included.
