# Offline table boundary repair results

The opt-in whole-span concurrent mapper now receives a complete exact table window when the ordinary reading boundary separates a row label from its values. A unique authorized source record must establish the period, column headings, row label, amount and share. The selected window starts at the year before the headings and ends after the row. Windows exceeding 600 characters are excluded. Existing reading spans retain their IDs and offsets.

An initial row-only implementation failed integration because its quotation omitted the measurement year. Strict numeric validation detected the omission. The final implementation preserves the year and both column headings inside the exact selected window. Negative amounts, ambiguous rows, incompatible units, multiple matching records and changed source content receive no silently inferred row. Hash mismatches fail explicitly.

The new private helper is src/pilot/subtasks/_table_spans.py. Its call site is restricted to the existing whole_fact_spans concurrent path. The private mapping version is cq-fact-span-selection-v1-complete-table-rows. This pass changed the existing scoped composer and fact version, and added helper/tests. Other pre-existing checkout changes were preserved.

## Verified checks

- Targeted mapper, focus and boundary suite passed 107 tests.
- Full maintained Windows offline suite passed 1,869 tests with 14 warnings in 504.42 seconds. The terminal process exited zero. [JUnit](offline-windows.xml)
- Socket-blocked fixed-response mapping and composition passed for consumed cq1-a28 and cq1-a27. The retained cq1-a28 duplicate response fails the repaired schema. A deliberately selected fixed response completes through verified unit rendering. Actual model calls and NeMo invocations were zero. Largest prompt reservation was 3,671/4,096 tokens. [Replay](offline-replay.json)
- Captured archived outputs, original corpus/source inputs and dependency manifests retain their hashes. Two expected existing runtime files changed. The helper and tests are new files. [Integrity](integrity-check.json)
- The new wrapper's inspect-only admission passed for 129 frozen inputs. No execution grant was created.
- git diff --check passed. Git reported existing line-ending conversion warnings.

These checks establish offline engineering behavior. They do not establish new model quality, fresh safety outcomes, owner acceptance or production qualification. This pass did not rerun Linux qualification.

## Remaining gates

The archived CQ1 batch remains one passing case, one technical failure and eighteen unattempted cases. Both attempted cases are consumed. Its allowance is closed. Preserve the owner's explicit U.S. editorial copy and the original generated result independently.

The next execution candidate is a new consumed development allowance for cq1-a28 followed conditionally by cq1-a27. [Authorization packet](authorization-packet.md)

Manual human review is required for future technically assessable outputs before owner acceptance. Any stored approval/export applies to the exact stored draft revision. A fresh twenty-case qualification must freeze its revised pool before generation and obtain its own applicable grant after development succeeds.
