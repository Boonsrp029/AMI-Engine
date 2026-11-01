# Selection-only mapper migration — v1.60

The owner explicitly selected **“Adopt selection-only mapper with application extracts (offline implementation only)”** on 1 November 2026, accepting the [prospective contract decision](mapper-contract-decision-2026-11-01.md). This record supersedes the proposed status for implementation going forward; it does not edit historical decisions, failures or scores.

## Implemented behavior

The analyst workflow explicitly uses the new `source-selection-v1` wire, mapping `requested-evidence-v40` and workflow `analyst-pilot-v1.60`. The model selects canonical component IDs, states, source-span IDs and scope/gap information. A model-written `short_answer` field is forbidden. Unknown versions, missing required fields and invalid states fail; an old malformed response cannot become a valid new-wire abstention.

The application resolves each selected span against its retrieved source, hash and exact character offsets before using any text. For supported/partial states, it joins **all** selected quotations in selection order into the internal required answer field. It neither rewrites the text nor infers missing facts. Complete extracts longer than 800 characters fail without truncation. Missing/conflicting states keep empty answers and their validated gaps/evidence; conflicts require distinct quotations through the existing validators.

The `application_evidence_extracts` event identifies application authorship, wire/mapping version, exact text, span IDs, source IDs, hashes and offsets. Raw model output remains separate. Exact extracts prove provenance, not relevance, interpretation or completeness. Unknown geography remains unresolved; no location/date is inferred from the question.

Existing anchor, quotation, subject, period, measure, scenario, direction, number, composition and final safety checks remain. Composition still receives source quotations, and [v1.59 omission fallback](investment-coverage-2026-11-01.md) remains active. Final composed claims and human approval/export rules are unchanged. No additional model call or repair loop is added.

## Quantity validation preserved on the selection side

The initial full suite exposed a real migration regression: a declared value-change slot could select project-count evidence, with no model-written numeric answer left to contradict it. The selection resolver now rejects a known other-measure-only selection for the existing typed value/count grammar. It reuses the declared currency/project-unit vocabulary and recognizes explicit project-count wording.

This necessary check does not prove level/change support, percentage denominator, subject or period. Unrecognized units remain unknown. A source containing an office address can still be irrelevant to a financial question despite faithful extraction; numeric compatibility has never been relevance proof. Final source-quality qualification remains necessary.

The wrong-span rejection test is retained with its new precise error. Separate legacy numeric-answer checks remain unchanged. The runtime test formerly injecting a numeric model answer now checks rejection of the forbidden answer field instead; it does not falsely attribute that field to the new model wire.

## Compatibility

The existing EvidenceSelection, EvidenceMap, required legacy answer field, resolver and instruction/version remain available. Default `constrained_selection` behavior is unchanged; a new optional component-type argument explicitly selects the migrated schema. Public Draft/API, SQLite schema, legacy agent, model/settings, retrieval, dependency versions, four-main-call ceiling and human approval controls remain unchanged.

Seventeen runtime test modules explicitly migrate fixed responses using a **test-only** fixture helper. It is not imported by application code and is not a model-output repair. New strict-wire tests bypass it to test actual required-field and forbidden-field behavior. No legacy omission test was deleted.

The offline composer-capture utility preserves valid historical replay under its original contract. It explicitly reports `legacy-model-written-answer-replay`, uses the old parser/mapper semantics in its scoped replay harness and emits no application-extract provenance for old generated answers. New-wire replay is separately labeled. Malformed old mappings fail rather than being upgraded. This replay harness is not a production acceptance path and does not requalify historical output.

## Validation and limits

- **1,133 Windows tests passed.**
- **1,132 Linux tests passed, with one platform-specific skip.** Both platforms retain 15 warnings.
- New strict-wire/provenance tests cover required and forbidden fields, source/hash/offset tampering, unknown IDs, duplicates, states, anchors, source commands, exact length failure, necessary quantity roles, SDK serialization and actual fixed-response workflow safety behavior.
- Both new and historical composer replay are tested, including malformed legacy rejection.
- Restart/restoration checks preserved all four cached approved exports byte-for-byte, with no new human decisions, inference or owner-backup changes. Disposable storage was removed.

Initial failures are retained: three targeted tests assumed the old runtime contract; the first full suite found eight historical replay failures and the real quantity-selection regression. These were addressed with explicit fixture/replay compatibility and a selection-side measure check, followed by a complete rerun. They are not hidden as a clean first attempt.

A clearly labeled offline conversion of retained r04 selections passes the current necessary mapper gates and retains the selected details. It is not a fresh model response, corrected historical attempt, full generated draft or owner acceptance. The original v1.58 failure remains failed. No real model/NeMo calls ran for this migration.

Long selections may now reject at the unchanged internal extract limit. Wrong-but-valid source selection, incomplete retrieval, ambiguous source meaning and incomplete final composition remain qualification risks. Offline tests do not establish real-model quality or production readiness.

## Next step and human review

Prepare a new frozen mapper diagnostic binding the new request, wire, compiler and source/model identities before requesting a separate inference budget. Its prospective criteria must assess selected evidence relevance/coverage and application extracts, then final generated draft quality if conditionally authorized. Preserve the same requested facts and final quality thresholds; do not rescore the old model-written-answer preflight under the new semantics.

No factual scoring is needed for engineering fixtures. New assessable generated drafts require owner source-support and wording review, and export requires exact-revision approval. Independent reviewer usefulness and actual deployment qualification remain separate incomplete gates. No inference, twenty-case run, Ragas, commit/push, deployment or reviewer contact was authorized by the offline design choice.

Detailed local evidence and image identity are retained under `reports/workflow_pilot/production-readiness-2026-10-27/resume-v63/`; those ignored reports are not published benchmark claims.
