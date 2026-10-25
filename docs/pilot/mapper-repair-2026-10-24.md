# Mapper contract repair - 2026-10-24

**Contract repair demonstrated on the two synthetic preflights; overall workflow quality gate failed.** Offline tests passed. The five workflow attempts produced three validation failures, one source-inaccurate draft, and one valid abstention. Findings are assistant-authored and are not new human scores.

## Confirmed cause and repair

The previous schema required only component ID, question anchor and status. It allowed short_answer/evidence to be omitted, then conditional validation rejected the empty defaults. All 20 previous components omitted both fields. That was a contract-design defect, not evidence of a Databricks authentication or Ragas failure.

`requested-evidence-v2` makes short_answer and evidence mandatory without defaults. Missing information requires explicit empty values; supported/partial answers still require exact source quotations. Instructions focus on extraction, discourage topic-label components and include supported/missing synthetic format examples. The two probes use different facts, wording and IDs from those examples.

Prompt version is `analyst-pilot-v1.5`. The four-call workflow ceiling, model/context/completion settings, composition/fallback/NeMo behavior, exact no-information message, APIs, page labels, dependency versions and old artifacts are unchanged. The engine changed only its prompt-version assignment in this pass.

## Offline validation

- **157 passed, 3 warnings, 15.28 seconds**, against the 140-test baseline; targeted checks: **89 passed**.
- Seventeen new regressions check required schema fields, absence of defaults, omission failures for every status, explicit missing states, empty supported-state rejection, and format-example completeness. Existing quote/anchor/citation, coverage, abstention, guardrail, approval/export and page-label tests remain in the suite.
- Tests use fixed model responses. They establish contracts and wiring; real extraction and answer quality are assessed below.

```powershell
.\.venv-pilot-clean\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp/mapper-repair-full
```

## Gate 1: two one-shot mapper probes

Fixtures and acceptance checks were frozen before generation. Both ran once, with unchanged local model/settings, and passed:

| Probe | Observed result |
|---|---|
| Answerable | Correct Larch output of 13 MWh in June 2021, exact source quotation and requested scope. |
| Missing evidence | Explicit missing status, empty answer/evidence and a Nimbus price/date gap; the unrelated forecast was not substituted. |

These two synthetic results opened Gate 2; they are not a general benchmark. All seven new mapping responses supplied the answer/evidence fields, so the previous omission defect was not observed in this bounded run.

## Gate 2: five one-shot workflows

| Case | Parsing / mapping / final outcome | Assistant assessment |
|---|---|---|
| d01 | Parsed; mapping invalid; failed | Mapping validation failed: added electronics/automotive/petroleum anchors not in the question. Some quotes also normalize source punctuation. No final brief was produced. |
| d02 | Parsed; mapping invalid; failed | Mapping validation failed: the energy-price quote was assigned to BOT_AUG_2026:0:0 but actually occurs in returned source BOT_AUG_2026:5:0. The candidate also does not fully explain core inflation. |
| d03 | Parsed; mapping valid; answered | A draft reached and passed NeMo, but the consumption claim converts an index-definition note into a causal explanation. It omits the requested consumption direction and activities; the investment clause ends with a truncated 'investment in data'. |
| d04 | Parsed; mapping invalid; failed | Mapping validation failed: quote retypes 'build -out' as 'build-out'. Independently, the assigned passage concerns all energy sources, not regional annual electricity demand. Relaxing punctuation matching would not solve the measure mismatch. |
| d06 | Parsed; mapping valid; abstained | Valid missing-evidence mapping: no claims, exact requested no-information message and a gap for retail electricity prices yesterday. Composer and NeMo were correctly skipped. |

### Why failures remain

- **d01: request scope.** The mapper extracted useful export facts but added electronics/automotive/petroleum question anchors not present in the question. The strict validator rejected the whole mapping rather than silently dropping invalid components.
- **d02: citation assignment.** The energy-price quote exists in returned chunk `BOT_AUG_2026:5:0`, but was assigned to `BOT_AUG_2026:0:0`. Source identity validation correctly rejected it. The proposed answer also failed to cover the core-inflation mechanism completely.
- **d04: quotation fidelity plus measure mismatch.** The model rewrote extracted `build -out` as `build-out`; whitespace-only matching rejected it. More fundamentally, the selected passage discusses all-energy demand, not the requested regional annual electricity measure. Accepting the rewritten punctuation would not fix that semantic problem.
- **d03: source interpretation.** The investment statement uses a chunk ending in the incomplete phrase 'investment in data'. The consumption statement turns a PCI measurement-definition note into an unsupported main-driver explanation and omits the actual direction/activities available in returned `BOT_AUG_2026:1:0`. Both claim IDs resolve, but that does not establish their entailment or completeness. NeMo accepted this draft; the source review did not.
- **d06: valid abstention.** Empty claims and the exact requested no-information message were returned, followed by the gap 'retail electricity prices yesterday'. Composition/NeMo were correctly skipped. This meets the bounded insufficient-evidence criterion; it does not establish general abstention accuracy.

All mapping responses ended normally with stop, not an output-length finish reason. The observed remaining failures are scope selection, source assignment, verbatim extraction and interpretation. The evidence does not justify attributing them solely to GPU capacity or all open-source models.

Budget used: 2 mapper probes plus 16 workflow calls; no case exceeded four workflow calls. Known usage was 21,767 input and 2,059 output tokens across 74.92 generation seconds. NeMo internal usage and monetary/hardware cost remain unmeasured.

## Preservation and next action

Original owner comments, completed CSV, source snapshots and frozen attempts are retained unchanged. The [integrity record](../../reports/workflow_pilot/mapper-repair-2026-10-24/verification.json) checks the snapshot and version identity. No model retries, new Ragas run, hosted inference, commit, push, deployment or reviewer contact occurred.

**Next technical action:** reduce the model's responsibility for inventing request anchors and retyping/citing evidence. Investigate canonical source-span identifiers with server-resolved quotations/citations, and independently validate request coverage. Preserve the current strict checks; do not auto-correct this frozen run or claim that another prompt alone will establish reliability. Source interpretation still needs explicit negative tests such as definitions versus causal explanations. Multipart retrieval remains a separate follow-up.

Your owner judgments remain sufficient for the acceptance criteria. No repeated manual scoring is needed to identify these failures. The new d03 draft and d06 abstention can be inspected in the [local packet](../../reports/workflow_pilot/mapper-repair-2026-10-24/review-packet.md); all new output assessments remain assistant-authored pending owner adjudication.

**Verdict: Request Changes.** The required-field repair worked in this bounded experiment; the full workflow is not qualified for reviewer sessions or production claims. [Structured findings](evidence/mapper-repair-2026-10-24.json) retain the individual checks and artifact hashes.
