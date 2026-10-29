# Proposed gated v1.49 development diagnostic

**Execution update: authorized, executed, then stopped at r05; budget closed.** Both mapper checks and r03/r04 passed. r05 exposed a currency-adjacent numeric-parser false rejection plus an independent selection/completeness failure; r06 was not attempted. See the [actual findings](diagnostic-v149-findings.md). The protocol below is the proposal frozen before execution. The [offline repair](mapped-answer-alignment-2026-10-28.md) removes compulsory bare-topic roots and checks mapped numeric answers against selected evidence; its replays/fixed responses alone did not establish actual model quality.

This is one new, explicitly gated budget:

| Stage | Cases and deadline | Ceiling and transition |
|---|---|---|
| Mapper checks | Synthetic m01/m02 once each; 60 seconds per case | At most two local mapper calls, no tools/composition/NeMo. Stop at the first technical or assistant source-quality failure. |
| Conditional workflow | Consumed r03/r04/r05/r06 once each; 180 seconds per case | Only after both mapper checks pass. At most 16 workflow calls and four NeMo invocations; inspect each output before the next and stop at first failure. |

Combined maximum: **18 mapper/workflow model calls plus four NeMo invocations**, with internal NeMo usage separately incomplete. No retries, automatic tuning, Ragas, hosted inference, twenty-case evaluation, approval/export, external deployment or reviewer contact. A stopped batch's unused ceiling cannot fund changed-code retries.

m01 asks for total application value/project count and their changes from 2018 to 2019. Sources contain 2.5 billion credits, 220 projects and 15%/10% growth, alongside a contact header and different FDI-subgroup facts. Require correct, complete short answers and quotations that support them, without unrequested header/FDI substitutions. m02 asks for actual completed cash investment in 2020; supplied sources contain 2019 applications rather than that observation. Require explicit missing status, empty answer/evidence and a requested-information gap.

The fixtures are development diagnostics, frozen before generation, with different facts/wording from instruction examples. The initial unexecuted protocol draft used descriptive fixture identifiers; version 2 retains the facts but uses neutral source IDs/URLs. Expected actions/checks stay outside model messages. These checks are not unseen benchmark results or release preflights.

The workflow source checks remain: inflation causes/period; monthly/quarterly investment directions and categories; total application value/count/growth; FDI denominator, leading value source and project-count comparison. Source-provided currency equivalents are acceptable. Verify model/settings, content digest, generator and source identities before/after execution. Retain raw/parsed responses, schemas/catalogs, tool traces, selected sources, timings, available tokens, finish reasons and failures.

Frozen contract: `reports/workflow_pilot/production-readiness-2026-10-27/resume-v8/gated-diagnostics-proposal-v149-v2/contract.json`, SHA-256 `0a4ec717ed454548808ec11f928d5479a9c90cce48bb14dc77a1dcc81d6e6ccb`. Expected generator identity: `1a5313ea106dc908ecaf30ed1a8e2c5d58dc1badd900d38da620051906f5ae68`. Expected model digest: `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`. These are expected pins, not a new model-availability check. Prerequisites are the final 745-test Windows and 744-test Linux logs, no-inference recovery, fixed-response harness checks and protected-evidence integrity.

Owner adjudication of unchanged v1.47 r03/r04 remains source-confirmed with minor country edits requested. Their separate editorial candidates are not fresh generation. Do not infer acceptance of new outputs; exact-content/source identity may reference existing review without duplicate scoring. Human approval of exact saved revisions remains necessary for export, and independent reviewer usage remains separate. The full portfolio/production Goal remains incomplete even if this consumed diagnostic passes.
