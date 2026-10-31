# Consumed r03–r05 diagnostic — 31 October 2026

**Regression gate failed; allowance closed at r04.** The owner explicitly authorized three consumed v1.55 cases after offline and Linux checks: one attempt per case, at most twelve main-model calls and three NeMo invocations, 180 seconds per case, stopping at the first technical/source/completeness failure. No retries or held-out run were authorized.

| Case | Actual outcome | Main / NeMo calls | Assessment |
|---|---|---:|---|
| r03 | Answered; process exit 0, no timeout, identity verified | 4 / 1 | Assistant frozen-case source/completeness checks passed; final NeMo passed. Owner wording acceptance remains pending. |
| r04 | Mapper validation failed; process exit 1, no timeout, identity verified | 3 / 0 | Invalid question-gap anchors; separate monthly aggregate-direction error. No composition or final safety call. |
| r05 | Not attempted | 0 / 0 | Stopped under the agreed rule; unused allowance closed. |

Known main-model usage was **8,455 tokens**: 7,824 input and 631 output. NeMo internal tokens and local monetary/energy cost remain unmeasured. Recorded worker elapsed times were 91.38 seconds for r03 and 26.24 seconds for r04; these are not a warm latency benchmark or a sustained workload result. Both processes finished within their runner deadline. Seven main calls and one NeMo invocation were used in total.

## r03: supported combined draft with remaining editorial limits

The headline-inflation claim retains energy inflation, subsidy-base effects and benzene-price causes from pinned BOT source unit 4. Core stability retains offsetting food/cooking and cleaning-equipment promotional movements from unit 13. Heading units 0 and 5 establish December 2024 and the monthly comparison. These HTML-unit locators are not PDF page numbers.

The headline claim used the logged source-excerpt fallback because the composer omitted a requested cause. Thus the assessed result is the combined application output, not model-only completeness. The new core claim explicitly names Thailand and December 2024. The headline claim remains report-context scoped, and unresolved-geography/report-heading/fallback/historical warnings remain. The owner's earlier country-wording request is not silently marked fulfilled. No owner acceptance, numerical human rating or approval/export is inferred from assistant source checks.

## r04: exact failure and source interpretation

The mapper returned parseable structured JSON with a normal stop, not completion-limit truncation. It supplied gap labels including `declined in December 2024`, which do not occur in the actual question. The unchanged resolver rejected the response with `Evidence mapping gap anchor is not in the question`.

A separate semantic defect is visible in the retained response: its monthly aggregate short answer is “declined,” but the selected complete monthly passage says aggregate private investment was stable; construction alone declined while machinery/equipment and vehicles increased. The selected quarterly passage does support a decline in vehicle/construction investment. Correct monthly and quarterly evidence was present and selected. This was not an evidence-availability failure.

An offline replay of the **unmodified** saved selection reproduced the exact exception with networking disabled and zero model/NeMo calls. No invalid fields were removed and no response was repaired to obtain a pass. Evidence establishes a mapping-contract violation and aggregate/subcategory confusion; it does not establish GPU insufficiency or an inherent limitation of all open-source models.

## Preservation, review and next action

Raw responses, tool traces, model identity, process outcomes, usage, source mappings, authorization and closed-budget records are retained in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v30/consumed-regression-v155/`, with diagnosis and a focused r03 review packet in `resume-v44/`. Historical attempts, source snapshots, frozen evaluation packages and human judgments remain unchanged. No application, prompt, dependency or model change occurred during the run.

The next technical pass should remain offline: constrain gap selection to application-provided requested-text choices, require an empty gap for fully supported components, and test aggregate direction against subcategory movements using distinct synthetic facts. Preserve strict span, anchor and scope validation. Any subsequent functional change needs a new version and evidence; no further generation may use this closed allowance.

**Manual review:** only the new assessable r03 wording/warnings need owner adjudication before owner acceptance. No repeated numerical scoring is requested. The r04 technical failure needs engineering diagnosis, not human scoring; r05 has no output to judge. Any future stored brief still requires exact-revision human approval before export.

This is consumed development evidence, not a fresh twenty-case benchmark. The frozen v4 qualification set, independent reviewer use, current-release CI and production deployment/operations gates remain open. No Ragas, hosted inference, twenty-case run, commit/push, external deployment, reviewer contact or approval/export occurred.
