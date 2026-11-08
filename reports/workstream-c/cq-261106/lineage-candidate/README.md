# Qualification-lineage candidate — tested, unapplied

This is an isolated offline candidate for the future CQ1 admission gate. It is **not integrated into the application** and authorizes no inference. The current single-composer protocol remains unchanged and verified.

## What changes

Each future development-gate entry must retain four additional private admission fields:

| Field | Meaning |
|---|---|
| `development_contract_path` | Exact retained two-case execution contract |
| `development_contract_file_sha256` | Hash of that contract's original file bytes |
| `started_path` | Original exclusive case-start record |
| `started_sha256` | Hash of the original start record |

Existing result/assessment paths and hashes remain. The helper validates the contract's canonical self-identity, exact case/start reference, pair ordering, pipeline/model/settings/limits, result source query/corpus, positive bounded reserved deadline, stored plan/event identity, counters and non-reused run/attempt IDs. Source findings must be explicit nonblank strings. Both cases must come from the same retained execution contract. JSON identity comparison distinguishes booleans from numeric settings.

This rejects the reproduced outer pipeline relabeling and old minimal gate records. It does not rewrite actual artifacts, change public APIs, alter the Plan schema, change thresholds or provide cryptographic proof of a human judgment or semantic support.

## Reviewable files

- `lineage_candidate.py`: test-only wrapper around the current gate plus proposed helper.
- `proposed_development_lineage.py`: exact helper content proposed for integration.
- `proposed_qualification_phase.py`: exact current module plus helper import/call.
- `integration.patch`: **unapplied** two-file diff.
- `manifest.json`: candidate/patch hashes and unchanged live module hash.
- `test_lineage_candidate.py`, `test_patch_candidate.py`: synthetic checks only. Proposed modules are loaded in memory; the live module is not overwritten.

## Verification

The first candidate set passed19checks. Expanded checks passed24. The final exact-patch set passed **27 checks in1.48seconds**, terminal exit zero (`../lineage-candidate-tests-v3.txt`). Includes legitimate reduced deadlines, outer relabeling, missing/wrong start/contract, stale settings/model, boolean/numeric mismatch, wrong query/corpus/plan, reused run/attempt, mixed contracts, source-finding/counter failures, and the existing9/10category stop rule under the proposed module.

`git apply --check` succeeds. This command only checks applicability; the patch has not been applied. The pending composer protocol's119inputhashes and6requesthashes still verify. No full integrated-runtime success is claimed for this candidate. Its27checks are not part of the earlier1583application/capturepasses or6separatecontrollerchecks.

Reproduce the candidate checks offline from the repository root:

```powershell
.venv-release-check/Scripts/python.exe -m pytest -q reports/workstream-c/concurrent-qualification-2026-11-06/lineage-candidate --basetemp .pytest-tmp/lineage-review
git apply --check reports/workstream-c/concurrent-qualification-2026-11-06/lineage-candidate/integration.patch
```

## Integration boundary

Do not apply this patch silently while the pending composer protocol is frozen: it pins `qualification_phase.py`, and applying the patch would change that reviewed identity. After that package is closed or deliberately superseded, integrate the helper, update maintained admission fixtures to retain complete lineage, run affected/integrated checks, and freeze subsequent development/CQ1 contracts. Do not reuse the old grant or treat candidate tests as a passed actual development pair.

Until integration, the live qualification gate retains the diagnosed limitation. No CQ1 execution is ready or authorized. The single composer-only diagnostic does not use that gate and remains independently awaiting its explicit grant.
