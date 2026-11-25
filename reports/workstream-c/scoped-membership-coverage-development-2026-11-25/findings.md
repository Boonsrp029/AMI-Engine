# Membership coverage development outcome, 25 November 2026

The explicit user grant for contract 3525b6122ac0eeb8ba9dd6ed72d1ebe67d5a86d544c8b3a60216f3e45b80c897 was recorded and used for cq1-a48 once. The attempt failed its strict composition check. The allowance is closed. cq1-a24 remains unattempted. No twenty-case qualification ran.

| Stage | Observed outcome |
| --- | --- |
| Identity and retrieval | Frozen inputs verified; pinned local model admitted; source evidence retained |
| Mapper | Parsed successfully and selected the exact full passage containing both requested members |
| Composer | Parsed successfully, then failed completeness validation |
| Safety | Zero NeMo invocations |
| Persistence | Failed run retained, with no final draft |

The direct source is eia-generation-2023 at character offsets 2388–2569, span s_92faf2a6f901b323. It explicitly lists sulfur and tire-derived fuel in Other (utility-scale) sources. Both reached the reconstructed composer input, alongside required_requested_members containing both names. The actual raw sentence was “The EIA other utility-scale sources category includes sulfur.”

The new check rejected that sentence with “Raw membership claim omits a requested source-listed member.” The added instruction/checklist detected the omission but did not produce a complete answer. The same omission remains a model-composition quality failure. The guard is an engineering success only. No historical result was regraded.

Both raw responses report done_reason stop. The mapping used 133 output tokens and composition 62, under the 900-token completion allowance. This evidence does not establish truncation, insufficient GPU capacity or an inherent limitation of all open-source models. The mapper selected the required evidence successfully. The mapping stage reports 79.84 seconds, including 39.57 seconds of model load, which explains much of the latency but does not explain the omitted name.

The unchanged private composer schema still requires one free-text claim for the whole question. The two requested names appear in instructions/input data, not in separately required response fields. A necessary phrase-coverage check can reject an omission after generation while the decoder still permits it. The separate composition-contract proposal examines this distinction without activating a new path.

One of two planned development cases ran, with zero passing cases and one unattempted case. The attempt used two main-model calls and zero NeMo invocations, with 3,085 input and 195 output tokens recorded in raw-response metadata. The failure's persisted aggregate metrics report incomplete token accounting; the raw-response totals are the stronger evidence. Outer elapsed time was 122.188 seconds, within 180 seconds. Monetary cost is unmeasured. Zero retries or warmups.

actual-input-trace.json contains an offline reconstruction of the mapper/composer requests using unchanged pinned inputs and actual saved responses. It is identified as reconstructed rather than captured wire traffic. That replay made zero model/NeMo calls and reproduced the exact validation failure. failed-case-source-findings.json resolves the selected quote, content hash, URL and offsets. batch-summary.json preserves denominators and unattempted cases.

There is no final draft requiring owner semantic review or approval/export. The source assessment is assistant-authored. No failed attempt should be manually scored as a successful answer. The proposed contract change requires its own design review, offline implementation/checks and a new execution grant before further generation. The requested named-model final integration review remains pending; this actual diagnostic proceeded under the later direct execution grant without claiming that review had occurred.
