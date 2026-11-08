# Proposed gap contract after the failed position-selection attempt

Status: **design proposal only; no runtime or frozen-gate change adopted**.

## Current behavior and ownership

`src/pilot/_requests.py` intentionally retains this imperative compound question
as one canonical component. The concurrent private mapper marks it partial and
selects an unanswered question range. `_question_spans.py` proves its membership;
`_coverage.py` checks required branches. `generation.py` resolves the selection,
and the existing evidence layer builds gap messages. The actual selected range
`and` demonstrates that structural validity does not establish a useful gap.

The current application already retains per-branch outcomes, queries, selected
source IDs and missing required branches. Source facts and gap semantics are
different obligations. Do not weaken exact evidence validation or add another
model/repair call to hide this distinction.

C owns the proposed private gap projection and composition diagnostics. A owns any
new plan field or runner integration. B's ranking and result envelopes need no
change for a branch-disclosure prototype. Shared runtime edits would need explicit
integration ownership; no additional workers are launched by this proposal.

## Options

| Option | Benefit | Remaining failure or contract change |
|---|---|---|
| Add lexical rejection for conjunction-only ranges | Rejects this pattern offline | Does not identify the missing request; synonym/irrelevant content still passes. Insufficient as the next complete fix. |
| Keep range selection and tune instructions/examples | Preserves the wire | Real-model benefit remains unproven; not justified by another identical budget request alone. |
| **Application-owned branch disclosures, with explicit requested-scope provenance** | Removes model transcription/offset selection from the final gap message and reports observable execution facts | Changes the earlier model-selected-gap contract. Precise subpart labels may require A-owned plan annotations; no default parser change implied. Needs explicit review. |

Recommend the third option for offline prototyping, **not** relabeling the present
failure as a pass. Keep all old contracts/results and the existing acceptance
criteria. A future protocol must declare the new contract and demonstrate useful,
specific gap language against the original task rather than make the gate easier.

## Proposed behavior

1. Retain source-span selection, component/branch bindings and supported partial
   facts. No factual answer is supplied by the application for absent evidence.
2. Derive disclosures from actual required-branch outcomes and selection coverage.
   Record the exact original question, branch query/identity, outcome and source
   selection state. Escape displayed query text as data.
3. Say **no evidence returned for this retrieval subtask**, not that the entire
   database or full source lacks the requested fact. Failed/cancelled branches
   mean unverified coverage, not absence. Conflicting evidence remains conflict.
4. A branch with returned but unselected sources is **unselected/unresolved**,
   not missing. Optional branches must not become mandatory gaps automatically.
5. Include the full original request to preserve dates, geography and measures.
   A query is labeled a retrieval query, not silently promoted into an exact
   interpretation of what the user requested.
6. Where precise task subparts are needed, accept explicit plan-bound verbatim
   question spans and shared scope annotations. Validate their offsets and IDs.
   Missing or ambiguous annotations produce an honest unresolved-scope disclosure;
   they cannot be guessed from corpus content or a new conjunction regex.
7. Keep raw selections, application disclosures, composition fallback and editorial
   changes distinguishable. Strict final safety and exact-revision review remain.

## Different-fact examples for an offline prototype

These are design illustrations, **not generated outputs or adopted wording**.

| Scenario | Supported result / proposed disclosure |
|---|---|
| Chile solar share in 2012 available; today's gas tariff retrieval empty | Preserve the exact solar fact. Identify the tariff subtask/query and say it returned no evidence; display the original request for country/measure/date context. Do not call the historical solar fact a gap. |
| Norway wage level retrieved; quarterly-change branch timed out | Retain the level. Say quarterly-change coverage is unverified because the branch timed out; do not classify it as unavailable in the source. |
| Kenya price query returned documents, but none selected | Label returned evidence unselected/unresolved and expose source inspection; do not claim retrieval was empty. |
| Mandatory Brazil forecast branch contains conflicting values | Preserve the separate scenario/period/value units and label the conflict. Do not replace it with a generic no-information message. |
| Optional background branch fails | Keep a diagnostic entry without inventing a required answer omission. |

## Reviewable passes and checks, if the design is accepted

1. Specify the private disclosure contract and explicit A/C field ownership before
   implementation. Preserve sequential APIs, dependencies and model/settings.
2. Prototype deterministic projection over fixed report envelopes with the different
   facts above. Check missing, unselected, failed/cancelled, conflict and optional
   branch distinctions; no inference or source-text instruction can authorize action.
3. Integrate through C only if A's existing contract suffices. Propose any needed
   requested-scope field separately to A. Do not edit A-owned files concurrently.
4. Verify supported partial claims, whole-question scope, provenance, final safety,
   exact-revision approvals and cached exports. Maintain historical wire replay.
5. Freeze a new bounded diagnostic only after offline evidence is reviewable. A new
   generation grant is required. Any actual failure remains retained and stops it.

The human decision is whether to replace model-selected final gap text with this
application-owned disclosure contract. No numerical rescoring or repeated manual
review of `and` is needed. This decision grants neither inference nor deployment.
