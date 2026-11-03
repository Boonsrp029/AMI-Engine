# Financial decoder coverage repair — 2 November 2026

This offline pass follows the [failed r05 v1.62 diagnostic](reduced-r05-v162-findings-2026-11-02.md). Runtime is now **analyst-pilot-v1.63 / requested-evidence-v43**. The selection-only wire, public APIs, Draft/SQLite shape, source retrieval, model/settings, dependencies, approval/export controls and historical failed result remain unchanged. No new inference is performed in this repair.

## Structural change and its limits

Previously, the decoder permitted any subset of financial span choices, while the application required available current/baseline/change roles. The actual mapper omitted the offered prior-year monetary baseline, parsed successfully and then failed validation.

For small unordered financial views, the decoder now offers explicit complete evidence sequences for supported and partial states. It includes every valid order, optional evidence and a shared span only once, rather than requiring duplicate identifiers for roles satisfied by the same text. The application still resolves every identifier and verifies provenance, coverage, scope, quantities and extract limits. Nothing inserts unselected evidence or converts malformed output into abstention.

Enumeration is deliberately bounded: at most five candidate identifiers and 32 complete sequence alternatives. Larger or more combinatorial views retain their full eligible choice set, a necessary minimum evidence count and the existing mandatory runtime coverage validation. This fallback avoids uncontrolled schema growth and does **not** guarantee decoder-level role coverage. A sufficient count can still select the wrong roles; the runtime must reject it. No candidates are silently discarded to fit the decoder budget.

Missing and conflicting states retain their separate contracts. They are not forced into supported evidence choices. False abstention, irrelevant evidence selection and semantic misinterpretation remain possible. Complete role coverage is a structural condition, not proof of truth, geographic applicability or completeness beyond the recognized question grammar. Other request types retain their existing decoder conventions.

## Validation

Thirteen new synthetic tests extend the retained 1,181-test Windows baseline. They cover supported/partial omissions even when a second optional span is present, every small-catalog order and duplicates, exact selected-text retention, unresolved states, bounded large-catalog fallback and malformed internal coverage. Existing tests retain shared-span behavior, composition fallback, guardrail rejection and workflow call bounds. An existing failure assertion now checks that rejection occurs at schema parsing rather than the later coverage validator; it still requires no composition or guardrail call.

The two new omission tests first failed against the old implementation, proving the decoder mismatch. An initial fixture failure during the repair lacked coverage-role metadata; the fixture was completed without changing the production validator. Failed logs are retained alongside final results.

Final results:

- **86 targeted tests passed.**
- **1,194 Windows tests passed**, with 15 existing warnings.
- **1,193 Linux tests passed, one skipped**, with 15 existing warnings; networking disabled and image/source hashes checked against the sanitized current snapshot.
- Dependency checks report no broken requirements. No dependency files or versions changed.
- A non-root disposable container restored a read-only copy of the owner-history backup, restarted successfully and preserved all four cached approved exports byte-for-byte. It created no human decision or model inference; original owner history/backup remained unchanged. The isolated empty-claim export block also passed. This is not an actual deployment-outage drill or production RTO qualification.

Linux used a source-only overlay over the existing verified dependency image. It is not a fresh dependency rebuild, remote CI run or upgrade of the running Docker Desktop application.

## Saved-response replay and schema size

With sockets blocked, the unchanged actual r05 response now rejects at schema parsing. A separately labeled counterfactual fixture selecting the available monetary baseline reaches the composition boundary through the actual engine without invoking composition or NeMo. This fixture is not a corrected historical result, new generated success, source-quality gate pass or owner-approved draft.

On the retained r05 question and tool turns, serialized schema size grows from **8,122 to 17,736 characters**; message content remains **13,434 characters**. Native UTF-8 request body grows from **22,726 to 32,340 bytes**. Exact current token count, live grammar behavior and real selection quality remain unverified. Model context/completion settings remain 4,096/900; no context-fit or latency guarantee follows from these character counts.

The failure, raw service response and v1.62 contract remain immutable. Evidence for this repair is in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v83/`, including before hashes, red/green tests, socket-blocked capture/replay, Linux snapshot, image identity and recovery results.

## Next gate and manual review

A fresh bounded diagnostic proposal must bind the new generator, request and criteria before a new direct grant. All earlier inference allowances remain closed. Do not reuse the failed v1.62 controller/protocol or describe its result as repaired by this offline replay.

No manual scoring is needed for these engineering checks or the retained technical failure. A later assessable generated final draft needs owner source/wording review; exact stored approval/export and independent reviewer usefulness remain separate human actions. Fresh held-out quality, intended-release CI and actual security/operations/Databricks deployment qualification are still required by the full [Goal](../production-readiness-goal.md). Neither milestone is complete.
