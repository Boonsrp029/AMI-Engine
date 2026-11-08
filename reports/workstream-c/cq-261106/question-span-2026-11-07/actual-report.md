# Actual mapper-only attempt — semantic gate failed

The specifically authorized attempt finished once on 7 November 2026. **The
allowance is closed.** No retry, composition, NeMo, full workflow or CQ1 run followed.

| Gate | Actual result |
|---|---|
| Frozen protocol/model identity | Passed before/after execution |
| Response | Complete JSON, normal `stop`; new private wire parsed |
| Source selection | Correct synthetic wind span retained |
| State | `partial`, consistent with an available wind fact and unresolved prices |
| Gap membership | Positions 44–47 resolve to the original question |
| Gap meaning | **Failed: those positions select `and`, not the missing price request** |
| Overall quality | **Failed**; no owner acceptance or approval/export inferred |

Question:

> Describe wind generation in Denmark in 2015 and provide Denmark retail electricity prices yesterday.

Selected source:

> In Denmark, wind supplied 29% of total electricity generation in 2015.

The source is an explicitly synthetic development fixture, not verified real-world
electricity statistics. The fact's 29% share, generation denominator, country and
2015 date remain together in the resolved mapping. Geography resolved to Denmark.
The application's intercepted composition payload retains that exact source unit.
**No actual composition request was sent and no draft was generated.**

The selected range is `{start: 44, end: 47}` and resolves to `and`. It does not
identify Denmark's retail electricity prices for yesterday. A user could not
understand the evidence limitation from that gap. This fails the predeclared
semantic/completeness checks despite passing technical membership validation.

## What the retained response establishes

The new wire prevented arbitrary source-text transcription into the gap field.
It did not solve semantic gap selection. The old v7 failure remains unchanged;
this is a distinct, newly retained failure. The actual token count fits the model
context, and normal finish metadata provides no evidence of truncation or GPU
exhaustion. Retrieval returned the available source. This does not establish an
inherent limitation of open-source models or a need for hosted inference.

The full imperative question currently maps to one canonical component. The
private payload includes all 14 word hints, including `and`, and permits every
valid character range. Selecting that conjunction is an observed failure; these
facts alone do not prove the model's internal reason for choosing it. The
validators establish state, membership, source identity and structural coverage,
not semantic identification of missing information. Do not patch only this word
or count a corrected range as a new raw-model success.

## Actual budget and timing

- **One main-model request**, zero composer calls and zero NeMo invocations.
- **730 input + 141 output = 871 known tokens.** No interrupted request in this
  attempt; earlier interrupted usage remains unknown.
- Service worker: 14.750 seconds; controller: 28.094 seconds; owned outer envelope:
  **28.468 seconds**, within 95. No timeout/retry/warmup occurred.
- Server finish metadata reports about 8.500 seconds total, including about
  5.075 seconds load time. These backend fields and client wall times measure
  different boundaries; this is not a sustained latency benchmark.
- Backend cancellation remains untested, and monetary/hardware costs unmeasured.

The controller's exit 0 means technical validation completed. Its original summary
correctly leaves source assessment pending. The separate immutable
`actual-mapper/assistant-source-assessment.json` records **quality_gate_pass=false**
and binds its exact input/output hashes. No earlier status was overwritten.

## Preservation and next action

`executed-source-snapshot/` preserves all **93 source/helper/test files** used by
the frozen protocol, plus request/proposal/context/protocol/grant files and an
output-hash manifest. Prior source snapshots, owner judgments, outputs and approved
exports were not changed. CQ1 remains **0/20 attempted**; the original nineteen
reserved cases remain untouched.

Before spending more generation, review a gap-contract change: derive explicitly
qualified unresolved-branch disclosures from application-owned branch outcomes,
while retaining full original-question scope and selected evidence. Do not infer
global information absence from empty retrieval. If precise requested subparts
need new plan annotations, propose them through A's contract rather than silently
changing the sequential parser. See [design decision](gap-contract-decision.md).

**Human review:** no repeated scoring of this failed gap is requested. Existing
cq-p01 wording/source review remains pending. A contract/design choice is the next
human decision; this does not approve/export a stored revision. Any future model
test needs a new explicit purpose, budget, frozen protocol and grant.
