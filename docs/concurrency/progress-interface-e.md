# Workstream E — persisted progress interface

The original read-only milestone below is retained for context. The expanded, capability-gated request-to-review/export interface is documented in [E workflow interface](e-workflow-interface.md), with API construction in [A's workflow handoff](e-workflow-api-handoff.md). The new selector does not activate bounded creation in the default server configuration.

Implemented opt-in read-only display of existing concurrent runs. Enable **Show persisted subtask progress** or open an existing run with `?run=<id>&progress=1`. Current request creation stays sequential. A owns the additive authenticated snapshot endpoint documented in [API handoff](e-api-handoff.md); E owns HTML and UI-specific tests.

The panel shows declared branch order, required/optional labels, dependencies, safe reasons, result outcomes and recovery-derived interruption. Counts use the fixed persisted plan; no percentages or ETAs are invented. Finished retrieval is distinct from composition, safety, parent review readiness and exact-revision approval. Optional failures expose incomplete coverage; unavailable projections never silently become sequential runs.

Polling uses1.5seconds whilequeued/running and10seconds for terminaltasks. Failures backoff3/6/12/30seconds; authenticationfailure stops polling andrequiresreconnect. Lastviewandlocaleditsremainvisible butmutations/exportdisableuntilfresh. Selection/epoch/attempt/event-watermark fencing handles stale responses; equal eventsequence canstillcarrynewrevision/reviewdata andisaccepted. The selected runandread-onlyflagareinURL; credentials/drafts/sourcesare notstoredinbrowserstorage. Refreshreconstructsserverstatewithoutrestartingwork. Unsaved edits trigger navigationwarnings.

Same-revision polling preserves draft edits, notes, support confirmation and expanded branches. A changed revision/attempt retains local edits, presents a conflict and blocks stale submissions until explicit reload. Existing source inspection/PDF numbering and role/exact-revision export controls remain. All DOM source/reason text is rendered as text, not HTML.

## Validation status

Fifteen headless Edge synthetic browser scenarios passed, including allstatefamilies, partial/required failure, completedbrancheswithunfinishedbrief, sourceescaping/PDFpage7, dirtyeditpreservation, equal-sequence revisionchange, backoff, authenticationreconnect, late selectionresponses, reload restoration, emptyclaims, readerpermissionsandcachedexportdownload. Screenshotreview corrected UTF8 and badge spacing. No realmodelorownerdata.

A real API/storage integration test additionally checks branchcompletioncannotapprove/export, then exact-revision review/edit invalidation and cachedexportbytes. Its first run correctlyfound that the testexpected409forinvalidrevision0while theexistingschema returns422. The fixture nowtests422andavalid-but-stale409 separately. The historical targeted run passed 84 tests. Its earlier full-suite log ended at 98% without a terminal summary; that is not a pass. Current expanded-Goal evidence is recorded in the linked workflow-interface document.

Run browser checks using an existing Playwright installation and Edge, without changing projectdependencies:

```powershell
$env:NODE_PATH='<existing Node module directory containing playwright>'
node tests/browser/progress-interface.cjs
.venv-release-check/Scripts/python.exe -m pytest -q tests/test_progress_interface.py tests/test_subtask_progress_api.py tests/test_pilot_identity.py tests/test_pilot.py tests/integration/subtasks --basetemp .pytest-tmp/e-UNIQUE
```

Local logs, screenshot, source hashes and exact continuation are in `.pilot-work/workstream-e/`. E implementationwasdevelopedinisolatedworktreecodex/workstream-e-progress andcopiedinto sharedcheckoutonlyforE-ownedfiles afterbaselinefingerprintcheck. A's API/store/identity/projectionfiles were noteditedbyE. No commits,push,deploy,generation,Ragas,Databricksorrealreviewerdecisions. No human factual scoring is needed for these synthetic checks; future actual drafts still require source review and exact-revision approval.
