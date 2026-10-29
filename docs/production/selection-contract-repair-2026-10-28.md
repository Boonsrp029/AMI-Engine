# Distinct selection and reporting-range repair — 28 October 2026

Prompt `analyst-pilot-v1.48`, mapper `requested-evidence-v33`. This repair follows the [failed v1.47 diagnostic](diagnostic-v147-findings.md). Two subsequently authorized mapper-only preflights passed their declared checks; no v1.48 full-workflow result, owner acceptance or production qualification is established.

The frozen r05 response parsed because its generated schema permitted repeated supporting span IDs. Later validation correctly rejected the same quotation repeated four times per component. The mapper also selected a monthly label from an annual reporting range. It never reached composition or NeMo, so no final answer exists for this case. A zero-inference replay retains the exact parser/validator mismatch.

The private selection schema now declares `uniqueItems`, including dynamically generated ordered evidence choices. Inherited parsing validation rejects repeated IDs per component without removing, reordering or repairing evidence. Separate components can still cite the same span. Existing downstream quotation, scope, citation and composition checks remain. Instructions explicitly say optional evidence is not a quota and IDs must not repeat.

**Schema declaration and local parsing tests do not prove the Ollama decoder honors uniqueness or chooses relevant facts.** A malformed response remains a failure. No retry, repair loop or new model is introduced. The first new gate must test actual mapper behavior with a new explicit budget.

Literal period choices now exclude full English month names used as endpoints of explicit `to`, `through` or dash-separated ranges. A separate standalone occurrence of the same month/year remains eligible. This prevents “January to December 2018” alone from supplying a December-only measurement label. It does not infer annual scope, alter source text or solve arbitrary date language. Existing standalone monthly observations and publication-date exclusions retain their contracts.

Synthetic fixtures were frozen before editing in ignored `resume-v6/contract-v1.json`. The new selection-contract tests initially failed 11 checks and passed five; after repair they pass. Targeted integration checks pass 64 tests. Full results: **723 Windows tests; 722 Linux tests plus one Windows-only skip; 15 existing warnings**. Both dependency manifests remain unchanged. The local image uses sanitized context `74b75212101c45eb34e4bcf7af0f08234fb89bee7ddf116ecb6ed1d2319f4967`; image ID `sha256:a5e6f453be55bc2f21bc54fd6f52a3ce29ec4f4af1d7c19bc8bf4416132d7bc3`. Its no-inference recovery check preserves all four approved exports and keeps empty d06 blocked. Final evidence is in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v6/`.

Library versions, local model/settings, retrieval ranking, public APIs, `Draft`, SQLite schema, four workflow calls, final NeMo and exact-revision approval controls are unchanged. Repeated IDs now fail during parsing rather than later semantic validation; that private failure-stage change is intentional and raw responses must remain retained. No inference, Ragas, commit, push, deployment or reviewer contact is part of this offline pass.

## Next bounded gate and human review

The [two mapper-only preflights](mapper-preflight-proposal-v148.md) tested unique evidence selection and annual range handling once each and passed their declared checks. Their two-call budget is closed. They do not authorize r03–r06 or the twenty-case pool. Actual full-workflow relevance and answer quality remain separate gates.

The unchanged v1.47 r03/r04 outputs received [owner adjudication](../pilot/owner-review-v147-2026-10-28.md): source support, completeness and usefulness confirmed, with minor country-wording changes requested. Separate editorial candidates implement that request; exact-candidate approval remains pending. Technical failures require engineering diagnosis, not repeated manual scoring. Any export needs approval of its exact saved revision, and independent usefulness still needs an owner-arranged reviewer session. Portfolio and production milestones remain incomplete.
