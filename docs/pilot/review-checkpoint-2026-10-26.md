# Analyst workflow review checkpoint — 2026-10-26

**Engineering validation complete; exact-revision owner decisions and export pending.**

This record continues the [owner follow-up](owner-followup-2026-10-25.md). The owner's rejection of the earlier d04 revision remains recorded. Retaining d06's wording did not authorize approval or export of an empty draft, or approval of a later nonempty revision. The completed historical human-review CSV and earlier assessments remain unchanged.

## Observed failures and changes

The retained local attempts exposed implementation and interpretation failures: country context on another page was rejected even within a pinned document; valid causal information could disappear during composition; electricity-demand answers could omit the requested rate or scenario; and a historical price passage could be substituted for a requested dated observation. These findings do not establish an inherent open-source-model or GPU-capacity limitation.

The opt-in pilot now:

- Allows geographic context across pages only when document identity, URL, publication metadata and the pinned corpus hash agree. The context binding and unresolved-scope warnings remain inspectable. Shared document identity does **not** prove that a claim applies to its country.
- Retains omitted evidence units and lexical causal clauses through explicit source-excerpt fallbacks. The diagnostic records the fallback. This conservative word-based safeguard can overuse quotations and cannot prove causal entailment or completeness.
- Builds separate rate and level evidence views for applicable electricity-demand projection requests, using facts from one source record. Scenario context is retained only when selected evidence unambiguously establishes the requested scenario. Source-relative “today” is labelled as the report's baseline without inventing an observation year.
- Rejects substituted historical/forecast material for relative-date price observations when the retrieved text lacks the necessary dated price evidence. This check recognizes explicit ISO/English dates and selected measure terms; it is not a general temporal reasoning system. Publication dates alone do not qualify as observation dates.

Prompt identity is `analyst-pilot-v1.26`; mapping identity is `requested-evidence-v23`. Dependencies, model/context settings, public draft/API shapes, SQLite schema, the legacy agent, the four-main-call ceiling, final nonempty NeMo check, and approval-gated export are retained. Earlier source-context recovery/search-policy work is also present in the uncommitted diff and should be reviewed with these changes. The current local model remains a development dependency, not a qualified production judge.

## Current review candidates

The local [review packet](../../reports/workflow_pilot/owner-review-2026-10-26/review-packet.md) contains the full drafts, source excerpts, page renders, warnings, immutable candidate hashes and revision digests. It deliberately separates candidate origin from source assessment and human acceptance. All current candidates are revision **2** in a separate review database.

| Case | Candidate origin | Assistant source assessment and remaining review |
|---|---|---|
| d01 | Unchanged completed v1.24 workflow | August 2026 export/technology explanation retained, including explicit source fallback. BOT PDF page 1 supports the selected facts. Geographic context warning remains; owner must inspect the Thai report scope. |
| d02 | Frozen model response reprojected through the current renderer; no new workflow generation | Food/weather/production costs, energy/global oil and core cost pass-through retained. BOT PDF pages 1 and 6 support the passages. Cross-page country context still requires review. Two headline claims overlap; source bullet formatting remains. |
| d03 | Assistant-prepared editorial proposal; original generated revision preserved | Investment machinery/equipment and technology/data-centre explanation, consumption services/tourism context and goods movements checked against BOT PDF pages 1–2. Month-to-month indicators are identified as seasonally adjusted. This is not proof of improved generation and is not owner-approved. |
| d04 | Frozen v1.25 model response reprojected through the current renderer | IEA PDF page 7 supports regional electricity demand growing 4% annually to 2035 in STEPS, and demand above 2,000 TWh from a report baseline above 1,300 TWh. No baseline measurement year is invented. This is a different revision from the rejected earlier draft. |
| d06 | Completed v1.25 workflow; empty abstention | No claim or export. Captured date 2026-10-26 makes “yesterday” 2026-10-25; retrieved historical material did not establish that Thai retail-price observation. Owner-retained wording is preserved. |

Reader-facing PDF pages are one-based; stored corpus indexes remain zero-based. Supporting passages and scope context were checked against pinned local sources, with page renders used for source interpretation. Exact excerpts stay in the ignored local review directory. All findings here are **assistant-authored; exact-revision human adjudication pending**. A configured NeMo pass is a separate control result, not a correctness certificate.

## Validation and accounting

- Final offline suite: **329 passed, 3 existing warnings**, 65.48 seconds in `.venv-pilot-clean`. The warnings concern Unity Catalog/Pydantic, Starlette/httpx and an MLflow prediction type hint. Fixed-response tests establish contracts and regressions, not actual model quality.
- Six fresh workflow attempts in the October 26 continuation used **22 recorded main calls**: four attempts under v1.24 and two under v1.25. Unsuccessful quality outcomes were retained. Later rendering/editorial work used **zero new main calls** and three configured guardrail invocations; NeMo internal model calls/tokens are unmeasured.
- The consolidated ledger covers the earlier ledger and explicitly enumerated continuations: **139 recorded main calls**, **33 workflow attempts**, **201,013 known input tokens** and **16,074 known output tokens**. This is a cumulative development cost record, not the cost of one five-case run or all project history. An interrupted earlier attempt may have incurred an additional unlogged call. Totals exclude Codex usage, fixed-response tests and unmeasured NeMo usage; monetary cost is unavailable.
- Baseline integrity: 610 captured files, 601 unchanged and 9 expected implementation/test modifications. No missing baseline files or unexpected historical/data/configuration modifications were found. All five review candidate files match their manifest hashes. New source/tests and evidence are additional files rather than changes to protected historical evidence.
- Both requirements files, pilot constraints, completed human-review CSV, BOT/IEA PDFs and corpus retain their recorded hashes. No installation, fresh dependency-resolution claim, Ragas scoring, hosted inference, Databricks test, commit, push, deployment or reviewer contact was performed in this continuation.
- Read-only API checks against the exact review database succeeded for all five revision-2 records. Export returned the expected conflict response for every unapproved candidate; the database hash stayed unchanged. No model generation, review decision or export was created by this check. Documentation/packet links resolve, structured accounting agrees and `git diff --check` passes (Git also reports its existing line-ending conversion notices).

The machine-readable [checkpoint record](evidence/review-checkpoint-2026-10-26.json) and ignored local integrity/usage records retain the supporting provenance. The final suite log is `reports/workflow_pilot/resume-scope-2026-10-26/final-offline-suite.txt`.

## Manual review and exact next step

1. Read **d01–d04 revision 2** in the new packet. Check every claim, scope warning, period, measure, scenario and causal explanation against its cited source. d03 is an editorial proposal requiring particular attention, not a request to rescore a technical failure.
2. Give an explicit decision for each revision you choose to review, including whether source support is confirmed. Earlier approvals/rejections never transfer to a changed revision. No further approval is requested for empty d06.
3. Only after an actual owner approval, verify the unchanged revision digest, persist that decision through the existing lifecycle, export that exact revision and verify exported bytes, page labels and idempotence. No approved export has yet been created from this packet.
4. Record any required edits as a new revision requiring its own approval. External reviewer sessions, usefulness/task-time evidence, fresh held-out evaluation, broader temporal handling and general semantic quality remain later work.

The manual-review checkpoint has been reached. The Goal remains active while owner decisions are pending; export and overall completion must not be claimed before approval. No more model generation is needed to make this review decision.
