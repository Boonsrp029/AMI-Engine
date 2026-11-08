# Actual concurrent diagnostic v3 — failed mapping gate

**Qualification failed; allowance closed.** cq-p01 was attempted once; cq-p02 and all20CQ1cases remain unattempted. No retry, tuning, substitution or regrading occurred inside the batch. Original owner-interrupted actual-development-v1 remains separate and unchanged.

## Observed result

The model returned complete JSON (finish_reason stop) after one main request. Usage reported471input tokens and141output tokens (612total); model duration42.169seconds including14.105seconds load. End-to-end attempt57.047seconds. No composition, NeMo invocation, draft, approval or export occurred. Prior interrupted-request usage remains unknown. Monetary/hardware costs remain unmeasured.

The mapper used supported status with a nonempty gap_anchor. Offline replay of the retained response through the unchanged SourceSelection validator rejects it: Supported evidence cannot contain a gap anchor. This rejection is correct and must remain. The selected span is Canada's observed5.7% growth in2016; raw kind incorrectly says projection. The available Japan forecast (2.6% annually through2036) was omitted. There is no final answer to rate or owner-accept.

## Implementation diagnosis

The callback sent generic SourceSelection directly to constrained decoding. Its JSON schema allows any gap_anchor string even for supported states; the state rule lives only in a Pydantic model validator. The existing sequential path already uses constrained_selection in src/pilot/_choices.py, whose SupportedRequestSlot schema sets gap_anchor to Literal[""], and constrains request IDs/states. C bypassed that more specific decoder contract. This is a concrete integration gap, not evidence of inherent open-source-model or GPU limitations. Low observed token counts and normal stop provide no sign of truncation.

## Next offline technical action — separate from this closed batch

Reuse the current constrained-selection builder in C with canonical request slots and source-span choices. Preserve all post-resolution validation. Add regressions with different synthetic facts for state literals, invalid IDs and no-repair behavior. Recount schema/context budget after changing decoder schemas. Do not assume schema repair fixes the separate missed comparison component or observation/forecast interpretation. Require source/completeness gates in any later actual diagnostic. No further inference is authorized by this failed batch.

Raw/parsed evidence and the exact validation replay are in v3-mapper-failure-diagnosis.json and actual-development-v2/. The code used is copied into v3-failure-snapshot/ before any later repairs; contract source hashes still matched at close. No manual semantic review is requested for this technical failure.
