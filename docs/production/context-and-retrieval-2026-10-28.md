> Historical v1.40 checkpoint retained below. The later [v1.43 evidence-role and comparison pass](evidence-roles-2026-10-28.md) supersedes its current-artifact labels; earlier test and replay results are unchanged.

# Reporting context and component retrieval — 2026-10-28

Assistant-authored engineering evidence. The full Goal remains active; actual quality qualification is still failed. No new model generation, human scoring, approvals or exports occurred in these passes. The proposed v3 final pool remains frozen and unattempted.

## Contracts and changes

| Pass | Previous behavior | Change | Evidence and limit |
|---|---|---|---|
| Source context, prompt v1.39 | A same-document heading could assign a month without bounded section proof. Wrong-report selections could reach composition with an unresolved-period warning. | Remove that fallback. Supply typed report/section hints before mapping; reject established selected-evidence incompatibility before composition. Keep publication-only and unsupported formats unknown. | Seven predeclared synthetic cases plus boundary tests; 82 integration checks. Full Windows suite: **544 passed**, 15 warnings. Compatible context is not semantic support. |
| Component retrieval, prompt v1.40 | A single fused query could fill the source budget with one topic or reporting period. | Use lexical rankings per canonical request; prefer compatible context, retain unknown candidates and omit known incompatibility. Deduplicate through round-robin selection within the existing result limit. Recognize a narrow explicit monthly/quarterly comparison grammar as two retrieval facets. | Six prototype tests and **66 integrated tests** passed. Full current Windows suite: **551 passed**, 15 warnings. Retrieval presence does not prove correct model selection or interpretation. |

The original 528-test checkpoint is historical. The source-context suite initially failed one old test that expected the removed unbounded heading behavior; the raw failure is retained. Its replacement asserts that a heading alone cannot authorize the date, while bounded positive coverage remains in the report-context suite. A retrieval integration test separately injects its deliberately incompatible record to isolate post-retrieval validation; filtering that record earlier is also valid behavior.

## Source-context boundaries

Only the pinned HTML preparation layout, matching corpus/document metadata and exact source content are understood. Header and section identities/hashes are retained. Explicit historical dates may differ from a newer report heading. Monthly context does not establish an exact day, a quarterly value does not supply a monthly value, and a forecast cannot answer an explicitly observed-outcome request. Mixed forecast/observation requests are not blanket-rejected.

Publication-only headings, unsupported PDF/assembled-record layouts and ambiguous provenance remain unknown. These checks do not establish that a matching quotation answers the assigned measure, geography, cause or percentage denominator. Source text cannot authorize actions. Existing span identity, citation validation, final NeMo and human approval/export controls still apply.

The mapper receives compact typed context hints rather than extra factual spans or source-authored instructions. Actual selected quotations remain authoritative evidence. Established incompatibility raises an explicit error; malformed mappings are not converted into abstentions or repaired by another model call. Missing and conflicting states retain their existing contracts.

## Retrieval boundaries and actual replay

The lower-level retriever and `Corpus.search()` retain their previous behavior. The existing corpus-pinned search profile also retains its path. The unprofiled analyst workflow uses `pilot-component-lexical-v2`; its identity hashes the policy and context dependencies. Original source strings, IDs and ranking ties within each context group remain unchanged. No embeddings, library versions, model settings, extra agents or model calls were added.

The comparison facets are retrieval queries, not new answer components or factual scope assertions. Supported grammar is deliberately narrow: explicit “How did … compare/differ month-on-month … and quarter-on-quarter …”. Other requests use their existing canonical clauses. Anaphoric category requests can share those facets. This does not provide a general natural-language intent parser or semantic relevance guarantee. A result limit remains a maximum, not a requirement to fill the budget with unsuitable records.

Read-only replay of the original failed tool arguments now includes:

- r03: December's summary and detailed inflation explanation (`BOT_DEC2024:unit:4:0` and `:unit:13:0`).
- r04: monthly private-investment detail (`:unit:9:0`) and the separate quarterly comparison (`:unit:14:0`). See the [locator correction](r04-locator-correction-2026-10-28.md).

The retained r03 mapping is rejected by the new context audit; valid consumed r01/r02 mappings remain compatible. None was regenerated or re-scored. Historical failed outputs stay failed.

## Remaining quality and human gates

Per-component topical relevance, complete requested comparisons/causes, percentage denominators and full source spans still need work. Neither a populated request slot nor exact quotation identity proves an answer is complete or correct. Do not request another generation budget merely because these tests pass.

Technically failed outputs do not need repeated human scoring. Any future owner-accepted output requires source-grounded human review, and export requires approval of its exact revision. The replacement final-pool topic mix needs review before qualification; independent usefulness still requires a real reviewer session arranged by the owner.

Evidence remains local in `reports/workflow_pilot/production-readiness-2026-10-27/resume-v3/`, including pre-edit snapshots, raw failures, test logs and saved-response/tool replays. The current v1.40 image passed **550 Linux tests, one Windows-only skip**, with 15 warnings, plus its no-inference recovery check. Docker was initially stopped; the failed connection log is retained, and the installed Desktop was started before building the same verified snapshot. No commit, push, external deployment, reviewer contact, Ragas or hosted inference is included.

The current image is `ami-pilot:qualification-9763a7df0c781026`, ID `sha256:33a2b6d1a352bc7ef13d8542e5bbcca3c996c68db28fdf38f9f234fd518909a9`. Local recovery retained all four exact cached exports and blocked empty d06. Both application and constrained serving dependency checks passed without package changes. Remote CI, real container inference, fresh model quality and production operation remain unverified.
