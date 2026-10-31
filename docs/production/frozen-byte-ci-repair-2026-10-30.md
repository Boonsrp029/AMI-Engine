# Frozen pilot byte preservation — 30 October 2026

**Exact remote failure reproduced and repaired offline; remote rerun pending.** The owner supplied the pytest traceback for [unit job 123513539490](https://github.com/Boonsrp029/AMI-Engine/actions/runs/40892722356/job/123513539490) at commit `11a3599ec570a5b117fca4b664814dd6d7fc29d8`. Its three failures share the same pilot-file integrity mismatch; dependency installation/checks were successful.

## Root cause

The manifest records SHA-256 of the existing CRLF working files. Git's `core.autocrlf=true` had normalized their stored blobs to LF. A Linux checkout received different bytes while retaining identical JSON values. The committed LF case-file hash exactly matches the owner-provided failure:

| File | Frozen/current CRLF hash | Committed LF hash |
|---|---|---|
| `data/pilot/cases.json` | `acb0933b846713b0a7e7305681ce99a760d1079d5221f11955dbd83ab18f2c86` | `002a70d7c0c7eb5f1fc96ab5846bd9e60f19a4dacd0a7f713db1e16c3752047a` |
| `data/pilot/synthetic_corpus.json` | `737f57f4a47086d50f5d459dad537e2a4ffcb394a6278da13d99dfcc04d3b67e` | `aa20bf4555dee46e301a97a0700bccc81adc1a559bce6eeda90e7ae927101cbd` |

`test_pilot_split_is_frozen` checks both files. The other two failures reach the same strict case-file guard in the comparison CLI. This is not a library-version or model failure.

## Focused repair

The root `.gitattributes` disables text conversion for exactly these two byte-addressed files. Scoped whitespace settings recognize CRLF while retaining checks for real trailing spaces, blank EOF lines and spaces before tabs. The existing manifest, questions, references, split IDs, corpus contents and working-file bytes are unchanged. Hash validation remains strict; no normalization or alternate digest is added to the runtime.

The working files were touched only to refresh Git's old stat cache under the new attribute policy; their byte hashes remain identical. Git now shows their corrected stored representations as changes relative to the old LF blobs. This is an intentional line-ending-only Git diff, not a benchmark revision. The primary Git index and HEAD were not changed by the agent.

**The future commit must include `.gitattributes` and both JSON files together.** Committing only the attributes would leave the already-normalized blobs in the old index. When the owner chooses to commit, stage these three paths explicitly. No commit or push was performed automatically.

## Validation

An isolated scratch Git repository reproduced the original normalization, then staged the existing frozen bytes under the new attributes. Both `core.autocrlf=false` and `true` checkouts preserve the original hashes. A Git archive built from that scratch tree also preserves them. A deliberately added real trailing space is still rejected. No scratch commits were created and the primary repository index remains unchanged.

Network-disabled Linux tests using the original Git-derived LF bytes reproduced **all three reported failures**. The same sanitized current-code environment using corrected Git-checkout bytes passed the **full 899-test Linux suite, one Windows-only skip and 15 existing warnings**. The three reported tests pass on Windows, with two existing import warnings. The prior full Windows 900-test result remains retained; it was not repeated solely for unchanged application code and a byte-policy fix.

The Linux reproduction uses Git-derived frozen files in the sanitized current-code context, not a fresh dependency installation or an entire historical clone. Application source hashes match the verified local image. No new model, NeMo, Ragas or hosted inference was invoked. Source snapshots, historical outputs, owner CSV/comments, approved exports and dependency versions remain protected.

Ignored evidence is under `reports/workflow_pilot/production-readiness-2026-10-27/resume-v16`: user-trace excerpt/provenance, exact working/blob hashes, isolated Git checkout/archive checks, `linux-before.txt`, `linux-after.txt`, `windows-targeted.txt` and reproduction results. Actual GitHub CI must still be verified after an owner-authorized commit/push. The separate v1.53 drafting quality gate remains unverified by these tests.
