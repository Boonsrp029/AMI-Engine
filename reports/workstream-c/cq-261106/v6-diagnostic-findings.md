# Actual v6 result — composition gate failed; allowance closed

**Qualification did not pass.** cq-p01 ran once and failed before safety/persistence. cq-p02 and all twenty CQ1 cases remain unattempted. No retry, warmup, tuning or case substitution occurred within the batch. The v6 grant is exhausted/closed under its first-failure stop rule.

## What actually ran

Two main calls, zero NeMo invocations, 36.281 seconds including preparation. The retained main responses report 1,521 input and 264 output tokens, 1,785 total; both finished normally (`stop`). Failed-worker metrics did not propagate those counts, so the raw response records are the authoritative known usage evidence. No draft or revision was persisted (revision zero); no approval/export occurred. Monetary/hardware cost remains unmeasured.

The mapper selected both exact supporting spans: Canada's observed 5.7% electricity-demand growth in 2016 and Japan's projected 2.6% annual growth through 2036. Schema, selection resolution and required branch coverage passed far enough to invoke composition. This one observation supports structural coverage of this consumed case; it is not an unseen completeness score or general mapper-quality result. Its global geography label was Canada alone; no final multi-country draft passed, so full geographic interpretation is not credited as qualified.

The raw composer repeated this sentence for both u1 and u2:

> Canada had 5.7% more observed electricity demand in 2016 than Japan had projected electricity demand through 2036.

Neither source establishes that relative comparison. The first unit contains Canada/5.7%/2016 only; the second contains Japan/2.6%/annually/2036 only. The text both transfers facts between units and omits the supplied projection rate. A historical growth observation and a future annual growth projection do not establish a relative demand-level difference.

## Confirmed rejection and diagnosis

Zero-inference replay of the exact retained responses raises **`Draft introduces a numeric value absent from its selected evidence`**, at `synthesis.project_report()` → `_scope.validate_claim_measure_and_numbers()`. The original JSON bytes remain unchanged. The first claim introduces 2036 outside its selected unit; the second repeats 5.7% and 2016 outside its selected projection unit. Validation stopped before NeMo or fallback publication, as intended. An invalid nonempty claim is not silently replaced with an extract.

This is a composition evidence-binding failure. Both facts were retrieved and selected. Both responses are complete JSON with normal stop reasons; there is no evidence here of truncation, GPU-memory exhaustion, an inherent open-source-model limitation or a hosted-model requirement. It resembles the retained r07 failure but does not replace or regrade r07. Actual post-NeMo publication remains untested by this batch because safety was never reached.

Existing composition instructions already require unit independence, preservation of rates/periods and no prior-unit duplication. The payload supplied separate u1/u2 quotations and source-literal cues. Thus another assertion that the prompt mentions these rules is insufficient evidence of repair. `composition-unit-scope-proposal.md` records the next private instruction-contract proposal without activating a new run or changing the shared sequential composer.

## Retained and offline evidence

- `actual-development-v5/`: original started/result/raw response/SQLite history/stopped artifacts; cq-p02 has no attempt marker.
- `v6-offline-replay.json`: exact captured composition inputs, rejection stack and original JSON hashes; zero live calls.
- `v6-failure-source-snapshot/`: exact runtime implementation snapshot before subsequent regression-only edits.
- `v6-diagnostic-findings.json`: structured findings, counts, source/contract identities and preserved artifact hashes.
- `v6-failure-regression.txt`: **42 targeted offline passes**. Two new cases use different Portugal/Sweden facts and verify that complete mapping cannot authorize the same unsupported relative sentence in either evidence unit; both reject before safety. Positive full-selection/provenance checks remain included. No application source or dependency changes were needed to retain rejection.
- The preceding full suite was **1,570 passes,14warnings**. It predates these two new regression cases; a new full-suite count is not claimed. No broad rerun was needed for regression-only additions.

## Human review and next step

No manual rating is requested for this hard rejected output. It is not an assessable saved draft and cannot be approved/exported. New technically valid outputs will require owner source/wording review before owner-acceptance claims. Independent reviewer usefulness and production qualification remain separate unmet gates.

The next safe step is offline review/implementation of a concurrent-only unit-scope composition contract, preserving free-prose interpretation, strict validation, raw/fallback/editorial distinctions and the existing call ceiling. A future actual diagnostic requires a newly frozen source/prompt contract and explicit grant. No CQ1 run or additional inference is authorized now. Shared five-hour usage remains unavailable; no reading is invented.
