# Composition request context repair — v1.53

**Offline repair; no new model-quality claim.** The [v1.52 diagnostic](diagnostic-v152-findings.md) passed mapping, then failed drafting after request context was omitted from the composer input.

The private composition payload now includes a separate `requests` block with validated component IDs, question anchors and supported/partial status. The composer can associate each evidence unit and its origin aliases with its actual task. Quotations and established scope remain factual authority. Request wording cannot establish a date, location, value or scenario; lossy mapper short answers and unrestricted gap text are still excluded. Canonical evidence grouping, unit identities, citation assignment and deduplication are unchanged.

The composition instruction makes that separation explicit. Prompt version is `analyst-pilot-v1.53`; mapper remains `requested-evidence-v37`, since mapper inputs/instructions were not changed. Public `Draft`/APIs, retrieval, model/digest/settings, four-call ceiling, fallback, final NeMo and approval/export controls are preserved. No library version changed.

New synthetic contracts cover request/measure identity, shared-evidence origins, exclusion of mapper summaries and missing/gap text, prevention of question-derived scope, actual engine delivery, four-call limits and final guardrail rejection. The targeted suite passes 56 tests. Full-suite, source-overlay image/recovery and protected-evidence checks are retained in local `resume-v13`. These fixed-response tests do not establish actual composition quality.

The updated image remains a source overlay on previously verified dependencies. It does not supersede the retained missing-cache failure of the fresh offline full build. Current-source Linux/recovery checks and fresh dependency-build reproducibility remain distinct evidence.

## Next technical action

Freeze a **composer-only** diagnostic from the actual retained r06 tools and mapper result, using the updated request payload and current schema. Preserve the former failed composition as a replay that still fails validation. A new composer response must pass actual projection/citation/measure/count/scope checks before any conditional full workflow. Final NeMo remains required for a complete workflow; a composer-only preflight must not fabricate a guard invocation or claim owner acceptance.

Prepare and test the isolated capture/validation path, preserve source/model/request identities, then propose its time/call budget before actual generation. Repeating another mapper preflight would not target the new failure. No new protocol or generation authorization is established by this document. Do not ask the owner to score a technical failure; request source/completeness/usefulness review only for a new assessable draft.
