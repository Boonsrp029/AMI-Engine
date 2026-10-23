# Owner handoff — 2026-10-21

## Saved implementation and evidence

- Local request → bounded tools → cited draft → correction → review → approved
  export is implemented in `src/pilot/`. Existing agent APIs remain available.
- Verified environment: `.venv-pilot-clean` (Python 3.12.10). `pip check` succeeds;
  final offline suite: 88 passed, three warnings. Serving resolver dry run
  succeeds; Linux CI and deployment are unverified.
- Original `.venv` is untouched. `.venv-pilot` was an initial diagnostic
  environment containing the Spark namespace collision; use the verified clean
  environment instead. Existing credential files were not rewritten.
- Fixed event-loop/client lifetime for real Ragas scoring. Synthetic parity
  fixtures retain original report, checkpoint, logging and prompt contracts.
- Frozen comparison: ten generation attempts; ten legacy and four workflow
  scored rows across two judge passes. Five additional boundary attempts are
  retained. See `validation-2026-10-21.md` and `evidence/results.json`.
- All 42 protected historical artifacts retain their original hashes.
- No commit, push, external deployment or reviewer contact was performed.

## Local application

The final local app was left running on `http://127.0.0.1:8000` with the explicitly
labelled automated QA history in `reports/workflow_pilot/browser-qa.sqlite3`.
That history is not external human usage. To launch a new pilot session later:

```powershell
$env:AGENT_LLM_PROVIDER='ollama'
$env:AMI_PILOT_DB='reports/workflow_pilot/pilot.sqlite3'
.\.venv-pilot-clean\Scripts\python.exe -m uvicorn src.pilot.api:create_app --factory --host 127.0.0.1 --port 8000 --workers 1 --no-access-log
```

Stop any existing listener before starting another instance on the same port.
Reload the page after a server restart to obtain the new session token.

## Exact next step and remaining acceptance gates

1. Human-adjudicate the five paired outputs using
   `reports/workflow_pilot/comparison-2026-10-21/human_review.csv`. Check omissions
   and evidence gaps, not just claim citation IDs. The new workflow answered
   only 2/5 cases; the unavailable-revenue boundary produced unrelated claims.
2. Address observed quality failures using development cases. Add new held-out
   facts for a later benchmark; these five outputs have now been inspected.
3. The owner invites 1–3 reviewers using `reviewer-protocol.md`. Record two
   tasks per person and raw checking/correction time, edits and feedback.
4. Implement one improvement supported by actual reviewer feedback and rerun
   affected checks. External usefulness and this iteration remain pending.
5. Review the diff, then commit/push when ready and inspect the real Linux CI
   result. The code was not deployed outside localhost.

The technical evidence is ready to inspect and the case study can support an
application with these limitations. Do not claim external usage, business ROI,
fintech production experience or enterprise readiness from the current results.
