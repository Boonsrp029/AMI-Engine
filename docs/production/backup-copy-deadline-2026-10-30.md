# Bound SQLite backup copy retries — 30 October 2026

The operator backup utility previously called SQLite's online backup API without a progress deadline. An exclusive source lock could keep that API retrying beyond its ten-second connection timeout. A synthetic probe reached the snapshot call and remained blocked until its parent stopped it after 12.03 seconds. No real review history was used and the source bytes were unchanged.

## Change and failure contract

`scripts/pilot_backup.py` now copies at most 128 pages per step and checks a **60-second monotonic copy deadline** through SQLite's progress callback. The copy connection uses a 250-millisecond busy timeout and a 50-millisecond retry sleep, allowing the callback to inspect the deadline during lock contention. This is a cooperative bound between SQLite operations; it does not preempt a stalled filesystem call or bound fingerprinting, the entire restore procedure, or operator response time.

A deadline failure raises `TimeoutError`. The backup/restore CLI reports a static `unavailable` message and exits 2 without printing source paths or a traceback. The incomplete destination is retained for investigation, without a completed manifest. Verification cannot accept it; a later attempt requires a new directory. An interrupted restore does not change its original backup.

Public function arguments, successful manifest fields, existing command arguments, snapshot verification and freshness rules are unchanged. The analyst application, prompts, model settings, dependency versions, corpus and frozen evaluation packages are unchanged. The operator-script change does not alter the pinned v1.55 generator identity or activate a generation allowance.

## Retained evidence

The post-change native probe used the actual default 60-second setting against the same synthetic exclusive-lock condition. It returned exit 2 after **60.25 seconds**, with the expected static reason, unchanged source bytes and no completed manifest. The parent allowed 75 seconds but did not need to terminate it. This is one controlled lock test, not a production recovery benchmark.

Four new tests exercise native lock contention in a separately supervised child, deadline expiration without a manifest, restoration failure without source mutation, and independence from wall-clock changes. Existing backup, WAL, corruption, cached-export and freshness tests remain in the suite. The focused set passed **33 tests on Windows and 33 on Linux**. The native test shortens only its test copy budget; the separate retained probe above uses the real default.

Full suites passed **1,021 Windows tests / 1,020 Linux tests**, with one Windows-only test skipped on Linux and 15 existing warnings on each platform. The Linux operator overlay uses the existing `ami-pilot:literal-v155` dependency image and replaces only the backup utility. All base filesystem layers are preserved; this is an overlay, not a fresh dependency installation. Its test container has networking disabled, a read-only root and synthetic temporary storage.

A separate localhost container restored the read-only owner-history snapshot into disposable storage, restarted successfully and returned all four cached exports byte-for-byte. It created no new human decisions and performed no model or policy calls. The original backup was unchanged and the disposable volume was removed. This verifies the changed utility's restoration mechanics, not a target-deployment recovery or backup schedule. The final integrity report and native probes are under `reports/workflow_pilot/production-readiness-2026-10-27/resume-v33/`.

## Operator and qualification limits

After a deadline failure, investigate lock contention or storage problems, retain the incomplete attempt, and retry deliberately into a new directory when safe. A stale or incomplete snapshot must not be reported as a successful daily backup. No scheduler, automatic retry, off-host transfer, deletion or notification was added.

Daily scheduling, a protected off-host destination, retention/access policy, alert routing, incident ownership and the named deployment's measured recovery-point/recovery-time gates remain pending. Human review of factual drafts is unrelated to this engineering check. The owner still chooses operating destination/ownership and authorizes external activation; new generated drafts and exports retain their separate review gates.
