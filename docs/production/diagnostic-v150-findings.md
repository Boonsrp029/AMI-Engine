# Reduced v1.50 diagnostic — 28 October 2026

**Owner update, 29 October:** [r05 review completed](../pilot/owner-review-v150-2026-10-29.md): request changes to claim 1, approve claim 2, and waive warnings for the separate editorial candidate. The dated findings below preserve the original pre-adjudication assessment.

**FAILED at r06; budget closed.** The owner authorized one mapper check, then conditionally r05/r06 once each. The mapper and full r05 workflow passed technical and assistant source checks. r06 completed technically and passed NeMo but omitted its requested country/project-count comparison. This consumed development batch does not establish fresh held-out quality, owner acceptance or production readiness.

| Attempt | Result | Evidence boundary |
|---|---|---|
| r05 mapper | Passed actual engine validation and source/completeness checks | All four requested quantities/tasks selected the correct spans; one actual mapper call with fixed tool turns, no composer/NeMo. |
| r05 workflow | Passed technical and assistant source checks | Source-provided USD33billion value, 35% growth,3,137 projects,40% growth and2,235 base retained in two cited claims. New owner acceptance remains pending. |
| r06 workflow | Failed source/completeness check despite exit0 and NeMo YES | FDI share/leading value retained, but no China 810 versus Singapore 305 project-count comparison. |

## r05: new assessable output

The mapper now classifies value, count and their changes separately with correct evidence. The final draft uses the source's approximate USD33billion equivalent rather than THB1.14trillion, which the protocol explicitly permits. BOI PDF page 1 supports the value, 35% growth,10-year high and data-center/cloud explanation; PDF page 2 supports3,137 projects,40% growth and2,235 projects in 2023. No contact details or FDI-subgroup quantities substitute for the requested totals. No extractive fallback was used.

The first claim would be clearer if it explicitly said **application value** and **compared with 2023**. Its monetary level identifies the value measure, while the second claim explicitly distinguishes project count and its2023base. These wording questions remain for owner review rather than being silently edited. Automated geography remains unresolved even though Thailand appears in the cited source and generated claims; the warning is retained. This source-assessed pass is not an owner approval.

## r06: why it failed

The request asks for FDI's share of all application value, the leading source by value, and whether Singapore or China had more projects. The first two claims retain 73% of all application value and Singapore's 357.5 billion baht/43% of FDI. The third instead discusses Chinese/American companies using Singapore as a base. That statement is traceable to its citation but does not answer the count comparison.

Both count passages were retrieved on stored PDF index 1 / PDF page 2. Span `s_a403e15f7eb38d5f` contains Singapore's 305 projects; `s_235e6b4a789691ac` contains China's 810 projects. The mapper's third short answer says China but selects `s_9245499730777b2d`, the regional-base background sentence. Qualitative answers contain no numbers, so the necessary numeric-alignment check cannot detect this mismatch. Composition renders that selected background instead of the requested comparison. NeMo accepts the grounded text, demonstrating again that grounding alone does not establish responsiveness/completeness.

This is an evidence-selection and comparison-coverage failure, not retrieval absence, malformed JSON, observed context truncation or established GPU/model incapacity. Next engineering work should explicitly require both entity/count evidence roles for a requested same-measure comparison, preserve partial/missing/conflicting states, and reject an unsupported qualitative winner before composition. Do not silently reassign source IDs, infer a comparison from nationality/background wording or add a repair loop.

## Budget and provenance

Actual use: **nine main calls plus two NeMo invocations**;12,298 known input /1,100output tokens. Internal NeMo usage and monetary cost remain unknown. Mapper elapsed26.33 seconds; workflow elapsed41.46/42.22 seconds. These are individual development executions, not warm p95 or sustained-load measurements. No retries, Ragas, hosted inference, twenty-case run, approval/export, commit/push, deployment or reviewer contact occurred.

Prompt `analyst-pilot-v1.50`, mapper `requested-evidence-v35`, model `ami-llama3.1:8b-4k`, digest `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`; generator `c46162eb97a6839d1ba13de703ef49d8a84ebd3a833aa5a20e8b8465c337810e`. Identities verified before/after; code/settings/dependencies remained unchanged during the batch. Offline evidence remains783 Windows / 782 Linux plus one Windows-only skip / 15 existing warnings.

Ignored evidence is in `reports/workflow_pilot/production-readiness-2026-10-27/resume-v9/`: authorization/contract, mapper input/raw/parsed result/process/gate, workflow traces/results/gates and `development-v150/summary.json`. Attempt hashes:

- Mapper: `8ee0d04575ffcc4bc3b86b85976939458382227b82b67274297fa31c99caa3b2`
- r05: `5f228b432d222050409fc06ccaf6f6410e13df2af51e5fe6b1ac04af0ef9eafe`
- r06: `8df9b902be691d298d7ebec7a52d2412e84f7d9548986fd07696a027e4d87aa2`

## Human review and remaining work

`resume-v9/owner-review-v150/review-packet.md` contains only new assessable r05, unchanged, with cited passages and the wording questions. Owner source/completeness acceptance is pending; export still requires approval of the exact saved revision. No numerical human ratings or SQLite decisions were created. r06's technical/source failure is an engineering task, not a request for repeated manual scoring. Existing r03/r04 adjudication/country-edit candidates and original four approved exports remain separate and unchanged.

The full Goal remains incomplete: comparison coverage must improve before fresh quality qualification, and independent reviewer use, current remote CI, real container inference/cancellation, scoped production security/operations/soak and authorized Databricks deployment/rollback remain open. The proposed operating-report work received inspection only; no code was changed before this newly authorized diagnostic took priority.
