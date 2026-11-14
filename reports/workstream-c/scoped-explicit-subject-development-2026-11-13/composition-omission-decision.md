# Concurrent composition omission decision

The retained cq1-a20 result passed technical and safety checks but failed source review. The mapper selected a sentence that answered both parts and a general metering sentence. The prompt asks for a claim per unit. The wire schema accepts ordered subsets, but application projection restores every omitted unit from its selected text. The [socket-blocked replay](cq1-a20-omission-replay.json) reproduced the exact draft and showed that both synthetic responses which omit the background unit publish that background via the existing fallback. Preserving the source's historical capability in the synthetic response changes its first claim, while the background remains.

## Proposed scoped contract

Require one explicit decision for every eligible canonical prose unit. The composer can emit a cited claim or identify a unit as background or redundant for the request. Require that each supported or partial component represented by an omission still has a retained unit from one of its own origins. Unknown, repeated, overlapping and incomplete decisions fail closed. Preserve mandatory table-row selection. Keep the current default and sequential contracts. For the opt-in revision, suppress fallback for explicitly omitted units only and record the omitted IDs, reasons and original source lineage. An unaccounted omission must fail, so a missing unit cannot silently disappear. Retain all source checks and the final NeMo check.

In the mapping and composition instructions, require passages and claims to answer a requested part or supply necessary context. Keep explicit subjects and preserve source modality and time, including historical capabilities expressed as “could.” The application will not promote an explicit omission to a missing-evidence finding automatically. Record semantic completeness and historical capability in the exact-source assessment. Structural origin coverage cannot establish whether a retained claim answers every requested fact.

The [offline prototype](check-omission-contract.py) passed eight synthetic accounting checks using distinct facts. It is isolated from the application. Runtime integration should cover covered-component omissions, only-evidence rejection, omissions involving shared origins, mandatory rows, raw/final provenance, strict validation, and actual preservation of historical wording in fixed responses. Fresh generation would require a separately frozen grant after implementation.

## Alternative

The [two-case boundary check](omission-boundary-results.json) found that the origin guard accepts both a background omission and an omission of the only annual maintenance figure when both units share one component. Origin coverage establishes structural accounting only. If the broader contract is chosen, retain exact-source review for every requested fact and include this case as a required rejection in the qualification rubric.

The current composer already canonicalizes exact duplicate evidence when source ID, quotation, established scope and scope citation IDs match. It preserves each originating unit for validation. The canonical-composition and duplicate-assertion suites passed 11 tests on the current checkout. Adding an exact-duplicate omission wire field would leave the distinct background span in cq1-a20 untouched.

Keep the current projection contract and tighten the mapper to select only necessary evidence. This avoids a new composer wire shape, but the fallback still republishes any extra span that passes mapping. The replay shows why changing the composer prompt alone leaves that behavior in place.

**Recommendation:** retain the existing omission fallback and exact-duplicate handling. Tighten mapper relevance and require preservation of historical capability in composition. If distinct background still passes mapping, use the retained result to evaluate a broader omission contract with an explicit fact-coverage gate. The inactive prototype does not provide that gate.
