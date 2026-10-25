# Explicit geography contract — 2026-10-25

**The requested mapper-contract repair is implemented and verified offline.** Geography can no longer disappear through an omitted field default. A declared unresolved location remains distinct from a malformed response, and useful partial answers are preserved. Actual local-model compliance and end-to-end answer quality are still unverified.

## Required response and provenance

Mapping version is `requested-evidence-v5`; workflow version is `analyst-pilot-v1.8`. The private mapper must provide a geography object, with every field explicit:

```json
{"status":"known","value":"Cobalt Cove","evidence":["selected-span-id"],"reason":""}
```

or:

```json
{"status":"unresolved","value":"","evidence":[],"reason":"The passage does not establish geographic scope."}
```

These are illustrative shapes, not generation results. Known state requires a name and real selected-span references; unresolved state requires empty value/evidence and a nonblank reason. Missing fields, null/legacy strings, contradictory states, fabricated/duplicate IDs and invalid provenance fail explicitly. There is no inference, field filling or retry to turn malformed data into a valid unknown state.

Known location text must occur as a whole phrase in the assigned span. When supported answer components exist, its evidence must also be selected for a supported component. Original source identity, span ID, content hash, character offsets and exact quotation are retained in `geography_resolution`, which flows into resolved mapping and scope events. Qualification applies only to components linked to the explicit geographic evidence; scope citations remain with the claim.

Explicit unresolved geography preserves supported/partial facts and adds:

> Geographic scope is unresolved for this draft; verify the cited sources before approval.

The diagnostic reason remains in audit data rather than being echoed as arbitrary source instructions. Missing answers still use the existing no-information message; unknown geography alone does not cause abstention. The application never guesses a location from capitalization or possessive phrases. A model's unresolved declaration is not proof of database-wide absence, and literal place-text matching does not prove semantic classification or claim support. Those remain source-review questions.

## Verification

- **244 tests passed, three existing warnings**, against the 204-test baseline; 40 new regressions. Full run: 17.98 seconds.
- Targeted suite: **176 passed, two warnings**, 48.42 seconds.
- Checks cover required schema fields, omission versus explicit unknown state, exact selected-span provenance, source/name boundaries, invalid references, truly unlocated and ambiguous named passages, preserved partial facts, the four-call ceiling, final guardrail rejection, and human approval before export.
- Applying the new schema to the unchanged archived failed response produces exactly `geography: missing`. The archived response and gate remain unchanged.
- Fixed synthetic known and unresolved examples exercise resolution and fallback output. They are not actual model or human acceptance evidence. No generation was run after or before these checks in this pass.

```powershell
.\.venv-pilot-clean\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp/geography-contract-full
```

The [structured record](evidence/geography-contract-2026-10-25.json), [emitted schema](../../reports/workflow_pilot/geography-contract-2026-10-25/mapper-schema.json) and [offline examples](../../reports/workflow_pilot/geography-contract-2026-10-25/offline-contract-evidence.json) retain the evidence. The warnings remain Unity Catalog/Pydantic, Starlette/httpx and MLflow predict type hints. [Integrity verification](../../reports/workflow_pilot/geography-contract-2026-10-25/verification.json) records baseline hashes and preserved boundaries.

The public Draft/API, SQLite schema, library versions, local model/settings, retrieval, tool limit, guardrail boundary, citation checks and approval/export controls remain unchanged. Older fixture responses were updated explicitly for the new private contract; no production compatibility path silently supplies missing mapper fields. Saved approved exports and original evaluation evidence remain untouched.

## Manual review and next boundary

**No new human judgment is required now:** this pass contains offline fixtures and no new actual analyst drafts. Leave the historical `human_review.csv` unchanged.

When future revised workflows produce actual assessable drafts, stop for the owner's source review: claim support, geography versus incidental/organizational names, causal completeness (especially d03), period/measure/scenario, partial answers and gap usefulness. An unresolved-geography warning particularly requires checking before approval. Approve the exact revision before export. Independent usefulness still requires external reviewer task sessions.

The [review checkpoints](../../reports/workflow_pilot/geography-contract-2026-10-25/review-checkpoints.md) and [handoff](../../reports/workflow_pilot/geography-contract-2026-10-25/handoff.md) identify those boundaries. Any future model validation must use a new bounded experiment and frozen fixtures; old stopped runs must not be replayed or relabeled. No commits, pushes, hosted inference, Ragas, deployment or reviewer contact occurred.

The contract repair is complete; the broader analyst workflow remains unqualified pending actual local validation and human acceptance.
