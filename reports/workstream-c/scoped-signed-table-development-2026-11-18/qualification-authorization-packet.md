# Signed-table CQ1 qualification request — 18 November 2026

Contract SHA-256 **6a134feb5c41785680b95b937255338cd1ab7f248b16980353e1aa935b88b89b** binds 201 inputs, twenty ordered cases, exact corpus/plan/scope identities, model/settings, current development lineage, owner editorial acceptance, source-review protocol and a new actual-cq1 output directory. [Frozen contract](qualification-contract.json)

Both current consumed development cases passed actual technical, assistant source, completeness, safety and storage checks. The owner confirmed source support and accepted both U.S.-explicit editorial copies. Those editorial copies remain distinct from generated/stored drafts. [Development results](development-findings.md) · [Owner acceptance](owner-acceptance-development.json)

The pool preserves eighteen exact unattempted cases and replaces consumed cq1-a37/cq1-a38 with two unused questions. cq1-a39 asks for solar thermal generation/share in 2023. cq1-a40 asks for the minimum utility-scale capacity in megawatts and kilowatts. The source documents are familiar. This is question holdout, with references reserved for source adjudication. [Pool and evidence limits](../cq1-signed-table-pool-2026-11-18/README.md)

Run each ordered case once, at most four local main-model calls and one NeMo wrapper invocation per case, 180 seconds per case including preparation. Total ceilings are eighty main calls and twenty NeMo invocations, zero retries and zero warmups. Inspect exact source support and completeness before advancing. Stop on a technical or critical failure, any failed full-pass category, the second noncritical answerable miss, or 90% five-hour usage.

Gates remain 9/10 complete supported answerable cases, 2/2 partial, 4/4 missing, 2/2 conflict, 2/2 injection and zero critical unsupported or wrong-scope/date/unit claims. Record raw output, application rendering/fallback and editorial proposals independently. An editorial correction cannot pass a case. Final completion requires owner adjudication of the exact result bundle. [Pinned source-review protocol](../cq1-fact-span-pool-2026-11-15/source-review-protocol.md)

Model/settings remain local ami-llama3.1:8b-4k, digest 6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23, context 4096, completion 900 and temperature zero. Internal NeMo usage and monetary cost remain incompletely measured.

All twenty mapper requests passed socket-blocked admission, largest reservation 3,544/4,096 tokens. Compilation verified current runtime hashes and both actual development starts, results and assessments. The owned wrapper passed inspect-only admission for all 201 inputs. The matching runtime has 1,881 passing Windows offline tests. No new qualification inference has started.

The development allowance is exhausted. AGENTS.md and the active Goal require this separate generation grant. Reply **Authorize CQ1 scoped twenty-case qualification** for this contract. Stored approval/export, publication and target-environment deployment retain their separate authorization boundaries.
