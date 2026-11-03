# v1.67 qualification preflight failure — 2 November 2026

**Qualification stopped at p02. No held-out case ran.** The user's grant covered the prepared preflights and conditional twenty-case scope under the new qualification protocol. The side chat had changed the runtime to v1.67, so the old v1.66 identity could not be used. Source/protocol identities were refreshed for v1.67 while preserving the exact case roster, budgets, stop rules and exclusions. The old unexecuted proposal remains unchanged.

## Preparation and actual outcomes

Current-code offline checks passed: 1,256 Linux tests plus one skip, 23 controller checks and disposable non-root restart/restoration preserving four cached exports. The side conversation retains 1,257 passing Windows tests and a clean dependency check. The test image is a source-only overlay on unchanged dependency layers; it is not a fresh dependency rebuild, remote CI or an upgrade of the running Desktop service.

| Case | Actual outcome | Main calls | NeMo invocations | Time including preparation |
|---|---|---:|---:|---:|
| p01 | Answered; actual final NeMo and assistant source/completeness checks passed | 4 | 1 | 65.86 s |
| p02 | Technical failure during mapping validation; no valid final abstention returned | 3 | 0 | 28.09 s |
| Twenty held-out cases | **All unattempted** | 0 | 0 | Not applicable |

Total observed use: **seven main-model calls, one NeMo invocation**, 5,067 known input tokens and 417 output tokens, **5,484 total known main tokens**. Internal NeMo usage and monetary/hardware/energy costs remain incompletely measured. Both attempts stayed within their 180-second limit. The controller closed the allowance after the technical failure. No retry or replacement occurred; conditional held-out execution was never enabled.

## p01 source assessment and raw-composer limits

The synthetic source directly supports the shipment increase, storage-cost decrease and warehouse-capacity cause in the final answer. The definition of the storage-cost index was not substituted as a cause. The raw composer retained all requested facts; no application fallback was used. Scope/date warnings were conservative and recorded as nonblocking, with no owner waiver silently transferred.

The new conditional financial coverage checklist was not activated by this nonfinancial fixture. p02 failed before composition. This run therefore **does not establish that the side-chat financial raw-composer omission has been resolved**, even though p01's raw answer was complete. These are development preflights, not unseen benchmark scores or owner acceptance.

## Confirmed p02 failure

The source contains shipment projections and explicitly supplies no profit or audited financial statement. The model correctly selected `missing` and empty evidence, but returned `gap_anchor` as **“requested dated observation.”** That phrase is not in the question.

The decoding schema accepted a free-text gap string, then `validate_mapping()` rejected it with **“Evidence mapping gap anchor is not in the question.”** The prompt's missing-state example contains the same generic phrase. These are concrete contract/instruction contributors; the error occurred before the composer or NeMo, with valid JSON, normal completion and no timeout/OOM observed. The source-selection code was unchanged by the side-chat composition patch.

Socket-blocked replay reproduced the exact failure. A separate, explicitly labeled counterfactual changed only a copied response's gap field to the supplied literal question anchor. That reached the existing empty-claims abstention path with the full question in the evidence-gap message and zero actual model/NeMo calls. The real response was not repaired, retried, replaced or retrospectively credited as a pass.

## Next engineering action and boundaries

Align the missing-state decoder's offered gap values with supplied request anchors and replace the misleading synthetic example with a question/request-bound example. Preserve literal partial-gap fragments, strict anchor/quote checks, the selection-only contract and the rejection of malformed output. Do not weaken the validator or silently replace an invalid model gap during runtime. This is the proposed offline repair; it was **not applied inside this failed batch**.

No manual rescoring is needed to diagnose this technical blocker. p01 remains assistant-assessed, not owner-approved; earlier r05/r06 judgments remain resolved and unchanged. Any further actual generation needs a new bounded grant after offline repair and validation. Unused conditional calls cannot be borrowed from the closed allowance.

Local evidence is retained under ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v106/`: exact grant/refresh basis, protocol, source baseline, offline logs, actual attempts and model responses, source gate, deadline/call checkpoints, closed allowance, batch results, offline reproduction and integrity hashes. Protocol: `3cac296cd9383ce26897bca238d3b66a8f0307005abe58562f5a1b6064155098`. Generator: `5e7ae8b78dc50cee309558e1dc368db72dca5e3a707463a56b525e4e8f8789d3`.

Original data, prior owner records/exports, source PDFs, dependencies and runtime source remained unchanged during generation and diagnosis. No Ragas, hosted inference, approval/export, commit/push, deployment or reviewer contact occurred. Neither portfolio completion nor scoped production qualification is established.
