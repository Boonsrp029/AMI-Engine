# v1.68 qualification results — 3 November 2026

**Both development preflights passed; qualification stopped at the first held-out case.** The owner explicitly granted the [prepared v1.68 scope](fresh-qualification-v168-proposal-2026-11-03.md). Code/policy/controller, source manifest, protected history, package and model identity were revalidated before execution. This is a new actual batch; the earlier v1.67 failure remains unchanged.

| Case/phase | Actual result | Main calls | NeMo | Time including preparation |
|---|---|---:|---:|---:|
| p01 supported multipart fixture | Answered; assistant source/completeness and real NeMo passed | 4 | 1 | 75.78 s |
| p02 missing audited-profit fixture | Genuine empty-claims abstention; full question retained in gap | 3 | 0 | 50.41 s |
| r07 first held-out answerable case | Technical failure: raw composed claim mismatched its evidence unit | 4 | 0 | 37.59 s |
| Remaining nineteen held-out cases | **Unattempted** | 0 | 0 | Not applicable |

Totals: **eleven main-model calls, one NeMo invocation**, **9,739 known input tokens and 728 output tokens**, **10,467 known main tokens**. All attempts stayed within 180 seconds. NeMo internal use and hardware/energy/monetary costs remain incompletely measured. No retry, replacement, Ragas or hosted inference occurred.

## What the preflights establish

p01 directly retained the synthetic Thailand/May 2023 shipment increase, storage-cost decrease, April comparison and warehouse-capacity cause. The raw composer was complete without application fallback. Generic geographic/period warnings were retained as nonblocking diagnostic issues; no historical owner waiver or acceptance was silently transferred.

p02 selected missing evidence with the literal question anchor, then returned the existing evidence-limited no-information message and full-question gap. It did not substitute a 2023 volume forecast for audited 2025 profit. Composition and NeMo correctly did not run for empty claims. This is one real repaired missing-evidence success, not a general guarantee or a twenty-case score. The preflights did not exercise the conditional financial-composition checklist.

## Confirmed r07 failure

The question asks for China's historical electricity-demand growth in 2024 versus its annual forecast through 2027. The pinned IEA Electricity 2025 executive-summary paragraph supports **7% in 2024** and **an average 6% annually through 2027**. Both source sentences were retrieved and correctly retained by the mapper.

The composer produced two copies of “China's electricity-demand growth in 2024 was 7%.” It assigned the second copy to `u2`, whose evidence was the **6% annual forecast through 2027**. Its JSON parsed, but per-unit factual validation raised **“Draft introduces a numeric value absent from its selected evidence.”** The error was at `validate_claim_measure_and_numbers()` before final NeMo. No final r07 Draft was returned, stored, approved or exported.

A socket-blocked replay of the unchanged saved responses reproduced the exact error with zero actual model/NeMo calls. There was no timeout or GPU-memory failure; the failure was a raw-composer evidence-binding error caught by an existing validator. This single response does not establish an inherent limitation of open-source models. No invalid response was silently repaired or credited as a pass.

Source locator: IEA Electricity 2025 executive summary, article paragraph 4 / extracted line 188 in the frozen snapshot; source ID `IEA_ELECTRICITY2025:unit:3:0`. This is HTML with no PDF page index. [IEA source](https://www.iea.org/reports/electricity-2025/executive-summary). Exact source content/hash and quotations remain in the local failure record.

## Gate accounting and preservation

The worker **and new controller** exited nonzero on r07. The allowance closed immediately. A technical failure stops the batch independently of the allowance for one noncritical answerable miss; that allowance cannot justify continuing after this error.

**Held-out coverage: 1/20 attempted, one technical failure, zero assessable final drafts, nineteen unattempted.** No accuracy percentage is calculated, and unattempted cases are neither passes nor observed failures. The agreed 9/10, 2/2, 4/4, 2/2 and 2/2 category thresholds remain unchanged and unqualified. Remaining calls in this closed grant cannot be reused.

r07 is consumed evidence from now on. If future tuning uses this failure, it must not be presented as an unseen success. Preserve the remaining reserved cases and predeclare the next evaluation pool before generation. Do not alter the old batch, references or judgments to manufacture completion.

Actual protocol `92bb0c4c504a35ec84154ca1cfb8dfe91a6aedf5d869a120be7cf465b87c4290`; generator `a15516b638f467c7c55ab3af7bc0663dcddc09d39b89180843583604217590c9`. Original inputs, approved exports, owner CSV/DB/history and earlier attempts remain protected. The code and model settings stayed unchanged during generation and diagnosis. Raw outputs, grant, source gates, process/call/deadline checkpoints, closed allowance, replay and hashes are retained in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v108/`.

## Next engineering work and manual review

Inspect the composer's unit-local coverage guidance using different synthetic facts, retaining strict evidence/numeric validation and the four-call ceiling. Do not retry r07 or another batch without a separate concrete repair/protocol and new grant. The raw financial-composer repair from the side conversation remains unqualified by these nonfinancial cases.

**No manual rescoring is needed for r07's technical failure.** The two new preflight outputs are assistant-assessed only; a short local packet preserves their exact wording if owner acceptance is later sought. No additional owner judgment is needed to reproduce the failure. New valid qualification outputs will require factual/wording adjudication; exact stored-revision approval/export and independent reviewer sessions remain separate human actions.

Portfolio completion, exact-release CI, independent usefulness and actual scoped production qualification remain incomplete. No commit, push, external deployment or reviewer contact occurred.
