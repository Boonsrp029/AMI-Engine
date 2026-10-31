# Read-only stored telemetry report

The operator CLI `scripts/pilot_operational_report.py` summarizes existing SQLite workflow telemetry without loading the agent, model SDK, project environment files or NeMo. It is an independent preparation step while source/wording review and remote CI remain pending; it does not qualify live monitoring or advance the failed quality gate.

Run from the repository using a database you are authorized to read. Prefer a verified backup for historical analysis:

```powershell
python -m scripts.pilot_operational_report `
  --database reports/workflow_pilot/production-readiness-2026-10-27/recovery-v1/backup/pilot.sqlite3 `
  --output reports/operations/stored-telemetry-2026-10-30.json
```

The output path must be new. The tool refuses to overwrite reports or create a missing database. A read-only SQLite transaction keeps the aggregate queries in one snapshot; it never initializes `Store`, migrates schema, reviews a draft or exports a brief. The existing backup was checked before and after a real report invocation and its bytes were unchanged.

## Report contents and boundaries

- Status counts for the selected latest runs, with unknown statuses bucketed rather than printed.
- Nearest-rank p50/p95 of **recorded run elapsed times**, plus sample count and missing/invalid metrics. These may include synthetic, replayed, failed or edited runs; they are not qualified warm end-to-end latency or sustained-load results.
- Model-request, model-call, model-failure and guard-invocation **event-marker counts**. A marker is not proof of backend inference, completion or cancellation.
- Available input/output token totals from valid model-call metadata and a count of events without valid usage. No valid metadata means `null`, not zero. An explicitly recorded zero remains a known zero.
- NeMo internal tokens, monetary cost and hardware/energy cost remain `null`; overall token accounting is explicitly incomplete.
- Local conditions such as failed/interrupted runs, unavailable latency, partial usage and truncation. These are report flags, **not delivered alerts**.

Queries, source text, reviewer identities, raw errors, arbitrary event labels and database paths are not output. JSON metadata is size-limited and invalid values are counted, not echoed. Unknown usage or malformed telemetry cannot turn into a zero-cost or successful-operation claim.

Defaults are the latest 10,000 runs and at most 100,000 matching event markers, ordered deterministically. Optional `--run-limit` / `--event-limit` may reduce those limits. Totals and truncation are disclosed. Selected JSON fields are capped at 64 KiB and processed as a stream; database/query processing has a five-second limit plus bounded connection wait. An error yields a sanitized error type and nonzero exit rather than a partial success report.

The tool reads the host database or backup. It is not automatically installed into the existing runtime image, scheduled, exposed as an HTTP endpoint or connected to an external service. An actual live deployment requires separate packaging, permissions and qualification.

## Operator response

If failed/interrupted runs are present, inspect the corresponding history in the authorized application before deciding whether a retry is safe and permitted. Historical counts alone do not identify a new incident. Investigate missing telemetry and truncation before drawing conclusions; increase limits only within the declared caps or select a more appropriate snapshot. Do not infer warm p95 compliance from this report or an edited owner-review database.

Alert routing/delivery, deduplication, incident ownership, production thresholds, service/data freshness checks, access controls, retention, scheduling and a sustained-workload drill remain open qualification gates. No email, Slack message, webhook or other external notification is sent by this CLI.

## Evidence

Twelve targeted synthetic tests cover read-only behavior, unknown/zero usage, redaction, malformed/oversized metadata, deterministic limits, missing database and non-overwriting output. Initial fixture failures exercised the existing PII/request-key guards; fixtures were corrected without changing those guards. A report against the verified historical backup contains only aggregate data and performs zero model/NeMo calls, reviews or exports. Full offline results and backup before/after hashes are retained in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v17`.

Integrated results: **912 Windows tests passed**; **911 Linux tests passed, one skipped**, with 15 existing warnings on each platform. Linux used the verified dependency image with sanitized current scripts/tests mounted read-only and networking disabled; this is not a fresh dependency build or remote CI rerun. The backup hash remained `661fedef976e5610c65dc9b032b6ab0626b26739cf15767bc591dc22522ed537`.
