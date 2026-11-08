# D-scope lifecycle barrier repair

The repaired decoder full suite terminated with1failure,1547passes and14warnings. The only failure was the HTTP active-shutdown/retry fixture receiving409 on release while the retried run was not yet current/running. A targeted recheck passed1test, confirming timing sensitivity rather than providing a clean full result.

Inspection found finish_api waited only for a historical attempt_id, which survives while the retry is queued. Under the Goal-authorized D execution/failure-control scope, this helper now waits for the authoritative API snapshot: run.status running, progress.attempt_current true, nonempty current attempt_id. No application runtime or release assertion was weakened. A deterministic mock supplies queued-old then running-new snapshots and forbids release before the latter. All7lifecycle tests passed (one warning).

Only tests/integration/subtasks/test_e_workflow_lifecycle.py changed after the full-suite source freeze. All C runtime hashes in contractv4 still match. This is not a new inference allowance. A final integrated run validates the stronger fixture and current revision; the original failure is retained.
