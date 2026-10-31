# Supported components cannot declare gaps — 31 October 2026

This is the first offline repair pass following the [failed consumed regression](consumed-regressions-v155-2026-10-31.md). It addresses the fully supported mapper state carrying an invented gap. It does **not** repair or qualify aggregate-versus-subcategory direction interpretation.

The private mapper now has separate supported and unresolved branches for each canonical request slot. The supported branch exposes `gap_anchor` as the empty-string constant. Partial, missing and conflicting branches retain their existing gap text, allowing specific unanswered question fragments rather than forcing every partial gap to name the entire request. Existing exact-question matching still applies after parsing; fabricated unresolved anchors remain invalid.

The base selection validator and lower-level mapping validator also reject nonempty supported gaps, so callers cannot bypass the rule by using an unconstrained private type. Invalid output is rejected, not normalized, dropped or converted into abstention. Instructions explicitly distinguish an answer/direction from an unanswered question fragment. Public Draft/API/storage contracts, span resolution, call ceilings, model settings, approval/export rules and dependency versions remain unchanged.

Prompt version is `analyst-pilot-v1.56`; mapper version is `requested-evidence-v38`. These are new code identities, not new successful model runs. The earlier v1.55 allowance remains closed; r05 was not attempted and no further generation is authorized by this repair.

Eight synthetic tests cover supported gap rejection in base and constrained parsing, schema constant exposure, preservation of granular unresolved gaps, and lower-level bypass rejection. Targeted checks passed **69 tests**. The first targeted run had six failures solely from the old hardcoded prompt-version expectation; the tests and raw failure log were retained, then the expected version was updated. No behavior assertion was removed.

Networking-disabled saved-response replay preserved the new r03 public draft exactly through current mapping/composition validation, stopping before safety with no model or NeMo call. The original r04 mapper remains rejected without modifying its saved response. These are fixed-response contract checks, not actual selection quality or a new NeMo verdict.

Full validation passed **1,048 Windows / 1,047 Linux tests**, with one Windows-only test skipped on Linux and 15 existing warnings per platform. Container restore/restart checks preserved all four cached exports byte-for-byte, with no model calls or new human decisions. Results are retained under ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v45/`. The image is a source overlay on the existing verified dependency image, not a fresh installation. Historical attempts, owner judgments and approved exports are preserved.

The remaining offline action is to test aggregate/subcategory direction attribution using canonical request subjects and distinct synthetic evidence. Merely finding both “stable” and “declined” in one selected passage cannot establish which measure changed. Do not remove invalid gaps from the failed response and then treat its incorrect monthly short answer as a success. Real-output quality remains failed/unverified until a separately authorized diagnostic demonstrates the repaired workflow.

No factual human scoring is needed for this engineering pass. The earlier new r03 draft still needs owner wording acceptance before that claim can be made; r04's technical failure does not need manual scoring. No new generated draft or stored approval/export was created.
