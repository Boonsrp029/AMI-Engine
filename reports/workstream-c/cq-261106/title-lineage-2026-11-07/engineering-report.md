# Concurrent title scope and development-lineage integration — 7 November 2026

This is an offline engineering pass after the one-request composer grant closed. No additional model, NeMo, Ragas, hosted-inference or Databricks calls occur. The actual composer result and its assistant/owner statuses remain unchanged in the prior package.

## Pass 1: constrain application title scope

Current evidence: the actual composer produced the correct two claims and a neutral title, while application projection appended Canada alone to the Canada/Japan brief. The new private `_title_scope.py` checks whether the candidate geography covers every selected quotation before retaining a global title label. Different explicit locatives or unsupported quotations suppress only that label; the existing period suffix remains. Claims, citations, source selection and original mapper resolution are unchanged.

Common literal geography is retained. Exact geographic-context spans and pinned-document identity may support contextual title qualification with an explicit applicability-review warning; document identity is not treated as semantic proof. An explicit other-country locative overrides shared-document context. Invalid geographic span hashes, offsets, quotations or value mismatches fail rather than being repaired. The helper runs before final safety and is included in sealed diagnostics. Lexical coverage is a necessary condition, not a general geographic classifier or entailment guarantee.

`project_report` gains only an optional internal resolution argument; existing calls remain valid. The default sequential engine and its shared projection/prompt remain unchanged. The title helper changes the opt-in concurrent result before safety; it does not modify stored drafts, approved exports or owner edits after the fact.

The exact retained actual response was replayed with zero inference. Its title changes from `Analyst research brief (Canada)` to `Analyst research brief`, with byte-equivalent claim texts, unchanged warnings, raw mapper resolution, composer request/schema and no fallback. This is saved in `offline-retained-response-replay.json`. It is a corrected offline projection, not a fresh generated success or owner acceptance. The original actual title-scope failure is not regraded.

## Pass 2: integrate retained development lineage

The previously isolated patch is now applied within its declared D scope. The actual composer attempt was closed and its 119 project inputs, six request artifacts and outputs were already archived before integration. No pending execution grant is reused after code changes.

The gate requires retained development contract/start file hashes in addition to existing result/assessment hashes. It checks the canonical contract reference, case order, current model/settings, bounded execution, stored plan/query/corpus, unique run/attempt IDs and explicit source findings. A reserved lower runtime deadline is accepted; extended or invalid deadlines are not.

Integration additionally pins the **actual current source, active/reference configuration and dependency-constraint bytes** in both development and qualification contracts. Equal outer labels cannot conceal an older code/configuration set. Existing `input_sha256` records carry these pins; no secrets/env credential files are included. This is an explicit private admission-artifact contract hardening, not a public API or library migration. Old minimal gate records fail closed; historical actual artifacts are not rewritten to add fields. New passing records are still absent.

Maintained synthetic fixtures/checks replace the old minimal development fixture. The first promotion missed a test-helper import, producing 15 test NameErrors; the import was corrected, with logs retained. Application validators were not loosened. Corrected targeted runs passed 92, then 95, then **98 checks** as runtime-pin and contextual-title edge cases were added. The final targeted log is `../title-lineage-targeted-v4.txt`.

## Integration validation and boundaries

`../title-lineage-full.txt` records **1,630 passes, 14 warnings, 453.07 seconds**, terminal exit zero, for this integrated Windows source revision. The final targeted run passed **98 checks in 6.05 seconds**. Older 1,583 and isolated 27-check results do not substitute for these results. Test coverage includes source identity, category stopping, partial/abstention behavior, strict unit-local validation, final safety and exact-revision approval/export controls. This pass does not claim a new Linux/container or live deployment result.

Dependencies/model/settings/public Draft/SQLite/API/sequential entry points remain unchanged. New helper code, maintained fixtures, diagnostics and opt-in title behavior are deliberate differences. Integration invalidates the old executed protocol against the current tree by design; verify the preserved snapshot for that historical attempt and freeze a new contract before future inference.

## Remaining actual gates and human work

Owner source/wording review of the prior two raw claims remains pending and is separate from this engineering correction. No repeated rating of the title bug or rejected technical outputs is required. New actual full workflows must demonstrate final title scope, local NeMo and persisted draft behavior; offline replay cannot establish these. The two-case development gate and all twenty CQ1 cases remain unpassed/unattempted respectively. CQ1 requires current passing linked records, its own explicit grant, source/category review and required owner adjudication.

Any next package must record the same local model/settings, new source identity, captured as-of date, two fixed development questions/corpora, stop-on-first-failure/no-retry policy and separate new output directory. Do not issue or infer an execution grant from these files. Independent reviewer usefulness and target-environment production qualification remain outside this offline result.
