# Focused publication packet for the CI byte fix

**Historical preparation record; subsequently [published with successful exact-commit CI](ci-publication-2026-10-30.md) after the owner’s direct grant.** At preparation, anonymous public metadata confirmed `main` pointed to `11a3599ec570a5b117fca4b664814dd6d7fc29d8`; its latest observed [CI run](https://github.com/Boonsrp029/AMI-Engine/actions/runs/40892722356) is completed with failure. This follow-up isolates the [frozen-byte repair](frozen-byte-ci-repair-2026-10-30.md) from newer local application work.

The packet contains exactly three paths: `.gitattributes`, `data/pilot/cases.json`, and `data/pilot/synthetic_corpus.json`. It restores the original byte-addressed CRLF JSON representations and disables text conversion for those paths. Parsed values, manifest bytes, case splits/references, prompts, dependencies, workflow configuration and application logic are unchanged. The uncommitted JUnit workflow enhancement is excluded.

Patch SHA256: `4f634f0a1b387aaa6cb09336605e26f07ccd01ea7fdfbf9bbcc12468e1c5146f`. The ignored local review packet is `reports/workflow_pilot/production-readiness-2026-10-27/resume-v24/review-packet.md`; the patch and all provenance/results are beside it.

## Exact committed-source check

The source snapshot was read from the committed Git tree using an explicit allowlist, scanned for credential-shaped data and tested with networking disabled. All source hashes were verified and the imported engine path confirmed under the historical snapshot, excluding current v1.54 source.

| Check | Result |
|---|---|
| Before the three-file patch | All three owner-reported hash failures reproduced. |
| After only that patch | **887 passed, one skipped, 15 warnings**; the result summary confirms each originally failing case passed. |
| Patch application | Clean `git apply --check` against exact committed preimages. |
| Benchmark contents | Parsed JSON values and manifest bytes unchanged; original frozen hashes restored. |
| Primary worktree/index/HEAD | Unchanged by packet preparation; no scratch commits or publication. |

The first full snapshot omitted `main.py` and stopped at collection. The allowlist was corrected with committed `main.py` and `databricks.yml` in new before/after snapshots; initial logs were retained. This was a test-setup error, not a new application repair. Corrected snapshots differ only by the three patch paths.

This uses the verified installed Python 3.12.10 dependency image, not a fresh install or the exact GitHub runner Python 3.12.15 environment. Actual remote CI still needs verification after publication. These 887 historical-runtime tests do not replace the separate 975 Windows / 974 Linux evidence for uncommitted v1.54, nor establish model quality or deployment readiness.

## Proposed action requiring a direct grant

Create one isolated sparse-clone `codex/` branch at the reviewed base, apply and stage only the patch, verify the exact paths/unchanged JSON and use the configured Git author identity for one commit. Recheck the remote base and push that commit as a fast-forward to `main`, without force, then inspect CI for that exact new commit. Stop if the base changed or authentication/protection prevents publication.

The committed workflow contains unit, serving-environment and local-container checks; it has no deployment or image-push job. Publication would trigger that CI, leaving all newer local v1.54 code, historical owner evidence and the separate pending model diagnostic untouched. A green focused-fix run would not qualify every newer uncommitted change.

The owner's Goal explicitly prohibits automatic commits/pushes, so no publication is authorized by preparing this packet. Model-call authorization is a distinct decision and is not implied by CI publication. No manual factual rescoring is needed for these technical results.
