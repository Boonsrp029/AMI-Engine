# Whole-span implementation checkpoint

The owner selected complete source span IDs for offline implementation. The new private opt-in contract is cq-scoped-fact-span-composition-v1. The original phrase-offset contract remains selectable. Changes are in src/pilot/subtasks/_fact_selection.py, _scoped_generation.py, _scoped_activation.py and tests/test_scoped_fact_selection.py.

The targeted offline suite passed 109 tests. Fixed-response coverage includes supported paraphrase, capability retention, numeric substitution rejection, missing and conflicting facts, and same-record context. No model calls ran.

Next: inspect the integrated whole-span mapper and composer requests against the 4096-token budget for the frozen roster and both consumed development cases. Freeze a new diagnostic contract only after these checks. Obtain a fresh exact grant for any actual request. Keep the failed offsets and context-ID diagnostics unchanged. No qualification pass or manual adjudication follows from these offline tests.
