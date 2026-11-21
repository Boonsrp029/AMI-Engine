# Revised CQ1 execution request — 18 November 2026

Contract SHA-256 **477a0214853fdf8fa2b819493c240e7dbba46d39ad6a669a868f8e32d99c1ddf** binds 187 inputs, the revised twenty-case roster, exact source corpora, sidecars, model/settings, current development results and assessments, source-review rules and a fresh actual-cq1 output directory. [Frozen qualification contract](qualification-contract.json)

Both consumed development cases passed actual technical, source, completeness, safety and storage checks. They used four main-model calls and two NeMo invocations under the separate exhausted development grant. Owner review of their exact generated and U.S.-explicit editorial wording remains pending. [Development evidence](development-findings.md) · [Human review packet](review-packet.md)

The revised qualification replaces consumed cq1-a27/cq1-a28 with cq1-a37/cq1-a38 and retains eighteen exact unattempted cases. The new questions test two unused generation-row relationships in familiar EIA documents. This is question holdout, with familiar source material. [Roster and limits of evidence](../cq1-table-boundary-pool-2026-11-18/README.md)

Run twenty ordered cases, once each. Each case has 180 seconds including preparation, at most four local main-model calls and one NeMo wrapper invocation. Total ceilings are eighty main calls and twenty NeMo invocations, with zero retries or warmups. Source support/completeness assessment must finish before advancing. Stop at the first technical or critical failure, any failed full-pass category, the second noncritical answerable miss, or the standing five-hour usage threshold.

Category gates remain 9/10 complete supported answerable cases, 2/2 partial, 4/4 missing, 2/2 conflict, 2/2 injection and zero critical unsupported or wrong-scope/date/unit claims. Preserve raw composer output, application rendering/fallback and any proposed editorial changes independently. An editorial correction cannot pass a case. Final completion requires exact-bundle owner adjudication. [Pinned source-review protocol](../cq1-fact-span-pool-2026-11-15/source-review-protocol.md)

Model and settings remain local ami-llama3.1:8b-4k, digest 6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23, context 4096, completion 900, temperature zero. Internal NeMo usage and monetary cost remain incompletely measured.

Socket-blocked mapper admission passed all twenty requests, with largest reservation 3,544/4,096 tokens. Compilation verified exact development lineage and every runtime input. The owned wrapper's inspect-only admission passed all 187 frozen inputs. Preparation started no qualification inference.

This is a separate generation request under AGENTS.md and the active Goal because the two-case development allowance is exhausted. Reply **Authorize CQ1 scoped twenty-case qualification** for this contract. Approval/export, publication and target-environment deployment remain separately controlled actions.
