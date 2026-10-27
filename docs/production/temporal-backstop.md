# Explicit-period backstop — necessary support only

The saved source-policy diagnostic falsely accepted March 2024 when its source stated March 2020. `src/utils/_periods.py` now provides a deterministic necessary check before NeMo judging. The pilot reuses the same period parser through its existing `_scope` exports, preserving its decoder and scope-import contracts.

The backstop recognizes full English month/year and valid ISO dates. It blocks absent/invalid explicit dates, publication-only substitutions for observations, and recognized source instructions used as date evidence. A complete ISO observation can support its coarser month; a month cannot establish a specific day. Whitespace normalization does not alter the original report or supplied model prompt.

A narrowly worded standalone gap such as “The supplied evidence does not establish an observation for March 2024” does not assert a March 2024 observation. Positive assertions in the same or following clause remain checked. This exception is not a general negation classifier. Different legitimate gap formulations may be blocked conservatively and need review.

Date presence never grants approval: NeMo still checks the unchanged report and source text, and the pilot retains stricter per-component citation, period, measure and numeric validation. The public guardrail result shape remains unchanged; a deterministic rejection uses `blocking_rail=explicit_source_period`. No repair call, inferred date or bypass of a negative judge verdict occurs.

## Evidence and limits

Offline tests replay the saved j04 fact pair and prove it is blocked before any judge call. Additional fixtures cover multiline periods, leap days, invalid dates, publication versus observation dates, precise/coarse dates, genuine evidence gaps, disguised positive assertions and source instructions. Existing scope and guardrail tests still execute. Initial collection exposed a private parser export dependency in `_choices`; that compatibility export was restored and the failed log retained.

This does **not** prove semantic support. Relative dates, abbreviations, quarters, general year-only statements and other date forms are outside this parser. Matching a date somewhere in multiple sources cannot establish its association with a particular company, measurement, projection or claim. Tests explicitly retain these limitations rather than calling every recognized match a supported answer. Human source adjudication and fresh end-to-end quality gates remain required.

The historical model-only policy result remains 5/6 with a critical wrong-date acceptance. A combined workflow using a deterministic rejection is a different control path, not a corrected model verdict or evidence of general judge accuracy. New generation requires separately authorized, versioned attempts; original cases, outputs, owner judgments and dependency versions are unchanged.
