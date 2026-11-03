# Reduced r05 v1.62 diagnostic proposal — 2 November 2026

**Prepared; not authorized or executed.** This is a consumed development case, not a held-out quality evaluation. The earlier v1.60 result remains failed and its allowance closed. Resuming the Goal does not grant new inference.

## Purpose and preserved behavior

The [financial comparison repair](financial-comparison-coverage-2026-11-01.md) addresses missing selections and loss of selected quantities during composition. Test whether the unchanged local model can use that contract on r05. Public APIs, dependencies, retrieval, model settings, approval/export controls and historical evidence remain unchanged. Literal coverage and exact provenance do not establish semantic support.

The question asks for Thailand BOI's 2024 investment-promotion application value and project count, and how each changed from 2023. Require 1.14 trillion baht and reported 35% value growth, the adjusted 846.5 billion baht baseline, and 3,137 versus 2,235 projects with reported 40% growth. Distinguish application commitments from realized investment and value from counts. Preserve the owner's source-supported data-centre/cloud and semiconductor/advanced-electronics detail as a separate editorial completeness requirement. Do not invent a 2023 USD figure or substitute USD-only figures for the baht comparison.

The pinned BOI press release is dated 13 January 2025; that publication date is not the 2024 measurement period. Source records `BOI_2024:unit:0:0` and `BOI_2024:unit:1:2` correspond to zero-based indexes 0 and 1 / PDF pages 1 and 2. Source: [BOI release](https://osos.boi.go.th/article_attach/PR4_2568EN.pdf). Use the pinned local snapshot; this preparation makes no new web or model request.

## Frozen request and identity

The local packet is `reports/workflow_pilot/production-readiness-2026-10-27/resume-v77/diagnostic-proposal-v162/`. Its `contract.json` SHA-256 is `714bba1762afdf6c1ccbcb7f856d8e77c55c32d666c5ceb880c213cfa7ec3b1b`; generator SHA-256 is `0a1796d93f98a32ac9317f0a6bf7c92498823686d1064218ddcb45aaf255c875`.

Runtime is analyst-pilot-v1.62 / requested-evidence-v42, source-selection-v1. Expected model is `ami-llama3.1:8b-4k`, digest `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`; context 4,096, completion 900, temperature 0. Live identity/readiness has not been verified during preparation and must be checked after authorization. Package v2 manifest is pinned to `f28098dc9e43ce2048f154f9b3e59c5fd99ea9c67d682e97ec2179131925aa20`.

The mapper request replays retained tool turns with as_of 2026-11-01. A conditional full workflow records its actual execution date. This absolute historical question is not a matched timing experiment. Current instructions are 13,434 characters and schema 8,122 characters; actual token count and context fit remain unknown until execution. Historical token counts do not prove current fit.

## Two gated phases and budget

1. One mapper request: at most 60 seconds for the service and 30 seconds for offline validation within a 95-second timed envelope. Read-only contract/grant checks precede entry. Retain raw response, finish reason, identity, usage, timing, validation and source selections.
2. Only after technical success and a separate assistant-authored source/completeness assessment passes: one full r05 workflow, at most 180 seconds including identity preparation. The source gate must be bound to the contract, acceptance file and actual transport/validation results; synthetic fixtures cannot pass it.

Combined ceiling: **five main-model calls and one NeMo invocation**. Once per phase, stop at the first technical, source-support, completeness or time failure and close unused allowance. No retries, warmup inference, tuning, other cases, twenty-case evaluation, Ragas, hosted inference, approval/export, publication, deployment or reviewer contact. Backend cancellation is not proven; timed-out in-flight usage must be reported unknown rather than retried. NeMo internal token/call accounting remains incomplete.

Inspect source applicability, requested years, quantities, denominators, citation identity and useful warnings. Final output must be readable paragraphs without bullet graphs. Record raw composition and fallback separately; a NeMo pass or restored source excerpt is not independent evidence of complete synthesis.

## Offline evidence and its limits

The application repair retains 1,181 passing Windows tests and 1,180 passing Linux tests plus one skip, clean dependency checks and successful container recovery with four byte-identical cached exports. These logs are from resume-v76, not newly rerun for this documentation pass or evidence of remote CI.

Protocol preparation adds six fixed-selection checks, intercepted SDK request-body parity, 13 controller tests, normal and optimized-Python missing-grant rejection, and an actual offline validation subprocess with sockets blocked (13.375 seconds, under its 30-second bound). The first harness-directory failure is retained; corrected fixture invocation mirrors supervisor ownership. All service responses used here are explicitly synthetic, with zero model requests. These checks prove mechanics, not real selection quality or source completeness.

## Human checkpoints

- Before inference: a new direct grant, **Authorize reduced r05 v1.62 diagnostic**. Previous allowances cannot be reused.
- Technical failures and fixed fixtures: engineering diagnosis; no repeated owner scoring required.
- A new assessable final output: owner must check source support, factual completeness, wording and warnings before it is called owner-accepted. The assistant's intermediate source gate is not owner acceptance.
- Saving an approved brief: approval of that exact stored revision remains necessary; this protocol grants no approval or export.
- Independent usefulness and production acceptance: later real reviewer sessions and target-environment qualification remain pending.

Neither portfolio completion nor production qualification is established by this diagnostic. The full [Goal](../production-readiness-goal.md) remains in force.
