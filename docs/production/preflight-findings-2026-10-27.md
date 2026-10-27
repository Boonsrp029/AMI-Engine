# Fresh evaluation preflights — retained failures

Status: **quality gate failed; held-out generation has not started**. Findings are assistant-authored engineering assessments, not owner approvals or human ratings. Source preparation and owner-confirmed thresholds are in [the protocol](evaluation-protocol.md).

## Attempt accounting

| Directory | Attempt | Main workflow calls | NeMo invocations | Result |
|---|---|---:|---:|---|
| `preflight-v1` | p01 once | 4 | 0 | Composition assigned an unestablished period; strict validation failed before safety |
| `preflight-v2` | p01 once, following explicit owner authorization | 4 | 1 | Composition fallback retained evidence; final source-facts judge rejected it |
| Both directories | p02 | 0 | 0 | Unattempted after stop condition |
| Held-out package | r01–r20 | 0 | 0 | Unattempted; no qualification denominator or score yet |

The first preflight budget was eight main invocations. The owner then explicitly authorized one new two-preflight pair, adding at most eight and bringing the cumulative ceiling to twelve. Actual use was **eight main workflow invocations**, one NeMo invocation, **4,849 known input tokens and 628 known output tokens**. NeMo internal tokens and provider-internal retries remain unavailable. No Ragas, hosted inference, automatic retry, human approval or export occurred. Each worker was bounded by 180 seconds; neither timed out.

## First failure and focused repair

Retrieval returned the development fixture's two quantities and warehouse-capacity explanation. The mapper selected valid exact source spans. However, the composition payload offered global May 2023 scope even though the cost component's selected quotation did not establish that period. Composition copied the month onto that claim and omitted its requested cause. The cause-omission heuristic recognized “why” but missed “which factor explains”. The period validator correctly rejected the result.

Prompt `analyst-pilot-v1.27` supplies established scope per evidence unit. A dedicated `UnsupportedClaimPeriod`, still a `ValueError`, identifies that narrow failure. The application rejects the offending composed sentence and uses the original selected excerpt, then reapplies citation, period, measure, numeric and size validation. It does not infer a missing date or relax those checks. The causal omission check now also recognizes “which/what factor explains”. Fallback remains explicit in events and warnings, within the four-call limit and before the final NeMo check.

The unchanged saved response now replays successfully with both quantities and the exact causal excerpt. This is **fixed-response plumbing evidence**, not new model-quality success. The period remains unresolved for the second claim and is reported as such. Even a policy pass would not prove complete temporal support.

## Second failure

The authorized actual generation reached the final NeMo check. Its rejected composed cost sentence was replaced with the exact selected excerpt containing the warehouse-capacity explanation. The judge returned `NO.` followed by an explanation describing that causal phrase as an instruction in source evidence. The strict parser blocked the response. The worker then exited with an ordinary workflow exception; this was not the earlier Windows native cleanup crash.

The retained rationale is evidence of a false instruction classification for this synthetic passage. It does not establish that every other aspect of the draft is semantically correct, or that the model would fail all other sources. The response also violated the single-verdict format. Its leading negative verdict would block even with a permissive parser, so relaxing the parser would not fix this attempt.

A zero-inference prompt inspection confirmed the exact supplied evidence/report were rendered without unresolved template variables. The prompt was 909 characters, the adapter was NeMo's `OpenAIChatModel` using the configured local Ollama-compatible endpoint, and the configured task completion limit was 32 tokens. Actual wire options and internal token counts were not captured. This provides no evidence of context exhaustion and does not prove that the provider enforced every configured limit. The retained prompt inspection is `policy-render-v1.json`.

Classification: first failure was an application composition/scope contract defect; second was a local model/policy judgment failure. Neither shows GPU out-of-memory, context exhaustion, provider authentication failure or an inherent inability of open-source models. Do not bypass NeMo or credit this as a safe, useful answer. Generation remains stopped and the quality gate remains failed.

## Next technical action and human checkpoints

Prepare a small, frozen policy diagnostic separating supported causal statements, unsupported claims, actual embedded commands, and legitimate uncertainty warnings. Inspect the exact rendered policy prompt and model context limits. Validate prompt/adapter changes offline before proposing any additional bounded local judging; do not repeatedly run the entire analyst workflow or consume held-out facts for this diagnosis.

No human usefulness scoring is requested for these technical failures. Human source adjudication becomes necessary for technically valid new outputs before owner acceptance. Independent reviewer sessions, exact-revision approval/export and rollout acceptance remain separate human checkpoints. Docker repair is pending the owner's reported readiness; no external deployment is authorized.

Detailed inputs, raw/parsed responses, source spans, identity hashes, process results, replay and authorization are retained under ignored `reports/workflow_pilot/production-readiness-2026-10-27/`. Historical evidence and approved outputs remain protected.
