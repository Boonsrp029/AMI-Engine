# Exact-revision owner decisions and exports — 2026-10-26

This addendum follows the [review checkpoint](review-checkpoint-2026-10-26.md). The owner replied directly to the exact-revision packet, approving d01, d03 and d04 revision 2 with source support confirmed, and requesting a change to d02 revision 2. The earlier packet and its pending-status statements remain historical records.

## Approved and exported

| Case | Approved revision | Draft/source digest | Export SHA-256 |
|---|---|---|---|
| d01 | 2 | `f180e0b818a13c75ed6940c5e4deeac885893a20c983923ac7cb48b8790c4fc7` | `792c871cb743e828d388584088adb7c0f4344d4bcfbd408412ee9582ede09a2c` |
| d03 | 2 | `38744c3e535e9de98c8b5cc81622616831670532e11182fb107b9eb5ca4f1102` | `96c0a2c30a74d236f781ea23c745eb1d5504bacbb9c12c522c5a89075c69a61b` |
| d04 | 2 | `505a79ab513f6a76130d2b869a14e08075f03163229d08cfe072fa59bb42f2ca` | `058647ea676f072f486a3f4d4d8d56131cbfa24e04cc88d266c2eb09c3ed0d1b` |

Each approval is recorded under `sirapop-owner`, with the owner's explicit source-support confirmation and exact revision. The draft and source digests were verified before applying decisions. The existing lifecycle created exports, whose saved UTF-8 bytes match cached database content; repeated exports were identical. The files are in the ignored local `reports/workflow_pilot/owner-decisions-2026-10-26/approved/` directory. No numerical human ratings, usefulness or task-time measurements were invented.

The unresolved geography/reporting-context warnings in the approved drafts were retained. The assistant's earlier source inspection and the owner's explicit source-support confirmation are recorded separately; approval does not mean that the model independently resolved scope. d03 remains an editorial proposal accepted by the owner, and d04 remains a rendering of a frozen model response. These decisions are not fresh-model, external-review or production evidence.

## d02 revision 3: owner-directed change, approval pending

The two overlapping headline-inflation claims were merged using the owner's requested sentence:

> Headline inflation increased in Thailand in August 2026, driven by higher fresh food prices from lowered agricultural output due to adverse weather conditions and rising production costs, as well as higher energy prices following an increase in global crude oil prices.

The separate core-inflation explanation remains, because the question requests headline **and** core inflation. The two original source identifiers, source content and page indexes are preserved. BOT PDF pages 1 and 6 remain the locators; exact excerpts are in the local packet. The headline sentence agrees with the retained passages about agricultural output/weather/production costs and energy/global crude oil. This is an assistant source assessment; the new revision has not been owner-approved.

The new revision digest is `ea55c67b58767c0f533c4e6a6859d7266066603afed6832d269aca9637d73d6c`. Its state is `needs_review`. Export remains blocked. d02 revision 2, its original generated response and earlier source assessment were not overwritten.

The [focused local review packet](../../reports/workflow_pilot/owner-decisions-2026-10-26/review-packet.md) contains only this new review request. A decision must name **d02 revision 3**; the owner's request to change revision 2 is not recorded as approval of revision 3. Empty d06 remains unchanged, unapproved and unexported.

## Formatting change and verification

The owner requested prose without decorative bullet characters in this and other cases. The pilot's draft validators now remove decorative source bullet glyphs from claim text, titles and warnings while retaining words, units and citation identifiers. Bullet-only claims/titles fail validation. Generated claim text is normalized before the final safety check. The browser brief/warnings and new Markdown exports use paragraphs rather than bullet lists. Exact source snapshots/quotations and already cached exports remain unchanged; this does not rewrite historical evidence.

The full offline suite now passes **341 tests with three existing warnings**, including regression checks for bullet removal before guardrails, retained mathematical symbols/dates/units, unchanged source evidence, exact cached-export bytes and approval requirements after an edit. `git diff --check` passes. No dependency or model-setting changes were made.

No new workflow generation was run. One configured local NeMo invocation checked d02 revision 3 and returned passed; internal calls/tokens are unavailable. The diagnostic process printed its completion message and persisted the revision, then returned exit code 1 without a traceback. An independent no-inference verifier confirmed the actual revision, three approvals, three exports, hashes and unexportability of d02/d06. The unexplained nonzero process exit is retained as a diagnostic limitation, not reported as a clean process result; no inference retry was performed. The guardrail result is not proof of semantic correctness.

The selected Goal checkpoint now has source-assessed drafts, owner-confirmed exact-revision approvals and verified exports, and a concrete remaining human-review checkpoint for d02 revision 3. This closes that bounded engineering/review/export objective, not the broader project. External reviewer usage, fresh held-out quality evaluation, general semantic reliability and production qualification remain pending.

Detailed provenance is in the ignored local decision directory and the [structured decision record](evidence/owner-decisions-2026-10-26.json). No commit, push, external deployment, Ragas run, hosted inference, Databricks call or reviewer contact occurred.
