# Fresh v1.66 qualification proposal — 2 November 2026

**Prepared and offline-checked; no model execution authorized.** The owner [accepted r05's new prose and source support](../pilot/owner-acceptance-r05-v166-2026-11-02.md). This proposal advances to the frozen balanced v4 pool, without another r03–r06 diagnostic or tuning on reserved answers.

## Order and maximum new budget

| Phase | Cases, once each | Main-model calls | NeMo invocations |
|---|---:|---:|---:|
| Development preflights | p01 and p02 | At most 8 | At most 2 |
| Held-out qualification, only if both preflights pass | 20 in frozen order | At most 80 | At most 20 |
| Combined ceiling | 22 | **88** | **22** |

Every case has an overall **180-second deadline including preparation**. Source assessment and orchestration time are additional; the sum of 22 case deadlines is at most 66 minutes, not a promised completion time. No retries, warmup, extra diagnostics, Ragas, hosted inference or automatic tuning. NeMo internal requests/tokens and monetary/hardware/energy costs remain incompletely measured.

The controller admits one case at a time. A prior actual result must have valid pinned identity, process/attempt/checkpoint hashes, call/time accounting and an explicitly authored source assessment with reasons and locators. Used assessments are sealed by hash. Missing or unresolved assessment does not allow the next generation. This checks traceability and admission, not semantic truth or human acceptance.

## Existing gates and explicit proposed stop rules

The [unchanged gates](quality-gate-accounting-2026-11-02.md) remain 9/10 complete supported answerable cases, 2/2 partial, 4/4 proper missing-evidence abstentions, 2/2 explicit conflicts, 2/2 safe adversarial outcomes and zero critical unsupported/wrong-scope/date/unit/scenario claims.

- Preflights must both pass technical, source/completeness and safety checks; p01 must answer and p02 must genuinely abstain. Any failure closes the unused allowance before held-out generation.
- Stop held-out generation on a technical, identity, call or deadline violation, a critical claim, or a failure in any category requiring a full pass.
- Retain one noncritical answerable miss under the agreed 9/10 threshold. A second closes the allowance because the gate can no longer pass. No silent conversion to 10/10, relaxed safety threshold or regrading to continue.
- Preserve all attempted and unattempted case identities and unknown in-flight usage. Do not repair, retry, replace or tune cases within this batch. Editorial corrections stay separate from raw-output scoring.
- Check five-hour usage before each case. At 90% used, start no further case, retain the bounded active attempt and save/pause under the standing instruction. User-directed resumption must revalidate frozen identities; a pause never authorizes retrying a started/completed case.

These stop rules are proposed for this new grant, not retroactive changes to closed diagnostic contracts. Actual source findings are assistant-authored until human adjudication. Technical/citation checks cannot replace factual review.

## Offline preparation evidence

The private controller passes **23 synthetic admission checks**, including denied/closed grants, missing/failed preflights, changed evidence, sealed assessment changes, fake processes, forged call counts, critical errors, full-pass category failures and one-versus-two answerable misses. Actual missing-grant invocations fail before any phase/model metadata request in normal and optimized Python; verification-only mode starts no generation. These are controls tests, not model-quality evidence.

All frozen v4 package/source hashes were verified. A metadata-only audit inspected **53 saved local attempt records**, with no reserved case-ID match or unidentified attempt. This is limited to the inspected directory, not a guarantee about external runs, pretraining or statistical independence. Questions/references were not used to tune the generator. References never enter model prompts; each worker receives only its question and explicitly selected corpus.

The application and dependency versions are unchanged from the owner-reviewed v1.66 run. Retained full-suite evidence remains 1,253 Windows / 1,252 Linux tests plus one skip; these private controller checks do not constitute another full application run or remote CI result.

## Pinned identities and human checkpoints

- Package manifest: `36ab8c6f99cbd88385914a12f62139b16c99d76702db337dfe1bb7e0dcad5ce1`.
- Generator: `4009db6a3c416f5751c34266437bd67f16e4c23cd2647f2ca9e16f3bc203534c`.
- Model digest: `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`.
- Protocol: `eecd377a4e220ef730b6f884e89664f0639d1470d6987ffffb623b05984fc5ac`.

The local `resume-v104/review-packet.md` retains the complete frozen contract, roster metadata, acceptance criteria, expected identity and execution controller. No authorization or started-case file exists at preparation. Exact grant: **Authorize v1.66 preflights and conditional twenty-case qualification**.

Human source judgments remain necessary before claiming owner-accepted quality. Do not ask for numerical rescoring of technical failures or repeat the resolved r05/r06 decisions. Exact stored-revision approval/export, independent reviewer tasks, current-release publication and actual Databricks production/operations acceptance remain separate. This proposal authorizes none of those actions and establishes neither portfolio completion nor production readiness.
