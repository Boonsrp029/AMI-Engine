# Source-span selection and wording pass — 2026-10-25

**Implementation and offline validation complete; local quality gate failed.** The first mapper probe selected the correct evidence and passed parsing/validation, but failed the frozen requirement to state the requested period in its short answer. Generation stopped. The other two probes and all five workflows were not run. Assessments here are assistant-authored; no new human scores or owner acceptance are assigned.

## Changes

The [owner wording addendum](adjudication-2026-10-25.md) preserves the original revisions and the subsequently approved choices. The d03 development example uses the BOT explanation of consumption changes rather than treating an index definition as a cause. It is documentation guidance, not a hardcoded answer. The d06 message now refers to retrieved documents; an unavailable-answer gap preserves the whole question. Partial answers remain available and conflicting evidence receives a distinct warning.

Mapping version is `requested-evidence-v3`; prompt version is `analyst-pilot-v1.6`. The private mapper selects canonical span IDs instead of writing quotations and assigning source IDs. Application code resolves each ID to the exact source substring and applies the existing quotation, question-anchor, scope and citation validators. Unknown IDs or invalid mappings fail explicitly without repair calls.

Spans split at sentence boundaries and, when necessary, whitespace to fit 600 characters; longer unbroken tokens split at the limit. Offsets index Python characters in the original source content, not bytes or PDF coordinates. IDs bind source identity, content hash and offsets. No chunks are joined. The mapping payload groups exact spans beneath source metadata without duplicating full chunks. New events retain the catalog, raw selection and resolved mapping.

The four-call ceiling, two tool rounds, model/context/completion settings, retrieval ranking, final NeMo boundary, public Draft/API, SQLite schema, approval/export controls, page labels, dependencies and legacy agent remain unchanged. Span identity establishes provenance, not semantic entailment. The tests explicitly retain a definition-versus-cause example that identity validation alone cannot reject.

## Offline evidence

- **184 passed, 3 warnings**, against the recorded 157-test baseline; 27 new checks. Full run: 17.93 seconds.
- Targeted suite: **116 passed, 2 warnings**, 35.35 seconds.
- Coverage includes exact offsets, punctuation, Unicode, long text, stable identities, source resolution, stale provenance, unknown IDs, required fields, strict anchors, partial/missing/conflicting states and exact revised warnings. Existing composition, guardrail, lifecycle and cached-export checks pass.
- Fixed-response tests establish contracts and wiring. They do not establish actual model quality. Warnings concern existing Unity Catalog/Pydantic configuration, Starlette/httpx and MLflow predict type hints.
- The sandboxed targeted run stalled at local API tests and was stopped. Completed runs used the authorized unrestricted local process for the known Windows asyncio loopback issue.

```powershell
.\.venv-pilot-clean\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp/source-spans-full
```

## Local probe and precise failure

Three fixtures and acceptance checks were frozen before generation: multipart evidence with punctuation/distractors, a missing dated observation, and a causal explanation with a definition distractor. Each had a one-shot allowance with stop on first failure.

The multipart probe asked for Port Alder's grid capacity in April 2022 and the support for its expansion. The model returned two supported components with the correct short answers, **17.5 GW** and **new offshore links entering service**. It selected the exact intended spans, retained the source's unusual punctuation, used valid question anchors and avoided unrelated generation/tariff material.

The failed frozen check required **April 2022 in short-answer text**. That date appeared in the question anchor and resolved quotation, but not in the short answers; optional global geography/period fields were empty. This is a scope-completeness failure under that criterion. It is not an incorrect capacity figure, invalid mapping, source-assignment failure or proof that a composer would necessarily omit the date. Composition was not run. The criterion has not been relaxed after observing the output.

| Validation layer | Result |
|---|---|
| Parsing and required fields | Passed |
| Span/source identity, exact punctuation and question anchors | Passed |
| Correct figure, expansion explanation and distractor exclusion | Passed |
| Self-contained requested period in answer | Failed |
| Missing-evidence and causal-definition probes | Not run after stop |
| d01/d02/d03/d04/d06 workflows | Not run; Gate 1 failed |
| Owner acceptance of new analyst drafts | No new analyst drafts |

The single call used 761 input and 100 output tokens over 59.51 seconds, with a normal `stop` finish reason. No truncation was observed. There were zero composer, workflow, NeMo or Ragas calls. This evidence does not establish a GPU-capacity problem or an inherent limitation of open-source models.

## Next action and manual review

Close the scope-propagation contract before another run: supported geography/period or self-contained scoped answers need a validated path into composition. Add offline regressions for the observed fragment-only answer; do not infer measurement dates from publication metadata. Keep this frozen run and its checks unchanged. The untested missing-evidence and causal-definition behavior, real corpus outputs and later multipart retrieval work remain unresolved.

**No mandatory new owner scoring is required now:** there are no new completed analyst drafts. The [local diagnostic packet](../../reports/workflow_pilot/source-spans-2026-10-25/review-packet.md) allows optional inspection of the synthetic result and exact spans. Leave `human_review.csv` unchanged. When revised workflows yield assessable drafts, the owner must review factual support, completeness and usefulness—especially d03's causal explanation—and approve the exact revision before export. Independent usefulness still requires external reviewer task sessions.

The [structured findings](evidence/source-spans-2026-10-25.json) retain checks and provenance. The [integrity record](../../reports/workflow_pilot/source-spans-2026-10-25/verification.json) covers original hashes, preserved boundaries and local links; the [handoff](../../reports/workflow_pilot/source-spans-2026-10-25/handoff.md) identifies the next technical action. No historical outputs, owner judgments or manifests were rewritten. No retries, hosted inference, commit, push, deployment or reviewer contact occurred.

**Verdict: Request Changes.** Source-span selection worked in this single synthetic probe; end-to-end answer quality and the remaining gates are unverified.
