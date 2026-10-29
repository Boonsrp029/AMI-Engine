# Proposed reduced v1.50 diagnostic

**Execution update: authorized, executed and stopped at r06; budget closed.** The mapper and r05 passed; r06 omitted the required country/count comparison despite technical success. See [actual findings](diagnostic-v150-findings.md). The frozen proposal below predates that grant. The [offline repair](quantity-slots-2026-10-28.md) passes 783 Windows and 782 Linux tests, recovery and frozen-response checks. Those results do not establish actual model selection or answer quality. The v1.49 budget stopped at r05 and is closed.

This proposal reduces repeated generation while directly testing the retained failure:

| Stage | Cases / deadline | Budget and gate |
|---|---|---|
| Mapper | Actual consumed r05 question and retained sources, once, 60 seconds | One local mapper call; no tool-planning generation, composer or NeMo. Two fixed tool turns use actual local retrieval and engine preparation/validation. |
| Conditional workflow | r05, then r06, once each, 180 seconds per case | Only after the mapper passes technical AND assistant source/completeness checks. At most eight workflow calls and two NeMo invocations. Inspect each output before continuing. |

Combined ceiling: **nine main model calls plus two NeMo invocations**. Stop all generation at the first technical or source-quality failure. No retries, automatic tuning, budget reuse after a failure/code change, Ragas, hosted inference, twenty-case run, approval/export, external deployment or reviewer contact. NeMo internal tokens/cost remain incompletely measured.

The mapper input is captured from the actual current engine using fixed tool-turn responses, rather than a separate simplified schema/prompt builder. The capture makes zero model calls, freezes `as_of=2026-10-28`, and stops before composition is bound. A future authorized call must reproduce its exact messages/schema and pass the actual engine's mapping/scope/quantity checks. All expected answers below remain outside model messages; the original question, sources and request-slot instructions are the model input.

r05 must retain the application value (THB 1.14 trillion or the source-provided USD 33 billion equivalent), 3,137 projects, 35% value growth and 40% count growth with correctly assigned evidence and 2024-versus-2023/application scope. Contact details and FDI-subgroup statistics cannot substitute. r06 must preserve 73% FDI/all-application-value, Singapore's leading FDI value (THB 357.5 billion / 43% of FDI), and China's 810 versus Singapore's 305 projects without mixing denominators or value/count rankings.

r03/r04 are not rerun in this reduced diagnostic. Their prior owner adjudication remains attached to the exact older content, with country edits requested; it is not fresh v1.50 generation evidence. This consumed development check cannot establish the held-out quality gate or release/production readiness. Same-identity release checks and fresh quality remain later requirements.

Immutable contract: `reports/workflow_pilot/production-readiness-2026-10-27/resume-v9/diagnostic-proposal-v150/contract.json`, SHA-256 `5a5fe49004396ca8585279446db2990db6f091c0dfa8d67f328acf41a83a269e`. Expected generator `c46162eb97a6839d1ba13de703ef49d8a84ebd3a833aa5a20e8b8465c337810e`; model `ami-llama3.1:8b-4k`, expected digest `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`, unchanged context 4096/completion 900/temperature 0. Expected identities are checked before and after execution; this proposal is not a new live model-availability check.

Retain raw/parsed response, exact input/schema, span/catalog provenance, actual engine validation trace, model/prompt/source identities, process outcome, timings, available tokens and failures in new directories. Fixed-response capture tests remain separate from actual model results. No scoring request is needed for malformed/invalid mappings. Technically valid final workflow outputs require owner source/completeness acceptance; exact-revision approval remains necessary before export. Independent reviewer sessions remain separate and owner-arranged.
