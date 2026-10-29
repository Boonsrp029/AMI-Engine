# v1.48 workflow diagnostic — 28 October 2026

**Failed and stopped at r05's source-quality gate.** Three attempts completed technically, parsed and passed final NeMo; the third answer was irrelevant/incomplete. r06 was not run. The unused ceiling is closed and cannot fund changed-code retries.

The owner authorized r03–r06 once each, with at most 16 local workflow calls/four NeMo invocations and 180 seconds per case. Actual usage: **12 workflow calls, three NeMo invocations, 12,980 known input tokens and 1,312 output tokens**. Aggregate execution was 134.98 seconds across three cases, not a latency benchmark. Internal NeMo usage and monetary cost remain unknown. No retry, Ragas, hosted inference, approval or export occurred.

| Case | Actual result | Assessment |
|---|---|---|
| r03, inflation | Retained energy/subsidy-base-effect/benzene causes and the core-inflation offsetting movements, with December 2024 scope. | Declared source checks passed. The public draft and cited source records exactly match the [owner-reviewed v1.47 content](../pilot/owner-review-v147-2026-10-28.md); no repeated factual scoring is needed. The minor country wording request remains active. |
| r04, investment comparison | Retained monthly stability and all category directions/causes, plus the separately labeled quarterly decline. | Declared source checks passed. Exact draft/source identity links to the same prior owner review, with the country-wording correction separate from raw generation. |
| r05, total application value/count/growth | Returned institutional contact/address/telephone text, the correct project count/growth, and unrelated FDI growth/share. Omitted total application value and its growth. | **Failed relevance and completeness.** Technical success and NeMo's YES do not establish a useful answer. No human scoring of this known failure is needed. |
| r06 | Unattempted. | Stopped under the agreed rule. |

## Confirmed implementation defects

The required financial-subject view for r05 offered either an “INVESTMENT SERVICES CENTER” contact header or a Hong Kong-specific investment paragraph as the primary evidence for an overall application-value question. It treated the bare word “investment” as sufficient subject identity, preferred first source spans and excluded the needed total-value span from that request's narrowed choices. Required context can make selection worse when its classification is too broad.

The mapper's short answers contained the correct value/count/growth, but their assigned quotations did not support those numeric answers. Composition then used those selected quotations and produced the header and unrelated FDI facts. The pipeline validated exact quotation identity but did not check numeric answer-to-evidence compatibility before composition. Known facts were available: the tool-stage response had already stated the requested total value/count/growth.

The earlier duplicate-ID failure was absent, and the monthly period remained empty for this annual question. Those two repairs worked in this attempt without proving the workflow complete. All source/model/generator identities matched; processes exited cleanly with normal model stop responses. No OOM, malformed JSON or context-limit finish supports a GPU-capacity diagnosis or an inherent open-source-model limitation.

Next offline actions: stop compulsory bare-topic views, retain qualified subject handling, and check each mapped numeric answer against its own selected quotations after reporting-period context is established. Do not silently reassign IDs, invent evidence, suppress warnings or add a repair model call. These necessary checks cannot prove semantic relevance or full completeness; an actual source-quality gate remains required.

## Evidence and human review

Ignored artifacts are in `reports/workflow_pilot/production-readiness-2026-10-27/resume-v7/development-v148/`: raw/parsed responses, mappings, catalogs, request views, process/identity results, source gates, budget and summary. Generator identity: `ed28b0e4f57b19c3a819637671c36a6ee74c13644666bd5512b74ffdc00d5109`. Model digest: `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`.

The new `resume-v7/owner-review-v148/review-packet.md` links identical r03/r04 drafts to their existing adjudication instead of requesting duplicate factual scoring. The separate country-clarified editorial candidates implement the owner's minor change request; they remain unapproved and are not fresh model results. No new assessable case requires human factual review from this failed batch. Exact edited-candidate/saved-revision approval remains necessary before acceptance/export, and independent reviewer usage remains pending.

The v1.48 engineering record remains 723 Windows tests and 722 Linux tests plus one Windows-only skip, with 15 warnings and successful no-inference recovery/export preservation. Those tests did not establish end-to-end relevance. Fresh held-out quality, portfolio completion and production qualification remain unmet.
