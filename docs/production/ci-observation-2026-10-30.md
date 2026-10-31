# Current GitHub Actions observation — 30 October 2026

A read-only public API check found [CI run 40892722356](https://github.com/Boonsrp029/AMI-Engine/actions/runs/40892722356), completed with **failure**, for commit `11a3599ec570a5b117fca4b664814dd6d7fc29d8`. The 272 saved source hashes matched that clean checkout before this diagnostic-harness pass. No push, rerun or remote mutation was performed.

| Job | Observed result | Scope of evidence |
|---|---|---|
| [unit](https://github.com/Boonsrp029/AMI-Engine/actions/runs/40892722356/job/123513539490) | Failed at `python -m pytest -q` | Dependency installation and `pip check` steps passed; this is not evidence of another resolver failure |
| [analyst-container](https://github.com/Boonsrp029/AMI-Engine/actions/runs/40892722356/job/123513539599) | Passed | Build and no-inference startup/readiness/restart check passed for that commit; not actual inference or model-quality qualification |
| [serving-environment](https://github.com/Boonsrp029/AMI-Engine/actions/runs/40892722356/job/123513539821) | Passed | The workflow's serving dependency check and synthetic serving smoke passed; not an actual Databricks endpoint deployment |

The public annotation states only exit code 1 for the failed test step. An unauthenticated request for the unit log returned HTTP 403, “Must have admin rights to Repository.” The exact pytest traceback/failed-test summary is required before classifying or repairing the remote failure. The owner has been asked to paste that text. Do not attribute it to dependency versions, runner changes or timeouts without the log.

Annotations also mention Node action deprecation and an Ubuntu runner migration. These are retained observations, not an established cause of the failed tests; no action/runtime/library version was changed on that basis.

The prior local Linux test snapshot contained no paths absent from this commit, ruling out that particular missing-tracked-fixture hypothesis. Current local results do not establish the cause or resolution of the remote failure. New harness changes are unpushed and have no remote CI result.

Ignored local evidence under `resume-v14` includes `remote-ci-observation.json`, `remote-ci-jobs.json`, failed-job annotations and `remote-ci-log-access.json`. Public run/job links and immutable commit identity support the statuses above. No authenticated credentials were accessed or used.

## Prepared failure-report retention

The local unit workflow now adds `-ra --junitxml=.ci-artifacts/unit/junit.xml` to its existing pytest invocation and uploads that report with `if: always()`. The artifact is named `unit-tests-<GitHub commit SHA>` with seven-day retention. Dependency commands, action versions, runner settings and test discovery are unchanged; there is no `continue-on-error` or exit-code suppression.

A deliberate, isolated one-test failure verified a nonzero exit code and a JUnit assertion/failure record. It is a reporting probe outside maintained test discovery, not a newly failing application test. YAML structure and unchanged runtime/dependency identities are checked locally. The existing 900/899 application-suite evidence is retained; the full suite was not rerun solely for this report-output change.

This prepares better evidence for a future owner-triggered CI run; it neither repairs the unknown current pytest cause nor retroactively produces its traceback. The change is uncommitted/unpushed, and artifact delivery has not been verified remotely. Report upload may be unavailable on a forcibly terminated runner. The owner still needs to supply the current failed-test summary/traceback; no new authenticated access was attempted.

## Owner traceback received and reproduced

The owner subsequently supplied the exact three failures: the frozen pilot hash test and two comparison CLI tests hit the same case-file digest guard. The committed LF hash `002a70d7…2047a` exactly matches the remote failure, while the manifest records the existing CRLF working-file hash `acb0933b…2c86`. The [focused byte-preservation repair](frozen-byte-ci-repair-2026-10-30.md) preserves the original manifest/data and disables Git normalization for the two hash-addressed files. An isolated Git checkout reproduced all three failures before the repair; corrected checkout bytes pass the full local Linux suite. The root cause is now established offline. A new remote run is still pending; earlier observations/log-access limits remain historical evidence.
