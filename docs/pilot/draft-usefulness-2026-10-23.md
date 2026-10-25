# Draft usefulness pass - 2026-10-23

**Implementation and offline checks complete; local answer-quality gate failed.** These findings are assistant-authored and await owner adjudication. No new human scores were assigned.

## Change and preservation boundary

The only application edits are `DRAFT_INSTRUCTION` and `PROMPT_VERSION` in the opt-in pilot engine, now `analyst-pilot-v1.3`. The instructions emphasize requested facts, supported partial answers, specific gaps, geographic/time scope, measure/scenario distinctions, and abstention without unrelated filler. They add no repair call or model-based judging loop.

The completed owner CSV, original source audit, frozen outputs, PDFs/corpus, dependency files, public schemas, APIs, retrieval, two-tool-round limit, local model settings, NeMo guardrails, approval/export behavior and legacy agent remain unchanged. The [owner-review summary](owner-review-2026-10-23.md) records seven unresolved clarification items without rewriting owner judgments.

The [structured findings](evidence/draft-usefulness-2026-10-23.json) retain configuration identity, artifact hashes, all 12 claim assessments and all 11 warning assessments with source locators. These are coverage counts, not quality scores.

## Five preselected development attempts

One workflow attempt each used local `ami-llama3.1:8b-4k`, temperature 0, context 4096 and completion limit 900, with real unchanged local NeMo. No Ragas, cloud inference, retries or new legacy generation occurred. The model digest, tool traces, source text, drafts, usage, timings and failures are retained in the ignored [experiment directory](../../reports/workflow_pilot/draft-usefulness-2026-10-23/identity.json).

| Case | Runtime result | Assistant source assessment |
|---|---|---|
| d01 - exports | Nonempty draft | Core driver/moderation answered with supported citations; explicit Thailand/August wording is still missing from the generic title and claims. |
| d02 - inflation | Nonempty draft | Supported food and core-inflation causes, but omitted energy/global-oil cause despite retrieval; irrelevant overall-economy warnings. |
| d03 - investment/consumption | Abstained | Specific consumption facts and partial investment support were retrieved; generic gap labels discarded available evidence. |
| d04 - electricity outlook | Nonempty draft | Retrieval missed requested regional growth/levels; all-energy and Indonesian peak-demand evidence was substituted for regional annual electricity demand. |
| d06 - yesterday's Thai prices | Nonempty draft | Required abstention failed; unrelated historical regional/Lao PDR facts and unsupported Thailand-specific access wording were returned. |

Four nonempty drafts and one abstention describe runtime coverage only. Four NeMo invocations accepted the nonempty drafts; acceptance did not establish task relevance, completeness or all claim scopes. d01's core answer is useful, but this run does not establish a general improvement.

These are development cases and there is no matched before/after generation. Do not compare their nonempty rate directly with the old h01-h05 coverage or claim a benchmark uplift. All five new outputs remain pending owner review.

## Validation and measured limits

- Full offline suite: **100 passed, 3 warnings, 26.23 seconds**; previous baseline 88 tests, plus 12 new instruction/plumbing checks.
- Integrity: 117 of 118 snapshotted existing files are byte-for-byte unchanged. The remaining file is the intended engine edit; its AST is identical after excluding the two prompt assignments. All ten completed owner rows and the original audit are preserved. All 25 retrieved contexts match pinned corpus records; all 12 claims and 11 warnings have retained findings.
- The new tests use fixed synthetic model responses. They verify prompt delivery, partial/empty draft plumbing, citation identity, model-call bounds and scope instructions; they do not prove an 8B model follows those instructions. Existing lifecycle/approval/export checks also passed.
- The first sandboxed runs were interrupted after asyncio blocked constructing its internal Windows loopback socket pair. A diagnostic traceback located `socket._fallback_socketpair`/`ProactorEventLoop`; the full suite passed outside the sandbox. No networking workaround was added to application code.
- The initial synthetic fixture incorrectly omitted the retriever's source-title prefix. Correcting the fixture restored its existing text contract; all 12 new tests passed before local generation.
- Warnings match the baseline categories: Unity Catalog Pydantic configuration, Starlette/httpx TestClient, and MLflow predict type hints.
- Preservation and local links are checked in the local [verification record](../../reports/workflow_pilot/draft-usefulness-2026-10-23/verification.json). The engine AST must be identical after excluding its two intended prompt assignments.

Exact full-suite command:

```powershell
.\.venv-pilot-clean\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp/draft-usefulness-full-unrestricted
```

The five workflows took 121.06 seconds in aggregate. The first took about 74 seconds, dominated by its first tool-model call; the other four took about 11-13 seconds each. This is one local run, not a sustained latency benchmark.

Known usage: 15 workflow model calls, 19,379 input tokens and 1,672 output tokens. Internal NeMo usage is unavailable, so token accounting remains incomplete. Hardware/energy and monetary cost are unmeasured.

## Prioritized next work and handoff

1. **P1: request coverage and safe abstention.** d03 discards available facts; d06 substitutes irrelevant facts. Design a narrow request/evidence mapping and relevance gate on development fixtures before another reviewer session. Do not treat another prompt-only patch or NeMo pass as sufficient evidence.
2. **P1: multipart retrieval and complete evidence spans.** d04 selected chart fragments rather than the demand-growth passage. Handle measure/geography and missing subtopics, including the previously observed nickel omission, in a separate retrieval pass within an explicit context/call budget.
3. **P2: requested causal completeness and useful warnings.** d02 omits a supported cause and emits instruction-like meta-commentary; d01 needs explicit geographic/period wording.
4. Freeze fresh facts for later evaluation before further tuning. These inspected cases remain development diagnostics. Retain original reference/source ambiguities and owner disagreements until explicitly adjudicated.
5. Owner reviews the five new drafts. External sessions, usefulness measurements and feedback-driven iteration remain pending; invitations must be arranged by the owner.

This bounded pass is complete, but quality acceptance is not achieved. Changes are saved for review and have not been committed, pushed or deployed. Do not rerun the local attempt script against this directory: it deliberately refuses a second generation start.

## My personal judgement (based on usefulness draft)
- **d01**: The answer is sufficient and can respond to all requests, however, the brief is more complete after adding in the month and year (i.e. August 2026).
- **d02**: The brief is acceptable after correction by adding the factors of the energy/global-oil prices.
- **d03**: Unacceptable. In the output it should have provide the overall information of investment and consumption. Do not discard available evidence for the output because of generic gap labels such as numbers and/or dates because these labels are not provided in the retreived source.
- **d04**: The assessment provided is correct and cited but stated the wrong page. The cited reference is in page 7 and not page 6.
- **d06**: The supplied evidence does not establish Thailand’s exact retail electricity prices for yesterday. I cannot provide a supported figure from these sources.