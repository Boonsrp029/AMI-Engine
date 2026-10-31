# Focused CI fix published and verified — 30 October 2026

**The authorized three-file fix is published, and all three GitHub Actions jobs passed for that exact commit.** This resolves the frozen-byte CI failure on the published runtime. It does not publish or qualify the newer, uncommitted v1.54 application.

| Evidence | Result |
|---|---|
| Published commit | [e433bd5f98519919d65a640cb8652b273ef721fa](https://github.com/Boonsrp029/AMI-Engine/commit/e433bd5f98519919d65a640cb8652b273ef721fa) |
| Parent | `11a3599ec570a5b117fca4b664814dd6d7fc29d8` |
| Reviewed and published tree | `607b950913f5d725f44cbf75be4dcad4dcf7e639` |
| Exact-commit workflow | [Run 41052912363, attempt 1](https://github.com/Boonsrp029/AMI-Engine/actions/runs/41052912363) — completed successfully |
| Unit | [Passed](https://github.com/Boonsrp029/AMI-Engine/actions/runs/41052912363/job/124053135438): dependency installation, `pip check`, and `python -m pytest -q` steps succeeded |
| Serving environment | [Passed](https://github.com/Boonsrp029/AMI-Engine/actions/runs/41052912363/job/124053135409): installation, `pip check`, and serving-environment smoke succeeded |
| Analyst container | [Passed](https://github.com/Boonsrp029/AMI-Engine/actions/runs/41052912363/job/124053135056): image build and non-root startup/readiness/restart smoke succeeded |

## Root cause and exact change

Git's automatic line-ending conversion had stored LF versions of two frozen JSON files while their manifest identified the original CRLF bytes. The three reported tests correctly rejected that mismatch. The fix adds scoped `.gitattributes` rules and restores the original byte representations of `data/pilot/cases.json` and `data/pilot/synthetic_corpus.json` in Git.

Parsed JSON values, questions, split IDs, references, corpus content and manifest bytes are unchanged. No application logic, dependency declaration, workflow, prompt, model setting or owner-review artifact was included. The before/after local historical-source test is recorded separately: three reported failures before, **887 passed / one skipped after**. That local count is not asserted as the remote count; the remote verification inspected job/step success metadata without downloading raw unit logs.

## Authorization and preservation

The owner directly replied **“Authorize focused CI publish.”** The agent created exactly one commit in the prepared isolated `codex/ci-frozen-byte-fix` clone and pushed it normally as a fast-forward to `main`, without force. GitHub's public commit object independently confirmed the parent, full tree and exact three changed paths. The existing published workflow was byte-identical to its parent and contains no deployment or image-push job.

The primary dirty checkout's HEAD, index and application files remained unchanged. It still points to the older local commit while remote main contains the focused fix; no pull, reset, rebase or merge was performed over the local application work. Any subsequent integration/publication of that work requires its own review and authorization. No new model/NeMo call, stored review, approval, export, deployment or reviewer contact occurred.

Raw authorization, preflight, commit/push result, public commit object, published workflow, exact-run/job observations and step verification are retained under ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v26/`. The original failed CI run and local failure artifacts remain historical evidence. The [preparation packet](ci-publication-packet-2026-10-30.md) describes the scoped repair and its earlier local checks.

## Remaining gates

This grant is fulfilled and does not authorize another commit/push or model generation. The proposed v1.54 diagnostic still needs its separate direct grant. The newer local application has [full-recipe packaging evidence](full-recipe-v154-2026-10-30.md), but fresh quality, independent reviewer usage, intended-release exact-commit CI and actual operational/security/Databricks deployment qualification remain open. Neither the portfolio milestone nor the full production Goal is complete.

No additional manual factual review is needed for this technical CI fix. New assessable answers require source/completeness review before owner acceptance; approval/export still applies to the exact stored revision.
