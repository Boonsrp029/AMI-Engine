# Concurrent question-span contract — 7 November 2026

## Failure and scope

The actual v7 development batch passed cq-p01 and stopped at cq-p02. The mapper
selected the available historical wind fact but transcribed that source sentence
into a free-text `gap_anchor`. It was not part of the question. Existing strict
validation rejected it before composition, safety or publication. The closed
allowance is not reused. See the retained [actual report](../../reports/workstream-c/concurrent-qualification-2026-11-06/title-lineage-2026-11-07/v7-diagnostic-report.md).

This private concurrent-only change replaces that transcription with position
selection. It does not change the sequential mapper, public Draft, retrieval
ranking, model settings, dependencies, safety policy or approval/export controls.
The C-owned callback and private decoder own the change; A's scheduler/persistence
and B's retrieval interfaces are unchanged.

## Wire and resolution

Mapper version: `cq-mapper-v6-question-spans`. Wire: `cq-question-span-v1`.
Every component requires its canonical ID, state, evidence selection and `gap`.

| State | Required gap | Application resolution |
|---|---|---|
| supported | `null` | Empty gap, preserving existing supported-state validation |
| missing | `null` | Existing canonical requested-component anchor |
| partial | `{start, end}` | Exact substring of the original full question |
| conflicting | `null` or `{start, end}` | Empty or exact selected question substring; conflict stays distinguishable |

Offsets use Python Unicode code points, start inclusive and end exclusive. They
are not UTF-8 bytes or JavaScript UTF-16 code units. Bounds are strict integers;
booleans, floats, strings, reversed/empty/out-of-bounds and whitespace-only spans
are rejected. No missing field, unknown ID or old wire is silently repaired.

The full question remains available up to the existing 1,200-character limit.
All nonblank substrings remain representable, including shared dates outside a
component's shortened anchor, noun lists, Thai, emoji and combining characters.
Up to 32 sparse token-position hints help selection. When sampled, the payload
states so explicitly; hints neither restrict valid positions nor remove text.
No quadratic enumeration of all substrings is embedded in the grammar.

Application resolution produces the existing source-selection shape and then
executes its state, exact quotation, source, scope, coverage and composition
validators. New diagnostics retain the raw range wire, resolved old shape and
per-component position/membership trace. Raw composition, deterministic fallback,
source extracts and later editorial changes remain separately identifiable.

**Membership is not semantic support.** An in-range span may still describe the
wrong unanswered component. Relevant evidence selection, factual relationships,
complete requested coverage and useful gap wording remain actual quality gates.

## Offline checks and migration boundary

The targeted suite has 94 passing checks, including different synthetic facts,
supported partial output, genuine absence, strict source identities, malformed
ranges, required fields, Unicode, hint sampling, composition and coverage checks.
This establishes contracts, not real-model success. The integrated suite's terminal
result is recorded separately in the [local handoff](../../reports/workstream-c/concurrent-qualification-2026-11-06/question-span-2026-11-07/handoff.md).

The original v7 failure was replayed with its executed source snapshot and network
blocked: all 128 snapshot hashes matched, the original question-anchor error was
reproduced, and the raw output remained unchanged. A current-wire parse rejection
of an old output is not reclassified as a semantic improvement. Old experiments
keep their old code; no live backward-compatible private-wire adapter was added.

An offline tokenizer audit finds all 20 CQ1 request budgets within the conservative
4,096 allowance (3,590–3,827 including 256 framing and 900 completion reservations).
Schema-format tokens are separate (7,723–18,790); grammar processing latency is
unverified. These counts are not server-observed token or timing measurements.

## Next gate and human decisions

A mapper-only request over consumed cq-p02 has been frozen without network access
in the [preflight proposal](../../reports/workstream-c/concurrent-qualification-2026-11-06/question-span-2026-11-07/mapper-preflight-proposal.json).
Proposed budget: one local mapper call, zero composition/NeMo calls, 95 seconds
total (60 service, 30 offline validation, 5 orchestration), no retry or warmup.
It must retain the wind fact and select the actual missing dated retail-price
request, not merely pass range validation. This proposal has **no execution grant**.

Owner source/wording review applies to the valid cq-p01 draft. No repeated human
scoring is needed for cq-p02's technical rejection. Future assessable outputs need
their own owner judgment; stored approval/export still requires exact-revision
review. A passing current two-case gate, CQ1 qualification, independent usage and
production qualification remain separate, unmet gates.
