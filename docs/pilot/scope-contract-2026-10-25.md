# Scope propagation contract — 2026-10-25

**Offline implementation and checks complete; new model quality remains unverified.** This pass addresses the retained mapper's fragment-only answer without changing its frozen failure record. No mapper, composer, NeMo or Ragas generation ran. The [structured findings](evidence/scope-contract-2026-10-25.json) distinguish deterministic evidence from actual model quality.

## Behavior and limits

The private scope helper conservatively recognizes full English month/year and valid ISO dates. An unambiguous requested period can be retained when a selected quotation contains both that period and the verbatim short answer. Publication-date metadata is not consulted; quotation sentences containing publication cues are excluded from this period qualification. Mapper-provided geography and period must occur in selected supporting quotations rather than only in the question.

The final claim retains verified literal qualifiers when the composer or fallback omits them. Qualifiers apply only to components whose selected quotations contain that scope. Their supporting source IDs remain in the displayed citations. Recognized periods invented in composed claims and overlong qualified claims fail explicitly, without silent truncation. Final text, including qualifications, reaches the unchanged NeMo boundary and still needs exact-revision human approval for export. A new `evidence_scope` event records scope provenance and unresolved requested periods.

These are provenance and presentation checks, not a semantic parser. A place/date occurring in a passage does not prove it qualifies the measurement. Publication-cue screening and literal-answer colocation are conservative heuristics that can leave scope unresolved. Missing geography remains blank; there is no general geographic extraction or alias resolution. Bare years, abbreviated months, relative dates and multiple requested periods are not automatically inferred. Supported partial answers are preserved; no new missing-evidence warning is invented merely because geography metadata is blank.

Mapping version is `requested-evidence-v4`; workflow version is `analyst-pilot-v1.7`. Existing instructions, local model/settings, four-call ceiling, retrieval, span identities, exact quotation/anchor validators, public Draft/API, SQLite schema, guardrails, dependencies and approval/export controls remain intact. There is no new model call or repair loop.

## Offline evidence

The final full suite passed **204 tests with three existing warnings**, against the 184-test baseline. Twenty scope checks cover fragment-only answers, component-specific scope, required citations, duplicate-label avoidance, conflicting date wording, publication-date and unrelated-date traps, ambiguous periods, unknown geography, length limits and the final guardrail boundary. The scope-only suite passed 20 tests. Warnings remain Unity Catalog/Pydantic, Starlette/httpx and MLflow predict type hints.

```powershell
.\.venv-pilot-clean\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp/scope-contract-full-final
```

The [offline reconstruction](../../reports/workflow_pilot/scope-contract-2026-10-25/offline-replay-final.json) reads the unchanged retained selection and uses an explicitly scripted empty composition. Its capacity claim becomes **April 2022: 17.5 GW**, with the period retained in the title. The cause remains unchanged because its own quotation does not state a date. Geography is not guessed. This proves the deterministic fallback path for that input; it does not show what a real composer or NeMo would return. The previous [source-span gate](source-spans-2026-10-25.md) remains failed, and its two remaining probes and five workflows remain unrun.

The saved checklist, completed CSV, owner judgments, sources and frozen attempts are preserved. [Integrity verification](../../reports/workflow_pilot/scope-contract-2026-10-25/verification.json) records hashes and unchanged execution boundaries. No scores or acceptance were inferred from the owner's act of saving a checklist.

## Where manual human review is required

| Point | Required now? | Human responsibility |
|---|---|---|
| Scope code, regression tests and offline reconstruction | No | Optional inspection; these are engineering checks, not new analyst results to score. |
| Fresh actual drafts that pass technical checks | Not yet available | Review source support, causal completeness, geography, measurement period, projection/observation distinctions, useful partial answers and gaps. Pay particular attention to d03. |
| Export of an actual reviewed brief | Yes, when exporting | Approve that exact revision through the existing workflow. |
| Claims of independent usefulness | Later | External reviewers complete real tasks and provide feedback. |

The [new local packet](../../reports/workflow_pilot/scope-contract-2026-10-25/review-packet.md) provides these review points. Leave `human_review.csv` unchanged now. Technical failures should be diagnosed before asking the owner to score another draft.

## Next technical step

Prepare a new bounded local experiment with fresh scoped-multipart, missing-dated-observation and definition-versus-cause fixtures. Freeze checks before generation; test end-to-end scope retention rather than requiring every raw answer fragment to repeat the date. Only passing probes should open conditional workflow attempts. This would be a new experiment, not a replay or relabeling of the stopped run. The [handoff](../../reports/workflow_pilot/scope-contract-2026-10-25/handoff.md) retains the exact state and limits.

**Verdict: Request Changes.** The offline scope contract is stronger, but actual mapper/composer quality, geographic coverage, retrieval completeness and enterprise readiness remain unverified. No commits, pushes, hosted inference, deployment or reviewer contact occurred.
