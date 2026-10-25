# Analyst workflow review checkpoint - 2026-10-25

**Assistant-authored; owner decisions pending. Functional quality gate: FAILED.**

One nonempty draft reached the review boundary, but source inspection found a material scope error. This is a checkpoint for adjudication and engineering diagnosis, not completion of the analyst workflow or evidence of production readiness. No brief has been approved or exported.

## Implemented changes

The private mapper now preserves explicit known/unresolved geographic states with span provenance. Geography selected from another sentence in the same retrieved record is retained as source context and triggers a review warning. It cannot establish a measurement period. Narrow source-qualified names can be normalized with the original value and normalization retained; country aliases and issuer-based inference remain unsupported.

Application-owned, verbatim request slots replace model-written question anchors. The generated schema uses positional request slots with literal IDs, preventing extra, missing, repeated or reordered request components during decoding. Strict post-parse coverage validation remains. This is a conservative lexical question splitter, not a general task-understanding system.

The composer returns component IDs and text; the application derives citations from that component's validated evidence. The existing deterministic fallback retains omitted supported components. These controls establish traceable identities, not entailment or complete answers.

Geographic decoder choices are bounded source-literal labels, with their permitted span references. Date occurrences are excluded; an independently occurring same-word place can remain available. The labels are **untyped**: capitalized organizations and headings can still be selected incorrectly. This limitation was observed in real attempts and remains unresolved.

The final mapping instructions were shortened and prohibit asserting a period copied only from the question. Current versions are `requested-evidence-v12` and `analyst-pilot-v1.15`.

Public `Draft`, APIs, SQLite schema, legacy agent, retrieval ranking/corpus, dependencies, model parameters, four-main-call ceiling, configured final NeMo check and approval controls remain unchanged. Stored PDF indexes remain zero-based; displayed PDF pages remain index plus one. This pass did not activate Databricks or run Ragas.

## Validation and real-output findings

The full offline suite passed **276 tests**, with three existing dependency/type-hint warnings, in 43.65 seconds. The final command was:

```powershell
.\.venv-pilot-clean\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp/positional-full
git diff --check
```

An earlier targeted invocation failed six assertions that still expected the preceding prompt version. The version assertion was updated; the full suite subsequently passed. Fixed-response tests establish contracts and lifecycle behavior, not model quality.

Three frozen synthetic mapper probes passed and their outputs were inspected: a multipart quantity/infrastructure request, supported facts with unknown geography plus an unavailable current observation, and a causal passage with a definition distractor. The subsequent five real workflows each ran once, without retries, against the unchanged local `ami-llama3.1:8b-4k` model (4096 context, 900 completion, temperature zero).

| Case | Actual result | Source assessment and next action |
|---|---|---|
| d01 | Mapping rejected; no final draft | Geography came from another record. The first short answer was an export topic label rather than its supporting cause. Engineering diagnosis; no owner rating requested. |
| d02 | Mapping rejected; no final draft | Geography selected an issuer label from another record. The answer selected external monitoring factors despite the retrieved inflation explanation on BOT PDF page 6. Engineering diagnosis; no owner rating requested. |
| d03 | Mapping rejected; no final draft | A heading was selected as geography. Investment text ended at a chunk boundary and consumption coverage was absent. A PCI definition does not establish causation. Engineering diagnosis; no owner rating requested. |
| d04 | Nonempty revision 1; configured NeMo passed | **Reject recommended.** The claim substitutes Indonesia peak demand for regional electricity demand and omits the requested magnitude. The unresolved-geography warning did not prevent the composer from adding regional wording. |
| d06 | Empty, evidence-limited abstention | Appropriate against the retrieved historical material. Preserves the original question and requested date in the gap. Owner may acknowledge the wording; this is not an exportable brief. |

### d04: unresolved geography was inspected before approval

The selected source is `IEA_SEA_2024:139:0`, stored index 139 / **PDF page 140**. The full rendered figure caption identifies peak electricity demand by sector and driver **in Indonesia**, in STEPS and APS, for 2023-2050. A 2035 bar does not make it the regional annual-demand passage.

The unchanged generated claim says:

