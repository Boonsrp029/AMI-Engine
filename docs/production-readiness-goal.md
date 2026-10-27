# Proposed AMI completion and production-qualification goal

Prepared 2026-10-26. This is a proposed next goal, not evidence of deployment or an instruction to start execution merely because this file exists.

## Verified baseline and claim boundaries

The project is an owner-reviewed local analyst pilot. Four exact drafts are owner-approved and exported: d01 revision 2, d02 revision 3, d03 revision 2 and d04 revision 2. Empty d06 remains unapproved/unexported. See `docs/pilot/d02-approval-2026-10-26.md` and its structured evidence. Some accepted candidates are frozen-response reprojections or editorial corrections; they are not four fresh successes by the latest unmodified model workflow.

The latest retained offline suite is 341 passed with three existing warnings. This planning audit inspected that log; it did not rerun the suite, install dependencies or verify remote CI. Much of the latest implementation remains modified/untracked in the local checkout. Four approvals and a green offline suite do not prove independent usefulness, general answer quality, fresh-clone reproducibility or production operation.

The legacy query graph, local analyst workflow, Databricks ETL/index adapters and model deployment utilities exist. `src/models/register_model.py` wraps `src.agents.graph.app`, not the reviewed `src.pilot` lifecycle. Docker/Compose currently package evaluation and MLflow, not a demonstrated deployment of the analyst browser application. The ETL requires an existing Bronze table; a functioning upstream live-news ingestion service must not be inferred from the Silver/Gold job. Existing historical Ragas results remain bounded diagnostics.

## Objective

Complete a reproducible analyst-workflow portfolio release, then qualify one explicitly defined production deployment for human-reviewed research using public data. Preserve the core architecture and distinguish the local pilot, legacy runtime, Databricks data/serving path and planned components. Do not claim enterprise readiness, sensitive-financial-workflow suitability, external usage or model-quality improvements without the corresponding evidence.

The two milestones are separate statuses. Reaching the portfolio milestone does not complete the full production goal. Missing permissions, budget or human judgments are real gates, not permission to redefine completion.

## Pass 1 — baseline, release contract and unresolved defects

Snapshot the current diff, untracked implementation, dependencies, corpus, source PDFs, approved revisions, exports and evaluation artifacts. Reconcile current documentation without rewriting historical reports or ratings. Establish one implementation inventory and readiness matrix with evidence links, owners and statuses: implemented, tested offline, tested live, or pending.

Define the production scope: intended users, data classification, hosting target, expected load, supported question types, source freshness, service hours, latency/error limits, budget, retention, recovery objectives and incident owner. Prepare a decision record resolving which application is deployed and how it relates to the existing Unity Catalog model. Do not silently expose the legacy graph as the reviewed analyst workflow or perform a framework/API migration.

Investigate the local guardrail diagnostic's nonzero process exit after a passed result and saved artifacts. Capture stdout/stderr and the actual process lifecycle in a narrowly bounded diagnostic; distinguish validation outcome from process health. Fix a demonstrated defect with a regression check, or document a supported diagnosis and operational mitigation. Do not blindly rerun complete workflow batches.

## Pass 2 — clean reproduction and deployable artifact

Prove fresh application installation, `pip check`, public entry points and the full offline suite using existing pinned requirements and constraints. Include the serving environment and separated Spark/ETL boundary. Revalidate against the current checkout rather than repeating older resolver success as current proof.

Add a reproducible analyst-application container/launch path with persistent review storage, explicit corpus/model prerequisites and meaningful health/readiness checks. Inspect `.dockerignore`: it currently excludes `.venv` but does not cover all the workspace's alternative virtual environments. Ensure build contexts/images exclude secrets, virtual environments, local databases and unrelated artifacts. Test non-root execution, model connectivity, restart and byte-stable approved exports.

Prepare CI changes for installation, dependency checks, offline integration tests and build/smoke verification. Remote success must come from the exact reviewed Git revision on Linux; local success does not substitute. Commit/push is a separate owner action unless explicitly authorized.

## Pass 3 — fresh end-to-end quality and reviewer evidence

Freeze fresh source-backed facts and acceptance checks before tuning. Create at least 20 new held-out cases spanning multipart questions, causal explanations, geography/period/measure/scenario distinctions, incomplete/stale evidence, conflicts, definitions versus causes and malicious source instructions. Do not reuse d01–d06 as unseen evaluation. Keep development and final test facts separate and preserve all failures.

Predeclare sample counts and numerical quality thresholds with the owner before qualification. Proposed small-pilot gates: no critical unsupported or wrong-scope/date/unit/scenario claims, at least 90% complete supported answers on answerable cases, and correct fail-closed outcomes on all designated missing/conflict/injection safety cases. These are proposed release gates, not achieved scores or statistical assurance. Review raw cases and denominators, not only averages.

