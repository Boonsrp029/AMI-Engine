# Source-rendered project-count comparisons — v1.55

**Implemented and verified offline; subsequently one [actual r06 diagnostic](diagnostic-v155-findings-2026-10-30.md) passed combined-draft assistant source checks and final NeMo. Owner review and general quality qualification remain pending.** This is an explicit change in composition responsibility, not a parity-only refactor. The [actual v1.54 failure](composer-v154-findings-2026-10-30.md) is preserved: valid JSON omitted count operands and said the wrong entity had more projects. No failed model claim is silently corrected by this change.

## Behavior and engineering decision

Before: even a validated mapping's simple count comparison was sent to the composer beside value-ranking language. After: the application identifies a narrow literal operation before composition, renders both selected counts and their more/fewer/equal relationship, and excludes that operation's fully owned canonical unit and requests from model input and schema. A model attempting to supply an excluded unit is rejected, even if its wording happens to be correct.

Mixed briefs keep their remaining units in original order and the same four-main-call ceiling. If every unit is application-owned, the composer is not called. The existing final citation, scope, measure/number, NeMo, exact-revision review and approval/export checks still apply to the combined draft. Diagnostic events attribute the rendered claim and source operands to application code, not the model. Lower-level helpers retain their existing behavior when source-rendering mode is not requested.

The recognized grammar is an explicit binary project-count question: “Did/does/do A or B have more/fewer/less projects?”, optionally with a year. A trailing “Keep the percentage denominators clear” style note is allowed; additional requested explanations or measures are not dropped. Arbitrary comparison language, currencies, percentages, tables and entity aliases are not newly interpreted by this operation.

Necessary checks include exact whitespace-normalized quotations, known retrieved source IDs, shared pinned corpus/document identity, one integer count per entity, no instruction-like selected content and no contradictory mapper count/winner. Differing explicit periods fail; one dated quotation does not supply another's missing period. A requested year without matching quoted period does not enter this path. Partial/conflicting states, scenario/forecast wording, measure qualifiers and mixed canonical responsibilities stay on the existing validated path. No source truth or general semantic entailment is inferred from those mechanical checks.

**Scope limitation:** undated operands in the same pinned document may be compared as selected counts, but this does not prove temporal or geographic applicability. No date/location is taken from publication date or the question. Existing unresolved-scope warnings remain; human source review is still required before acceptance. Shared document identity is not a semantic guarantee.

Prompt/behavior version is `analyst-pilot-v1.55`; mapper v37, local model/options, retrieval, graph nodes, public `Draft`/APIs, SQLite schema, legacy graph and dependency versions are unchanged. Narrow literal arithmetic moves out of free-form composition; no framework or provider migration is involved.

## Offline evidence

| Check | Result |
|---|---|
| Targeted contracts, including capture and graph integration | **167 passed** |
| Full Windows suite | **1,017 passed**, 15 existing warnings |
| Full Linux suite, networking disabled | **1,016 passed**, one Windows-only skip, 15 existing warnings |
| Dependencies | Windows and image checks clean; all **221 installed image distributions** match the baseline versions |
| Consumed r06 inspection | Model input/schema contains only `u1/u2`; `u3` is rendered from 305/810 with an explicit China-more conclusion; zero new model calls |
| Original bad v1.54 raw response | Unchanged and still rejected, not promoted to a successful output |
| Offline validator rehearsal | Explicitly synthetic source-excerpt fixture, three seconds within the 30-second phase; zero model/NeMo calls, not quality evidence or authorization |
| Container recovery | Non-root startup/redaction/restart/restoration passed; four cached approved exports byte-identical; no new decision/export |

The initial targeted fixture wrongly assumed separate quotation groups canonicalized into one shared unit; a single shared-span fixture corrected that setup. The first full Windows run then had seven failures in count-only composer-capture fixtures, which correctly no longer reached the composer. Those tests now use mixed inputs to preserve invalid composer checks, plus a separate count-only skip test. All failed logs remain retained; no tests were deleted. Forty-two synthetic cases were added relative to the 975-test Windows baseline. Fixed responses and source operations do not establish actual model quality.

Local image: `ami-pilot:literal-v155`, ID `sha256:a991e3fe9ed993dc2a720c42f845417e132e361459b4a9e7dcd0062a107cee93`; sanitized build-context SHA256 `deb8b83661513e3bf7930f5b26f1803de60de27c5c5c343e6b29554f5955e07d`. The unchanged full Dockerfile reused dependency layers; this is not a fresh install, exact committed release, actual container inference or external deployment. Raw snapshots, tests, replay, installed-version comparison, image and recovery evidence are under ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v28/`.

## Next gate and human review

A [new frozen diagnostic proposal](composer-diagnostic-v155-2026-10-30.md) tests one actual composer response and only conditionally one full r06 workflow. It is not authorized by the closed v1.54 allowance. No model, NeMo, Ragas, hosted inference, fresh twenty-case run, commit, push, deployment or reviewer contact occurred in this offline pass.

No manual scoring is required for the engineering tests or the preserved technical failure. New assessable generated answers require owner review of factual support, completeness, warnings and the distinction between model-written and application-rendered claims. Approval still applies to an exact stored revision before export. Independent reviewer usage and all remaining production gates remain pending.
