# Proposed r06-only v1.52 diagnostic

**Prepared only; no new model-run authorization.** The [transport-v1 allowance](diagnostic-transport-v1-findings.md) closed at its false-conflict source failure. The [offline repair](false-conflict-repair-2026-10-29.md) cannot reuse that allowance.

Use the frozen actual consumed r06 question and evidence, unchanged local model `ami-llama3.1:8b-4k`, digest `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`, context 4096, completion 900 and temperature zero. Current generator is `ef2e2cd044de99b050ddd9250649a9d812d1d57c049f0f193343b58d09e70a77`; prompt v1.52 / mapper v37. Original failed responses and owner-reviewed editorial candidates remain separate.

1. One mapper request through the tested lightweight diagnostic worker. **95 seconds total:** service child at most 60 seconds, separate offline actual-engine validation at most 30 seconds, five seconds reserved for orchestration. No warm-up or retry.
2. Only after transport, engine validation and hash-tied assistant source/completeness checks all pass: one complete r06 workflow, at most 180 seconds, four main calls and one NeMo invocation.
3. Combined ceiling: **five main calls and one NeMo invocation**. Stop at the first technical/source/completeness failure. No Ragas, hosted inference, twenty-case evaluation, approval/export, deployment or reviewer contact. Internal NeMo usage remains incompletely measured. A client timeout does not prove backend cancellation.

Mapper and final-answer acceptance require the 73% denominator to remain total 2024 application value; Singapore as leading source by value with 357.5 billion baht / 43% of FDI applications; correctly attributed Singapore 305 and China 810 project counts, with China having more; no false conflict or regional-base substitution; and application figures distinguished from completed investment. Parsing, literal validation, source support, completeness and owner acceptance are separate results.

The exact local contract is `reports/workflow_pilot/production-readiness-2026-10-27/resume-v12/diagnostic-proposal-v152/contract.json`, SHA-256 `4b3c9f8f800c27e60c5209b9c841e1ac138cf0008dc500a4641e31436b061368`. Current schema/messages/native request, code, corpus and source snapshots are pinned. Default inspection performs no inference. Execution requires a direct human grant tied to this contract and fresh verification of offline results/integrity.

No owner scoring is requested for the failed mapping. Any new assessable draft needs owner source/completeness/usefulness review before being called accepted, followed by exact-revision approval before export. Independent reviewer usage and production rollout acceptance remain separate later requirements.
