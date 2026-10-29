# v1.47 development diagnostic — 28 October 2026

Assistant-authored source assessment; owner adjudication pending. **The batch failed and stopped at r05.** r03/r04 passed declared source checks with explicit scope/readability limits; r06 did not run. The owner authorized four consumed cases, once each, with at most 16 workflow calls/four NeMo invocations and 180 seconds per case. Actual consumption: **11 workflow calls, two NeMo invocations, 12,118 known input tokens and 1,169 output tokens**. Aggregate execution time was 114.65 seconds across three attempts, not a latency benchmark. Internal NeMo tokens and monetary cost remain unknown.

| Case | Actual unchanged outcome | Gate |
|---|---|---|
| r03, monthly inflation | Two December 2024 claims retain energy inflation, subsidy base effects and benzene prices; core stability retains prepared-food/cooking-ingredient increases offset by cleaning-equipment promotions. | Declared source checks passed. Geography remains unresolved, and verbatim fallback needs usefulness review. |
| r04, monthly/quarterly investment | Monthly stability, machinery/equipment and vehicle increases, and construction decline/cause are retained. Quarterly vehicle/construction decline has its own Fourth Quarter of 2024 label. No unrelated tourism/export claims. | Declared source checks passed. Geography remains unresolved and the monthly excerpt is lengthy. This consumed-case result is not an unseen benchmark. |
| r05, annual investment applications | Mapping parsed, then failed duplicate-quotation validation. No composer or final NeMo call, and no draft. | **Technical failure; stop.** No human scoring is needed. |
| r06 | Not attempted. | Unused ceiling is closed after failure. |

## Confirmed cause and additional risks

The r05 decoder schema allowed repeated optional span identifiers. Each component selected `s_7d62ae0f3056eb38` four times. `validate_mapping()` correctly rejected this with `Evidence mapping repeats a supporting quotation`. A frozen replay recreates the same schema, parses the saved response and reproduces that exact semantic failure with zero inference. This is a contract mismatch; no evidence was deduplicated or repaired silently.

The mapper also chose December 2024 for an annual 2024-versus-2023 question. The offered monthly label came from a January–December range. Its first short answer listed unrelated FDI values. These are retained mapping/scope risks, not observed final unsupported claims, because drafting never ran. The earlier tool-stage response had already stated the requested value/count/growth facts; retrieval availability alone did not produce a valid final workflow result.

All three processes matched pinned generator/source/model identities. r03/r04 exited cleanly and passed final NeMo. r05 exited with a normal application validation failure after a model `stop` response. No retained OOM, context-limit finish or malformed JSON establishes a GPU-capacity problem or an inherent open-source-model limitation. Upgrading a model or using hosted inference is not justified by this evidence alone.

Next engineering checks: declare/enforce unique selection consistently, retain duplicate rejection rather than silently removing IDs, prevent a reporting-range endpoint from becoming an annual answer's monthly scope, and test relevance independently. Freeze synthetic fixtures and use offline checks before any new generation authorization. Do not reuse the stopped grant or start the twenty-case set.

## Evidence, correction and human review

Ignored evidence: `reports/workflow_pilot/production-readiness-2026-10-27/resume-v5/development-v147/`. The raw/parsed responses, source catalogs, process outcomes, usage and per-case source gates are retained. The zero-inference reproduction is `resume-v5/r05-contract-replay.json`. Generator identity: `b7b03d976add8aa006d38e7d76145c078c282db64c718847ea93a8afc879a28e`. Model digest: `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`.

The initial assistant inspection of r03 used Windows' default text decoding and displayed incorrect punctuation. Explicit UTF-8 inspection confirms the saved v1.47 draft has correct punctuation and no replacement characters. Its source gate records the previous finding/hash and correction. This correction changes neither the draft nor historical assessments.

Only r03/r04 enter `resume-v5/owner-review-v147/review-packet.md`, with unchanged outputs and source passages. Human review must establish support, completeness, scope applicability and usefulness before owner acceptance. This is evaluation adjudication, not a stored workflow approval. Any export needs approval of its exact saved revision. No human ratings, approval, export or external-use evidence was created. The prior v1.46 review packet remains historical and unchanged; review of these newer outputs need not duplicate scoring of technical failures.

The offline v1.47 result remains **707 Windows tests and 706 Linux tests plus one Windows-only skip**, with 15 warnings, clean unchanged dependency checks and successful no-inference recovery/export preservation. These engineering checks do not override the failed actual diagnostic. Portfolio completion and production qualification remain unmet.

## Subsequent owner adjudication — 28 October 2026

The owner confirmed source support, completeness and usefulness for r03/r04, with **request changes (minor)** to add explicit Thailand scope. The [separate adjudication record](../pilot/owner-review-v147-2026-10-28.md) preserves the wording and prepares editorial country-clarified candidates. Those candidates are not fresh generation or approved/exported revisions. Original outputs, source gates and pending status fields remain frozen as historical evidence; the new record supplies the current human judgment. r05 remains a failed technical diagnostic and r06 remains unattempted.
