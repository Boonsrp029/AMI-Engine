# Decoder-coverage development diagnostic — new grant required

Prepared only; **no execution grant exists**. The v5 attempt failed and its once-only allowance is closed. This packet does not reopen it or authorize a twenty-case run.

Contract: [development-contract-v6.json](development-contract-v6.json)

SHA-256: `008983029a7b3d7b1523b680fe80b1c909d484821bb2b8904228ef0091bf85c8`

The contract pins 112 input/source/configuration identities and a new output directory, `actual-development-v5/`. Mapping version is `cq-mapper-v5-decoder-coverage`. This is the **v6 execution contract**, distinct from the mapper-version label.

## Scope and limits

Run cq-p01 once. Only if its technical, source-support, completeness, safety and publication checks all pass, run cq-p02 once. Inspect each exact result before advancing. Stop and close at the first declared failure. No retries, warmups, repairs, prompt tuning or substitutions inside the batch.

- New ceiling: eight local main-model calls plus two NeMo invocations total, at most four plus one per case.
- Deadline: 180 seconds per case including preparation.
- Main inference remains serialized. Retrieval cap remains two.
- Same pinned model, digest, context 4096, completion 900, temperature zero, timeout and source facts.
- Across closed batches: five observed main-request starts and one NeMo invocation. Including this proposed allowance, the cumulative ceiling is thirteen main starts and three NeMo invocations. One interrupted request has unknown backend token use; NeMo internals and monetary/hardware cost remain unmeasured.
- No CQ1 run, Ragas, hosted inference, Databricks operations, approval/export, publication, deployment or reviewer contact.

## Explicit design and risk

The supported-state schema requires a selectable provenance-cover prefix; partial/missing/conflicting alternatives remain. It does not preselect a fact, prove semantic relevance, or force irrelevant citations. Shared/overlapping origins avoid duplicate mandatory citations. The application coverage guard, strict validators, final NeMo and exact-revision controls remain.

Twenty-case offline accounting remains 3,429–3,572 message/framing/completion tokens. Grammar format grows to 6,939–17,322 tokens; it is separate from message content. Actual grammar processing cost and real-backend compatibility are unverified and remain subject to the same deadline—no hidden extension or retry.

Both fixtures are development diagnostics. cq-p01 is consumed and inspected after failure; it cannot become an unseen benchmark success. cq-p02 is unattempted. The old r07 failure and nineteen reserved cases remain untouched; CQ1 is still unattempted and narrowly electricity-domain.

## Evidence and human action

- 34 targeted offline checks pass. The integrated suite passed **1,570 tests, 14 warnings, 451.25 seconds**, terminal exit zero, recorded in `decoder-coverage-full.txt`. All 112 frozen contract identities were rechecked afterward; `git diff --check` passed.
- `decoder-preservation-audit.json` verifies the source baseline, manifests, r07, unchanged dependencies and rejection of the unchanged saved incomplete response.
- `decoder-coverage-contract.md` explains the private wire-order change, provenance limits and unresolved actual publication boundary.

Technical failures need no repeated human rating. New assessable drafts need owner source/wording review before they can be called owner-accepted. This would not approve/export a stored revision. Independent reviewer usefulness and production qualification remain separate unmet gates.

The root AGENTS.md and the frozen stop/no-retry protocol require a new explicit grant after the previous failure. Authorizing this packet would grant only these two development attempts and their stated budget.
