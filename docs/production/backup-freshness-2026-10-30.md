# Verify backup freshness separately from integrity

The existing verifier accepted an intact snapshot regardless of age. That is appropriate for restoration of historical evidence, but cannot enforce the owner-confirmed 24-hour backup target. A restore also receives a new completion timestamp; treating it as a backup would obscure the age of the original snapshot.

## Additive operator check

```powershell
python -m scripts.pilot_backup check-freshness --snapshot PATH-TO-EXPLICIT-BACKUP --max-age-hours 24
```

| Exit | Status | Operator interpretation |
|---|---|---|
| 0 | `fresh` | Integrity and logical state verified; an original backup's recorded creation time is within the selected age limit. |
| 1 | `stale` | Snapshot verified, but its recorded creation time exceeds the age limit. Arrange an authorized backup and investigate missed operation. |
| 2 | `unavailable` | Freshness cannot be established. Check the explicit path, snapshot integrity, kind and timestamp through the private operator procedure. Do not treat this as a fresh backup. |

The default and maximum limit is 24 hours; operators may tighten it. Exactly 24 hours is within the limit. The check compares timezone-aware instants using the actual current clock after snapshot verification. Future, timezone-free, invalid or UTC-out-of-range timestamps cannot pass. A restore-drill or a record carrying a parent snapshot reference cannot substitute for an original backup. A metadata/type failure returns a static unavailable result without printing raw paths, exception messages or malformed values.

Existing `backup`, `verify` and `restore` commands, formats and return values are unchanged. Historical snapshots remain usable for restoration even when they are stale for operating purposes. The new check reads only; it never rewrites a manifest to make an old snapshot look current, deletes history, creates approvals or switches application storage.

## Evidence and limits

The retained 27 October backup correctly returned `stale` at about 73 hours old, with exit 1. A new, separately located one-time snapshot of the existing owner-reviewed history returned `fresh` with exit 0; its logical state matched the source. The original database and historical backup/manifest hashes were unchanged. No generation, policy invocation, review or export was performed.

Offline cases cover exact age boundaries, UTC offsets, naive/future/extreme timestamps, invalid limits, restored snapshots, corrupted/malformed/missing snapshots, read-only operation, CLI exits and the unchanged original verifier. The initial suite was extended with extreme UTC conversion and oversized-integer cases; earlier results are retained separately from final validation under ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v19/`.

Final results: **29 targeted backup tests**, including 25 new age/CLI cases; **945 Windows passed / 944 Linux passed, one skipped**, 15 existing warnings per platform. The packaged helper hash matches current source, and network-disabled container invocations returned stale/fresh for the respective read-only snapshots. A separate localhost container restored the new snapshot into disposable storage, restarted and returned all four cached exports unchanged; no generation or human decisions were made. The disposable volume was removed.

These checks use the recorded creation timestamp in a locally trusted manifest. Hash verification does not prevent an adversary with access from replacing both database and manifest. Protect the directory and check the host clock. Backup completion time is not a measured transaction recovery point, source-document freshness or proof that an external source is up to date.

This is a one-time local backup and verification mechanism. It does not establish daily scheduling, 24-hour production RPO, off-host copies, encryption/access policy, delivered alerts, incident ownership or sustained operation. A scheduled check must select the intended service's actual latest verified backup, handle nonzero exits and deliver an actionable notification through an authorized channel. No task, transfer or notification is registered or sent by this change.

No factual human scoring is needed for these engineering checks. The owner must confirm operating ownership, destination/access/retention and notification routing before the corresponding production configuration is activated. Existing composer source review and exact-revision approval remain separate human checkpoints.
