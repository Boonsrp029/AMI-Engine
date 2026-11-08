# F reliability handoff from D — Windows release candidate

Date: 6 November 2026. **Current status: fresh integrated F-candidate Windows run PASS: 1,503 tests, terminal exit 0.** The E-baseline reuse and helper results below are historical evidence; see the integrated-candidate section at the end. The initial E-baseline reuse below preceded F's additions; one fresh full suite now covers the integrated candidate. D edited only this handoff and evidence under `reports/workstream-d/release-candidate-2026-11-06/`. F owns subsequent packaging/CI/helpers/tests and all Linux/container/build/smoke evidence.

## Exact snapshot and reuse decision

D independently compared the current checkout to E's retained final manifest, validated the manifest's declared SHA256, and inspected the terminal log/structured record. All **216 files** still match: 68 application-source files, 130 test files, eight configuration files and ten root/CI/package descriptors. No additional source/test/config files were present at D's final check. All four requirements/constraints files match. No protected owner judgments, benchmark artifacts or approved exports were changed by D.

- Tested source manifest SHA256: `4dac813921071be52806d132a95a361e3bb89bae0f8c25114adbd66aca28a4a9`.
- Integrated working source: uncommitted A/B/C/D/E changes over Git HEAD `9b5e665ede286409346de0759c19e6fe5b231b34`. HEAD alone does not identify the dirty tested revision; use the manifest.
- Reused terminal result: **1,499 passed**, zero failures/skips/deselections, **14 existing warnings**, **460.62 seconds**, exit **0** as recorded by E and corroborated by the complete final log.
- This is **E's retained execution**, not a new D full-suite run. Do not describe the reuse as fresh execution or as coverage of later F additions.

D retained byte-identical copies of E's manifest, log and structured verification as `e-tested-source.json`, `e-retained-full-suite.txt` and `e-verification-retained.json`. Their hashes and the comparison are in `source-comparison-before.json` and final `verification.json`.

The original E full run did not generate JUnit. D did not fabricate full-suite XML or individual testcase results. The separate fresh helper run below does have real pytest-generated JUnit.

## Fresh operational-helper validation

E's 216-file manifest excludes Python scripts imported by several tests. D captured those helper hashes before a narrow offline run and compared them afterward. No tested helper changed. Existing libraries were used: **Python 3.12.10**, `.venv-release-check`.

| Check | Terminal result | Artifact in D report directory |
|---|---|---|
| Operational helper tests | **138 passed**, zero failures/skips, one existing FastAPI/Starlette warning, **46.48 seconds**, exit **0** | helpers-pytest.txt |
| Real pytest JUnit | 138 tests, zero failures/errors/skips | helpers-junit.xml |
| Helper identities before/after | No changes | helpers-tested-source.json; verification.json |
| E source comparison after helper run | All 216 unchanged; no new source/test/config files at check | verification.json |
| Whitespace check | Passed; Git line-ending conversion notices only | Terminal check; verification.json |

The 138 tests cover snapshot preparation, mapper transport/capture, desktop startup, backup/restore/freshness/deadlines, synthetic identity provisioning, mapper checks, operational reporting, corpus preparation, evaluation-release preparation and fixed source-policy diagnostic plumbing. **They overlap E's 1,499 tests; do not add the counts.** No actual model, provider, NeMo, Ragas or Databricks request ran.

The exact focused selection/command is retained in commands.txt. D's test session **52336 is terminal exit 0**; no D process remains running. Do not poll/reuse its historical handle or start another Windows full suite merely because a source-identical result was reused.

## F integration boundary and next step

At D's final check there were no later F source/test/config/helper additions. F is preparing them separately. Once added, F should record their exact hashes and focused test results and distinguish them from E's 1,499 baseline. F-owned packaging/CI files were not edited by D. Linux/container/build/smoke, cache-free installation and remote CI are not supplied by this Windows handoff.

If shared application/runtime/test files change, the manifest comparison must be repeated and affected checks rerun; use one combined Windows offline suite when the source no longer matches the accepted baseline. A owns runtime fixes. Do not silently credit the old suite to a changed candidate. A later packaging-only delta requires F's own meaningful tests and explicit evidence scope rather than retroactively changing E's frozen record.

## Qualification boundaries

These checks establish offline engineering reliability for the recorded source. They do not establish actual model correctness, inference-server cancellation/resource release, sustained load, independent usefulness or production operation. No manual factual scoring is needed for synthetic fixtures; real drafts retain source review and exact-revision approval. No dependencies changed, and no generation, publication, commit, push, deployment, alert or reviewer contact was performed.

## Integrated F candidate — fresh full Windows run PASS

F has now integrated its seven owned files, including four additional release-context tests. The E 1,499-pass reuse above is historical baseline, not evidence for those additions. D started exactly one new full Windows offline suite with real JUnit, expected 1,503 tests.

- D session **92659 is terminal exit 0**. The handle is historical; no D test process remains running.
- Directory: `reports/workstream-d/release-candidate-2026-11-06/integrated-final/`.
- Log/JUnit: `pytest.txt`, `junit.xml`.
- Frozen inputs: `source-before.json`, **252 files**, saved manifest byte SHA256 `6796fbe5fa6d1bf4f5563a58600b880700eda811ab55b6dff3267a437cb8b130`. The initial run-start metadata recorded the logical LF-JSON fingerprint `80bd4341ddfca545ab55326fe867eeb6252a918db3ec38def79cce1f4b9d3c77` before Windows newline translation. Both representations and the preserved initial record are explained in hash-format-note.json; all source-entry hashes are unchanged.
- Inputs include src/tests/config/scripts/.github/data-pilot and root execution/dependency/build descriptors. Documentation/report changes are excluded so F can finish its evidence without invalidating an otherwise unchanged execution snapshot.
- `run-start.json` records Python 3.12.10, dirty-base Git HEAD and exact command. Final comparison confirms all 252 input hashes unchanged, no additions/deletions; source-before.json and source-after.json are byte-identical. The new full run passed **1,503 tests, zero failures/errors/skips/deselections, 14 warnings, 464.02 seconds**; real JUnit confirms the count. F owns the parallel Linux/container check; D is not running Docker or repeating helper138.


### Final integrated-candidate acceptance

The fresh Windows result includes all four F release-context tests. The earlier E 1,499-pass reuse and helper138 remain separate historical/subset evidence; do not add their counts. Authoritative final artifacts: `integrated-final/verification.json`, `source-before.json`, `source-after.json`, `pytest.txt`, `junit.xml` and `hash-format-note.json`. Python 3.12.10 and all four dependency manifest hashes remain unchanged. `git diff --check` passes, with line-ending conversion notices only. No runtime failure required an A fix, and D edited no production or F packaging files.

**D integrated Windows handoff is complete for this frozen candidate.** F owns the matching Linux/container/build/smoke evidence and any later packaging delta. Remote CI, real model quality, independent usefulness and production qualification remain separate, unmet by this offline result. No new generation, publication or deployment is authorized.
