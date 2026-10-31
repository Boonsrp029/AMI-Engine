# Actual composer preflight — 30 October 2026

**Technical validation passed; frozen completeness gate failed; allowance closed.** After the owner requested offline work first with the composer diagnostic as a fallback, the CI byte mismatch was reproduced/repaired and model-free composer checks were completed. Actual new drafting behavior was still unverified, so one local composer request used that conditional fallback within the already described protocol. The exact owner wording and its interpretation are retained alongside the machine-readable authorization label. No unrestricted batch was authorized.

## Actual output and bounded findings

The model returned three claims: FDI represented 73% of total application value in 2024; Singapore led the FDI source rankings with 305 projects; Singapore had 305 projects while China had 810. Parsing, projection, citations and count validation passed. No deterministic fallback or editorial correction was applied to that output.

| Component | Source support | Frozen gate finding |
|---|---|---|
| FDI share | Correct share, total-value denominator and 2024 period | Passed |
| Leading source by value | Singapore's identity and 305 count are supported | Leadership is presented with project count only; value basis and the frozen criterion's 357.5 billion baht / 43% value figures were not stated |
| Project comparison | Both entity/count associations are correct | The frozen criterion required an explicit statement that China had more; the output leaves that conclusion to the reader |

The selected support is in the pinned BOI release, zero-based PDF index 1 / PDF page 2: `BOI_2024:unit:1:2` and `BOI_2024:unit:1:3`. The value-ranking passage establishes 357.5 billion baht and 43% of FDI application value for Singapore; the count passages establish 305 versus 810. [BOI source release](https://osos.boi.go.th/article_attach/PR4_2568EN.pdf).

These omissions are not invented numbers or reversed counts. The original question asks for the leader by value, not explicitly for every additional value figure; the gate was stricter. Owner review can inform future wording/criteria, but cannot retrospectively turn this frozen failed batch into a pass. The value-basis ambiguity and explicit-answer clarity remain useful product questions to adjudicate before more tuning.

## Invocation, timing and safety boundary

One local composer request used **921 input / 122 output / 1,043 total known tokens**, finish reason `stop`; model identity matched before and after. Total two-phase diagnostic time was 51.656 seconds. Supervisor records show 21.453 seconds for service and 30.047 seconds for offline validation, including process/orchestration overhead; the validation process did not report a timeout. The phase was near its 30-second boundary and does not establish a production timing guarantee. The overall 95-second bound was met.

Native service metadata reports 14.745 seconds total, including 11.398 seconds loading. This is a single cold request, not a warm p95 or sustained workload benchmark. Source/correctness/completeness findings remain separate from latency and schema success.

NeMo was intentionally not entered in the composer-only preflight. The full conditional workflow did **not** run because the completeness gate failed. No retry, Ragas, hosted inference, twenty-case run, stored approval or export occurred. Unused workflow/NeMo allowance cannot fund another attempt. Successful completion of this request did not exercise backend cancellation.

## Owner review and next action

An ignored local packet in `resume-v14/composer-only-r06-v153/review-packet.md` contains the unchanged raw/projected output, source excerpts, unresolved questions and a separately labeled assistant editorial proposal. Review is optional source/wording adjudication of this technically valid output, not repeated scoring of a parser failure. Reviewer identity, numerical ratings and original `human_review.csv` remain untouched. No proposal is treated as owner-approved or model-generated.

Before another generation pass, resolve whether the value qualifier and explicit comparison conclusion are required, and whether additional value figures are optional context. Any implementation change must preserve request/evidence separation, citation identity, supported partial answers, fixed work bounds and final NeMo. Do not add a repair model or hardcode the BOI answer into runtime. A complete workflow still needs a separately authorized actual run and exact-revision human approval before export.

The [CI byte repair](frozen-byte-ci-repair-2026-10-30.md) remains a separate offline success, pending owner commit/push and remote rerun. Historical artifacts, model settings and dependency versions were preserved. The full portfolio/production Goal remains incomplete.
