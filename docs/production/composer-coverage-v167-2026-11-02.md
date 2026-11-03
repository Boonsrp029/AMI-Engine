# Composer literal coverage repair — 2 November 2026

This focused side-conversation change follows the owner's request to address raw
composition omissions before authorizing qualification. It runs no inference and
does not resume or complete the paused Goal. Historical v1.66 evidence, owner
judgments and the unexecuted v1.66 qualification proposal remain unchanged.

## Confirmed issue and bounded change

The actual r05 v1.66 composer saw the selected application-value passages but
omitted the current baht amount and prior-year baseline. The existing application
coverage validator detected these omissions and used a logged source fallback.
Final-draft acceptance therefore did not establish raw-composer completeness.

The new v1.67 composition input adds `required_literal_coverage` to eligible
evidence units. It reuses the same narrow financial comparison coverage logic
already used after synthesis, supplying selected quantity/unit pairs, percentages
and explicitly quoted requested years before synthesis. This applies to the
recognized application-value/count and each-change request grammar, not arbitrary
financial questions. Each canonical unit retains its own checklist; aliases do
not duplicate evidence. Monetary quantities use the existing parser's base-unit
representation; relationships and original expressions remain in the quotations.

Instructions now explicitly require both current and prior-year values when
present and requested. A growth percentage alone is insufficient. The checklist
does not establish number/year/entity/denominator relationships or semantic
support. It cannot supply absent facts, infer scope or authorize source commands.
The unchanged validators, source fallback, final safety check and human approval
boundary remain necessary. No repair call or extra model call is introduced.

Public Draft/API shape, retrieval, mapper contract, model/settings, dependencies,
SQLite schema, stored exports and historical benchmark results are unchanged.
Private payload helpers accept an optional question; legacy calls without it
retain their original payload. The engine supplies its existing query internally.

## Evidence and remaining gate

Synthetic tests cover separate value/count obligations, absent baselines,
unquoted requested years, legacy calls and continued fallback on a lossy response.
A zero-call replay of the retained actual r05 mapping produces the expected
current/baseline/percentage/year checklist. Log-only geography annotations are
excluded explicitly when reconstructing the typed mapping for that replay; the
saved event itself is untouched.

Local snapshots, replay and test output are under
`.pilot-work/composer-coverage-v167/`. The first targeted run exposed an optional
question compatibility error and a Decimal-format test expectation mismatch;
both were corrected before validation. Fixed responses and input replay establish
contracts, not real-model improvement.

Final validation: **87 targeted tests and 1,257 full Windows offline tests pass**
(15 warnings). `pip check` reports no broken requirements, and `git diff --check`
passes. All 15 historical files included in the pre-edit integrity snapshot retain
their hashes. Linux/container checks were not rerun for this side-conversation
change; the earlier v1.66 Linux result must not be relabeled as v1.67 evidence.

**Raw-composer reliability remains unverified.** The pending v1.66 protocol's
version/source identities no longer describe this working tree. Do not execute
that protocol against v1.67 or claim that its previous proposal grants inference.
Before any newly authorized generation, the main thread must refresh source
identity, container/Linux validation and the bounded diagnostic protocol. Test
raw completeness and final fallback separately; stop on failed acceptance gates.
Do not inspect held-out facts for tuning. No new human rescoring is needed for
this engineering change; new assessable generated wording still needs review.

No model calls, Ragas, hosted inference, commits, pushes, service restart,
deployment, approval/export or reviewer contact are included in this change.
