# Qualification pool provenance and coverage — 30 October 2026

**Preparation only: no generation, tuning or benchmark-data changes.** The current v1.55 r06 source/wording review remains pending. This audit establishes the next qualification prerequisites rather than treating one successful consumed case as release qualification.

## Coverage finding before execution

All v2/v3 case/source hashes verify, and both pools retain the agreed 20-case category composition: ten answerable, two partial, four missing, two conflict and two adversarial. The answerable source mix nevertheless changed:

| Publisher/document family | v2 answerable cases | v3 answerable cases |
|---|---:|---:|
| BOT economic and monetary-policy releases | 5 | 3 |
| BOI investment applications | 2 | 0 |
| IEA electricity report | 3 | 7 |
| Total | 10 | 10 |

The four consumed v2 cases r03–r06 were replaced with r23–r26, all from IEA. Seven of ten answerable cases now concern one source family. This table concerns answerable cases only; partial/safety categories retain their own evidence and must not be described as having no BOI content without inspecting that category.

The v3 pool remains useful prepared evidence, but it cannot silently establish the original breadth of the Thailand/ASEAN market-intelligence workflow. Its same category counts do not make the changed topic mix equivalent. No result has been discarded on performance: zero completed attempt records tied to the v3 package were found in the retained qualification report area.

The public v3 specification also inherits a historical v1-to-v2 continuation block listing r03–r06 among retained IDs. The actual v3 case roster excludes them and contains r23–r26. Interpret that block as history, not the live roster. The [structured companion addendum](evidence/qualification-pool-v3-provenance-2026-10-30.json) records authoritative IDs, hashes and source counts without rewriting any frozen file.

## Balanced successor before broad qualification

Prepare a separately versioned successor retaining the 16 unattempted v3 cases inherited from v2, and replace the four additional IEA cases with **two new BOT and two new BOI facts**. Proposed new IDs r27–r30 restore the earlier answerable mix: five BOT, two BOI, three IEA. These proposed cases do not yet exist. Keep v3's unused additions and all prior artifacts unchanged; do not choose replacements by known model success/failure.

Use new fact/questions, source locators, explicit reference/check provenance and a new manifest. Freeze inputs before generation and avoid subsequent tuning against their outputs. Retain the agreed quality gates:9/10 complete supported answerable cases,2/2 partial,4/4 abstentions,2/2 explicit conflicts,2/2 safe injection outcomes,zero critical unsupported/wrong-scope/date/unit/scenario claims. Do not convert unknown/technical failures into credited abstentions.

Source/case preparation is not independent blindness. The audit did not print reference/check fields or new generated answers, but a public-spec metadata extraction also displayed existing synthetic source text. Runtime identity was already frozen beforehand and remains unchanged; that text was not used to tune it. Reference authors know source families, and the pool is neither statistically independent nor proof of absence from pretraining. Preserve those limits in any later report.

## Remaining consumed regression gate

A concrete, unexecuted proposal selects **r03, r04 and r05** from the unchanged frozen v2 package, under the current v1.55 code/model identity. They are consumed development cases despite their original frozen split label. No repeated r06 attempt is included.

Proposed ceiling: **12 main calls +3 NeMo invocations**, one attempt/case,180seconds each,stop at the first technical/source/completeness failure. No retries,Ragas,hosted inference,twenty-case run,approval/export,publication/deployment or reviewer contact. A separate direct budget grant is required after the current review checkpoint; none exists now. The full JSON proposal and SHA256 are beside the local audit under ignored reports/workflow_pilot/production-readiness-2026-10-27/resume-v30/.

Reuse the existing per-case src.pilot.qualify.run_attempt API and hash-bound identities, inspecting each result before the next case. Do not run a broad heldout stage under a three-case grant: the existing stage CLI loops its entire split and stops on technical failure, not after each source-quality judgment. No new runner/framework/API was added for this preparation.

Bind later p01/p02 preflights to the **exact final successor package**, because preflight verification checks both generator and package identity. Successful v2 preflights cannot substitute for v3/v4 evidence. This avoids spending calls on a preflight whose package will immediately be superseded.

## Human and execution boundaries

The existing [r06 actual-result review](diagnostic-v155-findings-2026-10-30.md) remains the only requested source/wording judgment. Do not infer it from Goal continuation, an old editorial acceptance or a preselected answer. No additional rating is requested by this metadata audit.

This preparation does not authorize regression, preflight or heldout generation. The prior v1.55 allowance remains closed. It makes no portfolio-complete, production-ready or broader quality claim; independent usage and operational/Databricks gates remain open.
