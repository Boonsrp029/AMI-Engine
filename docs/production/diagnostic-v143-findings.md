# v1.43 consumed-case diagnostic — 28 October 2026

**Assistant-authored assessment: source-quality gate failed; generation stopped.** The owner authorized r03–r06 once each, with at most 16 main calls/four NeMo invocations and a 180-second deadline per case. Only r03 ran. r04, r05 and r06 are unattempted; the twenty-case set was not authorized or run. Unused budget is not a retry allowance after changing the generator.

r03 exited cleanly in 50.85 seconds with matching generator/package/model identities. It used four workflow calls, one NeMo invocation, 3,877 known input tokens and 380 output tokens. NeMo internal tokens, energy and monetary cost remain unknown. The mapper and composer parsed, the narrow validators passed, and the final guardrail allowed the answer. This was not a process, schema or demonstrated GPU-memory failure.

The answer repeated the broad energy-inflation statement in two claims, citing the summary and detailed paragraphs separately. It retained the supported core-inflation explanation about offsetting prepared-food/cooking-ingredient and cleaning-equipment movements. It omitted the requested headline-inflation causes: the prior subsidy base effect and rising benzene prices. The detailed explanation was retrieved in `BOT_DEC2024:unit:13:0`, article paragraph 14/extracted line 248. Geographic and per-component historical-period warnings also remain unresolved. No owner acceptance, approval or export is inferred.

## Confirmed implementation failure

The causal continuation span `s_c0436b5037762f88` was present in the catalog but absent from r1's permitted subject view. The decoder permits extra evidence only from that view's span IDs, so this was an application-imposed exclusion, not simply a model omission. The continuation does not repeat its financial subject, and the current subject checker only inherits a qualifier for an explicit generic measure. Separately, the hyphenated headline-inflation wording matched generic inflation rather than the specific headline measure; the resulting view also admitted core-inflation material. The saved candidate selected two duplicate broad statements and none of the excluded causal detail.

Next repair: freeze synthetic regressions for hyphenated measure qualifiers and bounded same-record causal continuations; verify decoder eligibility as well as post-selection validation. Preserve exact source offsets, scope, unknown classifications, four-call limits and final NeMo. Do not repair this by hardcoding the consumed answer, silently filling missing model fields, relaxing source identity, changing the model or starting another batch. Duplicate statements across different source IDs require a separate provenance-aware composition check; existing exact-unit sharing does not deduplicate them.

## Evidence and remaining human work

Local evidence is in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v3/development-v143/`: raw attempt, model responses, source catalog, process result, budget, failed source gate and summary. Attempt SHA-256: `cfe9919b88ac1b050f6f5e18ac2895d203664776aefe4195499fdfb87060a230`. The expected full generator identity is `a7ed49a172c606f4c46e0371be6eb4600f59f5725590fac326c86fd92975c5e7`; the model digest remains the predeclared pin.

No repeated manual scoring is requested for this failed development gate. The owner may dispute this assistant assessment with source locators. Future assessable outputs still need source-grounded human adjudication before being called accepted; exact revision approval remains necessary for export. Independent reviewer sessions remain pending. The full goal, portfolio milestone and production qualification remain incomplete.

The separate [HTTP intake repair](request-intake-2026-10-28.md) passed 618 Windows /617 Linux tests plus one Windows-only skip, with 15 warnings, and actual chunked-container rejection/recovery checks. Those engineering results remain valid; they do not establish generated-answer quality.
