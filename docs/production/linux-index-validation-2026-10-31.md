# Linux validation after Docker recovery — 31 October 2026

After the owner confirmed Docker was ready, a local engine probe succeeded (29.9.2). The prepared indexer overlay built with network access disabled using the existing backup-deadline image. Its additional filesystem layer replaces only the indexer; all base layers are preserved. This is not a fresh dependency installation.

Image identity: `sha256:28249bbc4fd8fbe45a7cab0889131dc34fe4f0b75d6bc0461c0d85c4e685a4ac` (`ami-pilot:index-contract-v1`). The full offline Linux suite passed **1,039 tests, one Windows-only skip and 15 existing warnings** in 50.56 seconds. The preceding Windows suite passed **1,040 tests with 15 existing warnings**; it was not rerun because runtime source hashes were unchanged.

This completes the previously pending Linux checks for the [resource override repair](staging-overrides-2026-10-31.md) and [existing-index contract guard](existing-index-contract-2026-10-31.md). Their earlier Docker-unavailable statements describe the retained failed attempts, not the current outcome. Tests use mocked Databricks clients and fixed model responses; they do not establish compatibility with a real workspace index or model quality.

The test runner verified image/source parity for `src` and `config`, mounted a sanitized source context read-only, disabled network access, and did not mount credentials or owner reports. Context identity: `89199acb84614806cec858621b81a9a1f28809a39fc1c3355e1dda7c1a270803`.

A separate localhost smoke restored the existing owner-history snapshot, mounted read-only, into a disposable volume. Non-root startup, truthful unavailable-model readiness, rejected-input redaction, interrupted-task recovery after restart and all four cached approved exports passed. Cached UTF-8 export bytes match the previous hashes. Empty-claim export remained blocked. No model calls or new human decisions occurred; the original snapshot was unchanged and the container/volume were removed.

Evidence and image metadata are in ignored `reports/workflow_pilot/production-readiness-2026-10-27/resume-v43/`. Earlier failed Docker checks remain untouched. No commit, push, external deployment, Ragas or live Databricks request was performed. The frozen v1.55 generator and evaluation packages remain unchanged.

The Docker availability blocker is cleared. Fresh r03–r05 generation, qualification of the frozen twenty-case pool, independent reviewer use, intended-release remote CI and production deployment/operations gates remain pending. The owner's Docker confirmation is not a model-test or deployment grant. No factual human scoring is required for this container validation.
