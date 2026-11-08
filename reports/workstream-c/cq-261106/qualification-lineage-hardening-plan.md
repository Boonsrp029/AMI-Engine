# Future CQ1 development-lineage hardening — isolated offline pass

Current evidence: `qualification_phase.py::_verify()` checks two file-hashed passing results/assessments and equality of declared pipeline identities, without requiring the development start/contract records. The synthetic, zero-inference reproduction is in `goal-requirements-audit.json`. No real stale admission or CQ1 attempt is claimed.

## Ownership, boundaries and dependencies

D qualification-controller scope owns the gate and its regression tests; C may prepare the candidate under the active Goal's explicit D access. No agents/workers are launched. A/B runtime, retrieval, public Plan/Draft/API, prompts, model/settings, dependency constraints, owner records and actual artifacts remain unchanged.

The pending composer-only protocol pins this module, so do **not** edit the live module while that package awaits a user grant. Prepare a workspace-contained candidate copy/patch and synthetic checks first. It is acceptable to load a candidate module under the same package namespace for isolated tests; do not overwrite the current imported gate or treat candidate checks as integrated-runtime evidence. Integrate deliberately after closing/superseding the affected package, then freeze future workflow/CQ1 identities again.

## Small passes and explicit private-contract change

1. Require each future qualification gate entry to include retained development contract and start paths/hashes, in addition to existing result/assessment hashes. This is an explicit **private admission-artifact contract** change; legacy minimal synthetic gate entries must fail closed. It does not rewrite historical actual results or require retroactive scoring.
2. Validate the development contract's canonical self-hash, exact start record's case/contract reference, membership/order of both cases, matching declared pipeline identity, and matching model/settings. Bind the retained result/assessment to that exact started case and source query/corpus. Merely relabeling the outer gate cannot establish identity.
3. Preserve execution details when comparing planned/stored identities: preparation reduces the runtime deadline, so compare the immutable plan fields and verify a positive bounded reduced deadline rather than demanding equality with the unreduced frozen plan ID. Do not reject a legitimate current run merely because its deadline was reserved correctly.
4. Reject reused run/attempt IDs across the two passing cases, mismatched source/corpus/query, technical failure, missing source findings, changed files, wrong case/order, stale model/settings, and self-consistent outer relabeling of an older pair. Preserve all category thresholds and exact review-bundle owner acceptance.
5. Test positive current lineage, negative old/minimal lineage and legitimate reduced-deadline cases with fabricated public facts and fixed records only. Run targeted gate/admission checks first. Integrate only when its actual execution package can be re-frozen without silently changing an outstanding grant.

## Acceptance and remaining limitations

Candidate checks must fail on the reproduced relabeling case, pass correctly linked records, leave original fixtures/artifacts untouched and make zero model/network/Store calls. After integration, run affected development/qualification/controller checks and the integrated suite when the change justifies it; separate candidate and integrated results explicitly.

This is provenance validation, not cryptographic proof of a human assessment or semantic support. The operator must still establish the real user grant outside JSON, verify the actual source/model identity at execution, perform source review, and obtain required exact-output owner adjudication. The passing development pair and20case actual quality evidence are still absent. No CQ1 or additional generation is authorized by this plan.
