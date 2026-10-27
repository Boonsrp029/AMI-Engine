# Guardrail process and policy findings — 2026-10-27

The earlier diagnostic returned a passed NeMo result and saved the intended draft, but the process exited nonzero. The new diagnostic uses a parent subprocess supervisor, captured UTF-8 stdout/stderr, a 90-second deadline, Python fault handling and explicit normal-exit markers. Every variant is retained separately; no complete workflow generation or Ragas run was repeated.

| Controlled variant | Result |
|---|---|
| Import only | Exit 0; no background threads |
| Existing synchronous check, Windows Proactor loop | Passed result, then native `0xC0000008` during garbage collection after exit markers |
| Same check with documented telemetry opt-out | Same crash, despite no telemetry threads; telemetry is not a sufficient explanation |
| Initialize only, Proactor | Exit 0 |
| Initialize only, Selector | Exit 0 |
| Same check, Selector | Passed result, exit 0, empty stderr |
| Same check through new launcher policy helper | Passed result, exit 0, empty stderr |

Windows identifies `0xC0000008` as invalid handle in [Microsoft's status-code reference](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a1078-e883-4972-9bbc-49e60bebca55). The installed NeMo 0.23.0 synchronous `check()` obtains a thread event loop and runs `check_async()` on it. The controlled evidence associates this cleanup failure with the Proactor/check path; it does **not** identify a specific native extension or prove an upstream root-cause fix. Import/initialization alone did not reproduce it. The telemetry control is documented by [NVIDIA for 0.23.0](https://docs.nvidia.com/nemo/guardrails/v0.23.0/resources/telemetry); disabling it did not fix the failure.

`python -m src.pilot.launch` is the tested operational mitigation: it selects Windows' Selector policy before importing the application, only in the explicitly launched process. Importing the launcher has no effect; Linux and the old public APIs/entry points are retained. Seven targeted launch/guardrail contract tests passed. This is a Python 3.12 mitigation, not a library upgrade or universal guarantee for other event-loop-dependent applications.

Detailed native-process evidence is under ignored `reports/workflow_pilot/production-readiness-2026-10-27/guardrail-process*`. Four check invocations used frozen d02 text; two additional initialization probes and one import probe did not generate analyst answers. No automatic retries were used. Per-request/internal LLM usage was not instrumented, so these are guard invocation counts, not judge-token counts.

## Separate critical policy finding

Installed NeMo's `library/hallucination/flows.v1.co` runs `self_check_hallucination` only when `check_hallucination` is true. The current wrapper does not supply that flag. Its action also relies on a previous bot-generation prompt, which an externally composed report does not supply. That action is a self-consistency check, not proof of support by retrieved sources.

Therefore, historical `passed_guardrails` values must not be presented as evidence that this grounding check actually executed. This does not invalidate separately source-reviewed owner judgments. The activation gap was treated as a release blocker and repaired as follows; semantic quality qualification is still pending.

## Source-grounding repair and bounded validation

The existing output-policy configuration now uses NeMo's installed `self check facts` flow with `check_facts=True`, real `relevant_chunks`, and a prompt using the action's actual `evidence`/`response` keys. A narrow custom output parser preserves NeMo's `[is_unsafe]` polarity and accepts only a standalone affirmative verdict (`YES`, optionally followed by one period). Empty, uncertain, mixed and explanatory responses block. Empty report/evidence blocks without judging. The fact-check completion is capped at 32 tokens; the analyst model/context settings and dependencies are unchanged.

Tests execute the actual Colang runtime with a fixed LangChain judge adapter. They assert that the judge is called once and sees the exact report and source text, that negative/malformed responses and outages cannot pass, and that an affirmative verdict cannot bypass the topic policy. The explicit supported Windows loop fixture is necessary: the first real-engine test command printed passing assertions but reproduced the native exit; its failed process status/log is retained. Tests were rerun only after applying the already diagnosed loop mitigation. The fixed-response tests do not establish model correctness.

One new local check reused frozen d02 text and returned `YES.`. The initial literal-only parser blocked it; that failed diagnostic remains recorded. After the narrowly specified punctuation contract passed offline checks, one separate follow-up returned `YES.`, invoked the facts parser once, passed, and exited 0 with empty stderr through the supported launcher. There was no model-based repair loop, new analyst generation, Ragas run or owner rescoring. This verifies activation/format interoperability for one retained example; it does not establish general entailment or adversarial resistance.

The initial process investigation used four frozen-text check invocations with the old policy, plus initialization/import probes. The source-policy investigation used two additional local check invocations. Only the latter two have an observed judge response; internal request retries/token usage remain unavailable. Detailed inputs/configuration hashes and stdout/stderr are retained in the separate diagnostic directories. Approved outputs, previous reports and human judgments were not modified.
