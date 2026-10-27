# Local SQLite backup and restoration

The owner accepted daily backups and a 30-minute recovery target. `scripts/pilot_backup.py` provides online snapshots and isolated restores using Python's SQLite backup API. It preserves task/revision/event/review history and cached export content without creating a human decision. It does not copy model weights, source corpora, configuration or secrets; keep their pinned identities and copies separately.

```powershell
python scripts/pilot_backup.py backup --database reports/workflow_pilot/pilot.sqlite3 --output reports/workflow_pilot/backups/NEW-UTC-TIMESTAMP
python scripts/pilot_backup.py verify --snapshot reports/workflow_pilot/backups/NEW-UTC-TIMESTAMP
python scripts/pilot_backup.py restore --snapshot reports/workflow_pilot/backups/NEW-UTC-TIMESTAMP --output reports/workflow_pilot/restore-drills/NEW-UTC-TIMESTAMP
```

Every output directory must be new. Existing backups/restores are never overwritten. A failed copy leaves incomplete local evidence; without a valid manifest it cannot be verified/restored. A snapshot captures committed SQLite state, including WAL transactions; uncommitted writes are excluded. It checks database integrity and fingerprints all application rows, including cached export bytes. Restore checks both the file hash and logical state before and after copying. These hashes detect accidental changes, not an adversary who can replace the manifest and database; protect backup access separately.

## Operator procedure

1. Run backup from the intended database with a unique UTC directory. Verify it. Keep copies outside the application volume with access restricted to the operator; review/public-data history can still contain names and notes. Do not commit backup files.
2. Inspect the manifest timestamp, success status and verification result. Alert if no successful backup is newer than 24 hours. A scheduler, off-host destination and alert delivery still require configuration and exercise; none is claimed here.
3. For recovery, stop the affected application and retain its failed volume for investigation. Restore into a new directory. Never overwrite the failed database or change the original backup.
4. Verify the intended corpus/model/config identities. Start a separate localhost instance pointing `AMI_PILOT_DB` to the restored `pilot.sqlite3`, with external access disabled. Inspect task/revision/review history, verify cached exports are unchanged and check that unapproved/empty/outdated revisions remain blocked.
5. Measure from operator recovery start through usable application checks. Record data loss against the last verified backup, elapsed time, failures and owner rollout decision. Only then authorize switching the intended application to restored storage. The script does not switch or deploy automatically.

## Current evidence and limits

An isolated drill restored the actual owner-reviewed history and checked all four cached approved exports through the local HTTP API, byte-for-byte. Empty d06 remained unexportable (409). The original database hash was unchanged, with zero model or policy calls. The measured restore-to-usable interval was about **0.26 seconds** on this local machine. This is one small local restoration, not a deployment-outage recovery benchmark.

Offline tests cover committed/uncommitted WAL data, corrupted/incomplete backup rejection, logical-manifest mismatch, non-overwriting destinations, review history, exact cached exports and edit-invalidates-approval after restoration. Evidence is retained in ignored `reports/workflow_pilot/production-readiness-2026-10-27/recovery-v1/`.

The final local analyst image was also exercised with that read-only snapshot restored into an isolated disposable volume. Non-root startup, restart recovery, four cached export hashes and empty-draft rejection passed without inference or new human decisions. Evidence is in `resume-v1/container-smoke-v4-fixed/`. This verifies container restoration mechanics, not the named staging environment's outage recovery or daily scheduling.

Daily scheduling, off-host storage, retention policy, encryption/access controls, alert delivery, operator assignment and a deployment recovery drill remain pending. No production RPO/RTO qualification is claimed from this one successful local exercise.

The current v1.36 image repeated this no-inference drill successfully; evidence is in `resume-v2/container-smoke-v6/`. Daily/off-host operation and target-environment recovery remain unqualified.
