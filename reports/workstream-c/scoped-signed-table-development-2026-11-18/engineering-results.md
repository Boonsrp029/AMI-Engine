# Signed-table offline repair results

The table recognizer now uses a dedicated signed numeric pattern for totals, optional-footnote lookahead, amounts and shares. This lets it pass a negative row and identify a later requested row. Conversion statements and conversion claims keep the existing unsigned pattern. Private mapping version is cq-fact-span-selection-v1-signed-table-rows.

The current change affects _request_focus.py, the mapping version in _fact_selection.py and focused table tests. Existing source-window, citation, scope, composition, guardrail and exact-revision controls remain active. Public APIs, sequential default, source corpora, dependencies and model settings retain their earlier contracts.

## Validation

- Targeted checks passed 119 tests, including positive rows after negative rows, requested negative rows, footnote separation, malformed signs, duplicate rejection and unsigned conversions.
- Full Windows offline suite passed 1,881 tests with 14 warnings in 498.40 seconds. The process exited zero. [JUnit](offline-windows.xml)
- Socket-blocked fixed-response mapper/composer checks passed for the two consumed cases. The old archived parser offers no focus for Other sources. The repaired parser does. Both retained incorrect responses fail the repaired schemas. No model or NeMo calls ran. [Replay](offline-replay.json)
- The largest request reservation was 3,702/4,096 tokens.
- All 187 archived execution input copies verify against their frozen hashes. Only the two expected current runtime files differ from that execution. Source snapshots, dependency manifests and historical results retain their bytes. Accepted editorial copies still match their owner record and original result hashes. [Integrity](integrity-check.json)
- New two-case wrapper admission passed for 140 frozen inputs. git diff --check passed with existing line-ending conversion warnings.

Actual repaired-model quality, current safety outcomes and owner acceptance of future drafts remain pending. Linux validation was not rerun in this pass. Fixed-response success cannot regrade the stopped actual qualification.

## Next diagnostic

The frozen candidate runs consumed cq1-a38 once and only then cq1-a37 once after all first-case gates pass. Maximum eight local main calls and two NeMo invocations total, 180 seconds per case, zero retries/warmups. A fresh direct generation grant is required. [Authorization packet](authorization-packet.md)

The prior actual qualification remains one pass, one technical failure and eighteen unattempted cases. Preserve those eighteen until any later fresh pool is predeclared. Manual source/wording review applies to future technically assessable drafts. Stored approval/export requires the exact stored revision.
