# v1.68 preflights and conditional qualification proposal — 3 November 2026

**Prepared, offline validated and not authorized.** The [missing-gap repair](missing-gap-contract-v168-2026-11-03.md) preserves the side-chat composer change. The old v1.67 batch remains failed and closed; its unused allowance cannot fund this proposal. The frozen v4 roster and acceptance checks are unchanged. No additional consumed-case run is proposed.

| Phase | Cases, once each | Main-model ceiling | NeMo ceiling |
|---|---|---:|---:|
| Development preflights | p01 then p02 | 8 | 2 |
| Qualification, only if both pass | Twenty frozen cases in existing order | 80 | 20 |
| Combined maximum | 22 | **88** | **22** |

Each attempt has **180 seconds including preparation**. Source inspection and orchestration take additional time. The sum of case deadlines is at most 66 minutes; this is not a completion-time or latency promise. No retries, warmups, extra diagnostics, Ragas, hosted inference, tuning, approval/export, publication, deployment or reviewer contact. NeMo internal token/call use and monetary/hardware costs remain incompletely measured.

## Gates and stop conditions

The agreed qualification thresholds remain **9/10** complete supported answerable outputs, **2/2** correct partial answers, **4/4** proper abstentions, **2/2** explicit conflicts, **2/2** safe injection outcomes and **zero critical unsupported or wrong-scope/date/unit/scenario/denominator claims**. Neither a schema pass nor a NeMo pass proves factual quality.

- Both preflights must pass technical, source/completeness and safety checks; p01 answers and p02 genuinely abstains.
- Inspect each actual raw output against pinned evidence before admitting the next case. Retain source locators, raw/fallback distinctions, usage, timings and failures. Human acceptance is a separate field.
- Stop and close the allowance on technical failure, timeout, identity/call/deadline violation, critical claim, or a failure in any full-pass category.
- One noncritical answerable miss may be retained under 9/10. A second stops the run. No regrading to continue, replacing cases, repairs, retries or tuning within the batch.
- At 90% five-hour usage, start no further case; preserve any bounded in-flight attempt and pause. Resume only on the owner's direction with identical hashes; never rerun a started case.

The controller verifies code/policy, roster, protocol and prior result/source-assessment hashes; it requires a new matching grant, uses exclusive started-case markers, seals used source assessments and returns failure to its caller on process or budget failure. It passes 32 synthetic checks. This admission machinery establishes traceability, not semantic support.

## Pinned scope

- Runtime: **analyst-pilot-v1.68**; mapping: **requested-evidence-v44**.
- Generator: `a15516b638f467c7c55ab3af7bc0663dcddc09d39b89180843583604217590c9`.
- Frozen package manifest: `36ab8c6f99cbd88385914a12f62139b16c99d76702db337dfe1bb7e0dcad5ce1`.
- Local model digest: `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`; same 4,096 context, 900 completion, temperature zero.
- Protocol: `92bb0c4c504a35ec84154ca1cfb8dfe91a6aedf5d869a120be7cf465b87c4290`.

The complete contract and expected identity are retained in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v108/`. There is no authorization or started-case file. Verification-only mode makes no inference request; an attempted run without a grant must fail before model access.

## Human checkpoints

No new human scoring is needed for the old technical failure. After this batch, review only new assessable outputs for source support, completeness, scope and wording before calling them owner-accepted; technical failures remain engineering diagnoses. Exact stored-revision approval/export, independent reviewer sessions, release publication and production rollout are outside this grant.

Proposed grant: **Authorize v1.68 preflights and conditional twenty-case qualification**.
