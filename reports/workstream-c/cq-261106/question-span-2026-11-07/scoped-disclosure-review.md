# Scoped branch disclosures — offline design review

**Not activated. No new inference. No existing failed result regraded.**

The standalone [prototype](branch_disclosure_prototype.py) passes **10 offline
checks**. It uses different synthetic countries, dates and measures from cq-p02.
Its [example output](branch-disclosure-prototype-scoped.json) preserves supported
partial claims, the full original question and a predeclared requested subpart.
See [test output](branch-disclosure-scoped-tests.txt).

## Proposed contract change

Replace model-selected final gap wording with application-owned disclosures of
observable branch outcomes, linked to **explicit, predeclared question-scope
annotations**. The model still selects relevant source evidence; existing exact
source, relationship, composition and safety checks remain mandatory.

For the synthetic example, the exact requested subpart is `Chile retail gas
tariffs today`. Its branch returned no supporting evidence. The disclosure says
that, retains the original question and solar claim, and explicitly avoids
claiming the entire database has no answer. This is application output, not an
improved model answer or source-derived interpretation of the user's intent.

| Branch condition | Proposed treatment |
|---|---|
| Required retrieval returned no support | Name its declared question scope and query; state that this retrieval returned no support |
| Failed, cancelled or blocked | Coverage unverified because execution did not complete; never infer information absence |
| Sources returned but not selected | Evidence unselected/unresolved; expose source inspection |
| Reported conflict | Preserve separate evidence statements and label the reported conflict |
| Optional branch failed | Diagnostic only; do not invent a mandatory omission |
| No precise requested-scope annotation | Explicitly unresolved scope; do not guess a fragment from a query or a conjunction splitter |

Annotations retain exact full-question offsets and shared country/date/measure
context. Membership validation still does **not** prove the annotation is the
correct interpretation: the planner/caller must provide it, its provenance must
be recorded, and a reviewed diagnostic must establish its adequacy. A query label
is not automatically an exact requested subpart.

## Why branch-only output is insufficient

This prototype does not detect omitted facts inside a returned source passage,
prove semantic evidence support, create trusted request annotations automatically,
or establish full answer quality. Without adequate annotations, it must not claim
that the missing price request was precisely identified. That ambiguity remains
a failed/unresolved quality gate. The existing cq-p02 `and` result stays failed.

## File ownership and implementation, if accepted

1. C implements a private deterministic disclosure projection and fixed-response
   tests against A's real typed report/result envelopes. The prototype dictionaries
   are illustrations, not a second runtime schema.
2. C prepares an exact sidecar annotation interface: component/branch IDs, question
   offsets, scope provenance, and question/corpus/plan identity. No model-generated
   gap is silently promoted to a trusted annotation.
3. A remains the integration owner for accepting/persisting those annotations in
   the opt-in plan/runner path. Prepare an A handoff; do not edit A-owned runtime
   files concurrently or change public Plan/API shapes without separate review.
4. Preserve the default sequential workflow, public Draft, approval/export, model
   settings and dependencies. Keep raw mapper output, application disclosures,
   source fallback and editorial corrections separate.
5. Test real-envelope identity checks, missing/failed/conflicting/optional branches,
   source isolation, scope preservation, warning capacity and safety/review lifecycle.
   A prototype or green tests do not establish model improvement.
6. Freeze a new diagnostic only after offline integration passes. Keep the original
   acceptance criteria; obtain a separate generation grant. No inference is included
   in the design decision.

**Decision requested:** adopt this scoped, application-owned disclosure contract
for offline C implementation and an A integration handoff, or retain the current
model-selected-gap contract. This is a change to the earlier gap-selection
requirement, not a dependency/framework migration. No agent delegation, model
calls, workflow batch, CQ1, approval/export or deployment is authorized by it.