Test actual unchanged generation-to-review output before manual correction; separately label edited drafts. Use a small development diagnostic before the final held-out run, one attempt per case and explicit model-call/time budgets. Stop on technical-gate failure, preserve raw/parsed results and diagnose rather than retry automatically. Freeze answers before any selected local Ragas repeats; count actual judge requests and report unavailable internal usage. Ragas supplements source-grounded human judgments and cannot establish correctness by itself.

Owner arranges at least one independent reviewer session using public/synthetic data. Record actual task completion, checking/correction time, edits and usefulness; implement one justified improvement and repeat its affected checks. No external-usage claim until a real session occurs. These external findings require humans; do not fabricate or infer them.

**Portfolio-complete gate:** clean reproducibility, current CI/build evidence, a usable documented workflow, fresh quality findings, an actual independent reviewer session and its feedback-driven improvement, a concise walkthrough/case study, and accurate architecture/limitations. Report failed quality thresholds openly; a failed gate cannot be described as reliable completion.

## Pass 4 — production runtime and security

For the chosen deployment, implement or verify user identity, role-based access and review/export audit attribution. A shared per-launch localhost token is not multi-user authorization. Verify source trust boundaries, prompt injection, PII/log redaction, secrets access, retention and least-privilege workspace grants. Existing credential files are currently untracked; historical exposure and rotation still require evidence. Do not print credentials or rewrite Git history automatically.

Bound admission/queue size, total execution time including NeMo, cancellation, concurrency and retries. Exercise duplicate submissions, model/guardrail outages, saturation, application termination, changed corpora and partial failures. Preserve exact-revision review/export guarantees. Prove backup restoration, persistent history and restart behavior against declared recovery objectives. Introduce a queue/database change only when the scoped workload and tests justify it, with a separate migration record if required.

Add actionable operational measurements and alerts: request/stage latency, errors, retrieval misses, abstentions, model calls, available tokens, resource/cost budgets and source/index freshness. Report unknown costs honestly. Exercise an alert, identify incident ownership and document rollback/recovery actions.

## Pass 5 — target-environment qualification

In an authorized nonproduction target, verify actual table/index names, embedding source column, primary key, identity/grants, source freshness and the complete Bronze prerequisite → Silver/Gold → index → chosen application path. Test repeated ETL/index operations, partial failure, lag, backfill and recovery. Verify model registration/version/signature and that the serving endpoint runs the intended runtime with reachable model dependencies. Preserve the distinction between serving inference and the analyst application's durable human-review lifecycle.

Demonstrate reproducible deployment, endpoint authorization, smoke/integration behavior, rollback, backup/restore, alert delivery and an agreed sustained workload/soak test. Record environment, immutable build/revision, dataset/model/prompt versions, load, durations, p50/p95 latency, errors, resource use and budget compliance. A five-case run is not a sustained benchmark. Only the explicitly qualified workload/environment can receive a production-readiness claim; an untested architecture diagram cannot.

**Production-qualified gate:** the agreed scope/SLOs, security controls, quality gates, end-to-end deployment, operational tests and sustained-load criteria all pass with current evidence, and the owner accepts the residual risks and rollout. Otherwise retain the pilot/staging label and report the precise missing gate.

## Human checkpoints and execution boundaries

Human actions: confirm target/SLOs/quality thresholds and budget; provide permissions and evidence of credential rotation; adjudicate fresh factual outputs; arrange independent sessions; approve exact edited revisions before export; authorize any paid infrastructure, external deployment, destructive operation/history rewrite, migration, commit/push or public release. Prepare concrete reviewable work before requesting these decisions. Continue independent engineering while awaiting input.

Keep current library versions unchanged. Preserve public APIs, approved exports, historical inputs/scores/notes, and the local RTX 4060 path. Treat dependency repair, framework migration, public API change and architecture replacement as separate proposed tasks requiring explicit authorization. Do not add MCP, GraphRAG, additional agents or enterprise infrastructure just to expand the technology list.

Check five-hour usage before major passes and long validation. At 90% used / 10% remaining, save files, commands/results, exact next step and a handoff, then pause under the standing user instruction. Never consume budget just to reach the threshold. Do not mark this full goal complete merely because a milestone, test suite or manual-review packet is complete. Use repeated-blocker rules when essential human/external prerequisites remain unavailable.

Final deliverable: a requirement-by-requirement evidence matrix, runnable release/deployment instructions, fresh quality/reviewer findings, security/operations/rollback runbooks, and an honest verdict identifying exactly whether the portfolio and production milestones passed. Do not create or start this goal until the user activates it.