> Peak demand increases by 2035 in the IEA's Southeast Asia Energy Outlook 2024 STEPS scenario.

Its title says `Southeast Asia, 2024-2035`. Neither the selected Indonesian figure nor an unresolved-geography warning establishes that regional framing. This is a synthesis/scope error alongside a retrieval miss. A valid citation identity and NeMo pass did not establish semantic support.

The full-source regional passage is on stored index 6 / **PDF page 7**: regional electricity demand grows about 4% annually to 2035 in STEPS, from over 1,300 TWh to above 2,000 TWh. This page was absent from the five retrieved records in this attempt. It is audit evidence, not retroactively added model context. The page-display calculation is correct; selecting the wrong page is a separate problem.

Both pages were rendered and visually inspected from the pinned [IEA snapshot](../../data/external/market_sources/iea_sea_2024.pdf). Detailed source text and page images remain in the ignored local review directory. Source URL: [IEA report](https://www.iea.org/reports/southeast-asia-energy-outlook-2024). No current-world economic or online availability verification is implied.

## Retained evidence and integrity

- [Local review packet](../../reports/workflow_pilot/positional-request-validation-2026-10-25/review-packet.md): exact generated outputs, source excerpts, rendered pages, revision identities and assistant findings.
- [Owner decision worksheet](../../reports/workflow_pilot/positional-request-validation-2026-10-25/owner-review.json): pending decisions; no scores or approvals prefilled.
- [Structured assessment](evidence/analyst-review-checkpoint-2026-10-25.json): same case findings, provenance, integrity record and generation totals.
- [Local generation ledger](../../reports/workflow_pilot/positional-request-validation-2026-10-25/generation-ledger.json): includes all unsuccessful experiments in this goal, not just the final batch.

Across ten retained development experiments, there were **19 mapper probes and 15 workflow attempts**, using **66 main model calls** in total. Known usage was **96,613 input / 7,669 output tokens**. NeMo internal usage is incomplete; monetary and hardware costs were not measured. These counts exclude Codex reasoning and fixed-response tests. No matched improvement or sustained performance claim is made.

The goal-start 332-file snapshot was checked: 322 files remain byte-identical and ten expected implementation/test files changed. New modules, tests and this report are additional files. No baseline file is missing. Historical reports, owner comments, the completed human-review CSV, source PDFs, corpus, earlier attempts, dependency manifests and constraints remain unchanged against that snapshot. The original CSV's current verified SHA-256 is `88fd2d1a1d0c31d47cc39fd768c702ca61a1ecb619a116d679a5061ebcc8e64b`.

The separate local review database preserves d04 and d06 as revision 1 with `needs_review`; d01-d03 are failed runs. Imported draft/source bytes match the frozen results and revision digests. Unapproved exports were blocked. There are **zero human reviews and zero exports** in this new review database. Existing historical approval records are untouched.

## Manual review and exact next step

1. **Owner review required for d04's semantic decision:** inspect revision 1 and the two rendered source pages. The assistant recommends rejection; do not approve it to force an export. A reply such as “reject d04 revision 1” identifies the exact decision. No numerical rescore is needed.
2. **Owner wording review optional for d06:** acknowledge its source-limited abstention or request changes. Empty claims cannot be approved/exported as a factual brief.
3. **No owner review required for d01-d03 technical failures:** repair selection and coverage in code rather than asking the owner to score them.
4. **Approval required before any later export:** verify support for that exact revision and its unchanged digest, record the owner's explicit decision through the existing review lifecycle, then export. Any edit creates a new revision and requires fresh approval.
5. **External usage review remains later work:** no independent reviewer sessions or usefulness claim were created.

The next engineering priorities are: prevent headings/issuers from becoming geographic evidence without weakening provenance checks; prevent composed scope/measure changes from overriding the mapped evidence; and evaluate complete source spans/multipart retrieval separately, including the missed regional passage and truncated consumption/investment context. Retain these cases as inspected development diagnostics and freeze fresh facts before later evaluation.

The goal remains incomplete at this checkpoint. Work is saved for human adjudication, with no commit, push, external deployment or reviewer contact.
