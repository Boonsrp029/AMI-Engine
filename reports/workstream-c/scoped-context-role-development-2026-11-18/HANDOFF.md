# Paused at the owner's request

The user requested pause during offline schema repair on 18 November 2026. No actual model call or NeMo invocation ran in this repair pass. No test process remains live. The targeted process exited zero with 124 passes. The full suite has not yet been run for this revision.

Implemented changes are limited to src/pilot/subtasks/_fact_selection.py and new tests/test_scoped_context_roles.py. Private mapping version is cq-fact-span-selection-v1-distinct-context. The generic schema now creates one branch per direct span, with a fixed direct identifier and context choices excluding that identifier while retaining same-record binding. The prompt explicitly requires distinct context IDs and empty context when unnecessary. Wire keys, context maximum two, semantic rejection, dependency versions and model/settings remain unchanged.

The new tests use unrelated canal/reservoir facts. They verify self-context rejection for every generic direct span, single-span empty context, valid same-record context order, wrong-record/unknown ID rejection and continued semantic rejection of repeated context IDs. The schema intentionally does not encode every cross-selection uniqueness invariant. Do not remove the strict resolver checks or silently deduplicate responses.

Targeted command completed successfully with 124 passes in 7.63 seconds.

```powershell
.\.venv-pilot-clean\Scripts\python.exe -m pytest -q tests/test_scoped_context_roles.py tests/test_scoped_fact_selection.py tests/test_scoped_table_spans.py tests/test_scoped_request_focus.py --basetemp=.pytest-tmp/context-role-targeted
```

Next exact step after resume is to revalidate current source/instructions and usage, then complete socket-blocked fixed-response replay and schema/request-size measurements. The retained cq1-a40 self-context response must fail parsing under the repaired schema. Verify a correctly selected source with valid context through composition using fixed responses, retaining the old failure. Then run the full Windows offline suite and integrity checks. Only after these checks should a new bounded actual diagnostic be frozen and its applicable grant requested.

The preceding signed-table qualification directory retains all 201 frozen execution inputs in executed-input-snapshot. Its actual batch remains one pass, one technical failure and eighteen unattempted cases. cq1-a39/cq1-a40 are consumed. The latest generation allowance is closed. No new development contract, grant record or generation attempt has been created for this context-role repair.

Owner acceptance of the earlier U.S.-explicit signed-table development copies is preserved in the preceding directory. Current qualification result cq1-a39 remains owner-pending and cq1-a40 has no final draft to review. Exact stored approval/export and full quality qualification remain incomplete. No commit, push or deployment occurred.

## Current checkpoint

The subsequent full Windows suite passed 1,886 tests. The repaired schema rejected the saved self-context response, and both fixed-response workflows completed with sockets blocked. The development contract with SHA-256 6ad60047b361442d0141f9b333bc0fb4a296ede6660add27a1f23f59d2c96157 passed admission for 153 inputs. Actual execution awaits the separate grant in [the authorization packet](authorization-packet.md).

The [revised twenty-case roster](../cq1-context-role-pool-2026-11-18/README.md) is predeclared with eighteen exact retained cases and two replacement questions. Offline admission passed all twenty. The qualification compiler correctly stopped because two actual current development results and assessments are missing. After a valid development grant, run cq1-a40 first and assess it before conditionally advancing to cq1-a39. Compile qualification after both pass and use the applicable Bangkok date.
