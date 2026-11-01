# Evidence-first mapper contract — v1.58

This is an offline-validated instruction/schema change, **not demonstrated model-quality improvement**. The full portfolio and production Goal remains incomplete.

## Retained failure

The authorized reduced r04 v1.57 diagnostic ran once on 1 November 2026. Transport, schema parsing and empty supported-gap fields passed. The mapper selected the relevant monthly and quarterly passages but answered both requests with only “declined”. Monthly investment was stable in the selected evidence; the quarterly direction was supported but its requested explanatory categories were omitted. The direction validator rejected the monthly contradiction. No full workflow, composer or NeMo ran. The entire allowance closed after one call (2,269 input / 118 output tokens; 36.516 seconds overall).

An offline replay with networking prohibited reproduced the rejection. Relevant source material was available and selected; the run does not demonstrate a retrieval miss, timeout, truncation, GPU-capacity problem or intrinsic limitation of open-source models. Historical results remain unchanged in the local evidence package.

## Observed contract inconsistencies and change

The instructions said to select evidence first, but the private response schema declared `short_answer` before `evidence`. Both supported examples used bare quantity values despite requesting complete answers. These are verified inconsistencies; they are not proven causes of the failed generation.

The private selection schema now declares evidence before the answer and describes the answer's requested measure, direction and explanatory coverage. Supported examples now demonstrate complete sentences, including a synthetic two-period causal answer with separate source selections. No consumed-case answer or reference fact is inserted into the examples. Mapping version is `requested-evidence-v39`; workflow version is `analyst-pilot-v1.58`.

JSON object order is not a semantic validation rule. The installed SDK emits the revised schema order, but this does not guarantee a model's reasoning or output order. The set of accepted field values and required fields is unchanged; descriptions and declaration order alone do not prove completeness. No answer is corrected, inferred or silently filled by this pass. Existing direction, citation, quotation, scope, gap, composition and final safety checks remain active.

The public Draft/API, retrieval, model/settings, four-call ceiling, SQLite lifecycle, approved exports, dependencies and legacy graph are unchanged. The old v1.57 request/authorization cannot qualify this changed generator or authorize new calls.

## Offline evidence

- 64 targeted tests passed, including required-field failures, both dynamic status branches, SDK request serialization, examples and existing direction/partial/missing contracts.
- The full suite passed: **1,075 Windows tests** and **1,074 Linux tests plus one platform-specific skip**, with 15 warnings on each platform.
- A network-disabled Linux source snapshot matched the test image. Image ID: `sha256:44b270591abb56bc3b4273358836ef4fc43bfa8f27ff7cbc16c14796f4834252`.
- Restart/restoration checks passed with zero generation or new human decisions; four cached approved exports remained byte-identical, and the original backup remained unchanged.
- The actual saved wrong-direction response still fails the unchanged direction check under v1.58 in a no-network replay. This is safety-contract preservation, not a successful new answer.

Docker was initially stopped, so the first image build could not connect. Starting the existing local engine allowed a source-only overlay build with existing dependency layers; no versions or settings were changed. Both the initial failure and later successful checks are retained.

## Next gate and human review

Before any new inference, freeze the exact v1.58 mapper request, source/model/generator identities and explicit completeness criteria, then obtain a separate bounded authorization. An acceptable output must interpret the aggregate direction correctly **and** retain the requested categories/causes; parsing, valid span selection or compatible direction alone cannot pass the quality gate. Stop on failure; no automatic retries, answer repair, held-out batch or transfer of unused prior allowance.

No human scoring is requested for the engineering failure or mocked tests. New assessable generated drafts need owner source/wording adjudication; stored export requires its own exact-revision approval. Independent reviewer usefulness and actual production qualification remain unfulfilled separate requirements.

Detailed local evidence: `reports/workflow_pilot/production-readiness-2026-10-27/resume-v53/` (failure) and `resume-v54/` (offline change). These are ignored reports; they are not published benchmark results.
