# Explicit C request/branch coverage proposal

Observed defect: cq-p01's single supported mapper component selected only Canada's observation although the request compares it with Japan's projection. Both branches completed; source identity/binding validity and NeMo passage did not establish requested completeness.

## Proposed private contract

Add opt-in C complete_required_branches per canonical component, declared by the experiment planner before generation, independently of Plan.required (which remains an execution policy). Do not infer that arbitrary retrieved text supports the answer. Require IDs to exist in the component binding and frozen plan. The cq-p01 comparison declares both read-only branches as requested coverage, without preselecting any source or factual value.

For a component labelled supported, every explicitly required coverage branch must have selected support-source provenance; missing/failed/unselected coverage rejects before composition. A selected record shared between branches retains both origins and may satisfy structural coverage; it is not two independent confirmations. This is a necessary structural gate only.

Partial/missing/conflicting mappings preserve existing semantics and exact requested-information gaps. Never force citations to irrelevant evidence or infer that unselected text contains no answer. Supported partial facts remain draftable; diagnostics name unselected/unresolved required branches. Final source/completeness review still checks whether a claimed gap is real. No automatic repair or factual answer injection.

Legacy callbacks default to current behavior until the explicit private contract is supplied. Public Draft, Plan/Result, serving APIs, sequential workflow and approval/export are unchanged. New frozen experimental contracts must include coverage declarations; altered schema/prompt budgets must be recounted before any new actual grant.

## Offline acceptance before any generation

Use different fictional countries, dates and quantities. Reject supported comparison with only one required branch; accept structurally full selection while retaining unit provenance; retain explicit partial/gap output; reject unknown requirement/binding IDs; handle duplicates/conflicts safely; keep raw/composer/fallback/editorial separate. Test that irrelevant required-branch output causes a partial or rejection, never fabricated citation support.

This proposal is separate from publication telemetry. Neither a coverage guard nor an event-loop alignment proves actual repaired-model quality. No inference is included.
