# Gated v1.49 diagnostic — 28 October 2026

**FAILED at r05; stopped and budget closed.** The owner authorized two mapper preflights followed conditionally by four consumed development cases. Both preflights passed technical and assistant source checks. r03/r04 then passed; r05 failed mapping validation, so r06 was not attempted. These are development diagnostics, not a held-out quality score or production qualification.

## Results and preserved identities

| Case | Parsing / technical result | Source assessment and owner status |
|---|---|---|
| m01 | Parsed; valid mapping | Correct synthetic application value/count and growth; selected body facts rather than contact/FDI distractors. Assistant-assessed pass. |
| m02 | Parsed; valid missing state | Correctly withheld an absent actual observation from historical application data. Assistant-assessed pass. |
| r03 | Answered; four calls and final NeMo pass | Draft and cited records exactly match the owner-reviewed v1.47 result. Existing factual adjudication applies; minor country wording remains requested. |
| r04 | Answered; four calls and final NeMo pass | Draft and cited records exactly match the owner-reviewed v1.47 result. Existing factual adjudication applies; minor country wording remains requested. |
| r05 | Parsed; numeric mapping validation raised `ValueError` after three calls | No composer or NeMo invocation, no final draft. Both a numeric-parser false rejection and an independent evidence-selection/completeness failure were reproduced without generation. |
| r06 | Unattempted | Stop rule applied. |

Prompt `analyst-pilot-v1.49`, mapper `requested-evidence-v34`, retrieval `pilot-component-lexical-v3`; local model `ami-llama3.1:8b-4k`, digest `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`. Model/settings/source/generator identity checks passed. The frozen protocol is [documented here](gated-diagnostics-proposal-v149.md); its pre-authorization status remains historical in the immutable contract, with the actual grant recorded separately.

## r05: two separate defects

The question requests 2024 BOI application value, project count, and each change from 2023. The retrieved catalog contains the answer: THB 1.14 trillion / approximately USD 33 billion, value growth 35%, and 3,137 projects versus 2,235, up 40%. Retrieval absence is not the explanation for this failure.

**First raised failure: numeric parsing.** The value component selected span `s_06f4819ea1b3527c` in `BOI_2024:unit:0:0`, stored PDF index 0 / PDF page 1. Its heading includes `USD33 Billion` and its body includes `1.14 trillion baht`; the short answer says `33 billion USD`. The numeric parser recognizes 33 in the answer but overlooks currency-adjacent `USD33` in the evidence. Consequently it rejects a source-supported number. The new validator must not be described as wholly correct simply because it stopped the run.

**Independent selection failure.** The change component claims 35% value growth and 40% count growth but selects `s_728ed11317b934dd` (project count) and `s_58a39dc17c9bf1d5` (FDI share/growth), both in `BOI_2024:unit:1:2`, stored PDF index 1 / PDF page 2. Neither selected passage contains 35%; that figure exists in the first-page value span instead. A replay validates each component independently and reproduces this genuine mismatch even beyond the earlier parser error. Fixing `USD33` parsing alone will not make this mapping acceptable.

**Independent completeness failure.** The first component combines requested value and count, but its short answer/evidence only covers value. It omits the available 3,137 project count. The second component gives count growth without retaining that level. The free-text second tool response had all requested figures, but it is not a validated final answer and cannot replace missing evidence selections or be promoted into a successful result.

Responses ended normally with `done_reason=stop`; no JSON parsing failure, observed out-of-memory error or completion truncation establishes a hardware explanation. This single response does not prove an inherent limitation of open-source models. Evidence selection, request coverage and parser behavior need separate correction and validation.

## Budget and evidence

Actual use: **two mapper calls plus eleven workflow calls, with two NeMo invocations**, within the authorized combined ceiling of 18 main calls and four NeMo invocations. Known usage: **14,886 input / 1,177 output tokens** across these main calls. Internal NeMo tokens and monetary cost remain unknown. The three workflow executions totaled 105.21 seconds; this is not a latency benchmark. No retries, Ragas, hosted inference, twenty-case run, approvals or exports occurred.

The ignored evidence directory `reports/workflow_pilot/production-readiness-2026-10-27/resume-v8/` retains the authorization, mapper fixtures/results/gates, workflow responses/traces/process outcomes, `development-v149/summary.json`, and `r05-frozen-diagnosis-v149.json`. Workflow attempt hashes:

- r03: `255c6d64063c293fd8f7166a3bb896b1922700f7c8269f91a5e207ed92f08a97`
- r04: `3baffdeffb2731d07a2dfd0478c113f84fab803a8e457603a49ef30e6f4622b2`
- r05: `4c121740d54ae370c1931535763b0aa7539fd432b54d446e46433855b320165a`

The retained 745 Windows / 744 Linux test results establish offline contracts for the frozen implementation; the actual failure shows their coverage limits. No application or dependency change was made during this diagnostic. Prior failed batches, owner judgments, original CSV and four approved exports remain historical evidence.

## Next engineering work and human checkpoint

1. Repair numeric tokenization for currency-adjacent amounts, with positive and negative fixtures that preserve rejection of genuinely absent numbers. Do not turn arbitrary identifier digits into financial facts.
2. Establish explicit coverage of value, count and their changes within compound requests. Check evidence assignment to each requested fact; do not silently reassign span IDs, borrow another component's evidence, accept FDI-subgroup substitutes or repair malformed responses with extra model calls.
3. Replay this retained response and synthetic boundary cases before proposing further generation. Keep parsing, numeric compatibility, semantic support and completeness as separate gates. Preserve the failed original; a corrected replay is not a fresh generated success.

No manual scoring is requested for r05 because it has no final draft. r03/r04 need no repeated factual review: identical content links to the owner's existing source-confirmed judgment and requested country edits. Accepting the separate editorial country candidates still requires exact-wording acceptance, and any later export requires approval of that saved revision. New technically valid outputs need source/completeness review before being called owner-accepted; independent reviewer usage remains pending.

The full Goal remains incomplete. Fresh quality, same-identity release checks, independent reviewer use, actual container inference/cancellation, current remote CI, scoped production security/operations and authorized Databricks deployment/rollback remain open. The stopped diagnostic's unused allowance cannot fund another attempt.
