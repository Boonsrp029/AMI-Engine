# Balanced qualification pool v4 — 30 October 2026

**Prepared and frozen; no model generation or quality scores.** This is the successor to the proposed balanced pool in the earlier [coverage audit](qualification-pool-audit-2026-10-30.md). That audit's statements that v4 does not yet exist and that the r06 review is pending describe its earlier checkpoint. The [owner-directed r06 wording change](../pilot/owner-review-v155-2026-10-30.md) and [completed offline-first checks](offline-regressions-v155-2026-10-30.md) are separate evidence; neither authorizes fresh generation.

## Scope and identities

The new specification is `data/pilot/release-2026-10-30-v4/spec.json`, with a byte-identical copy of the existing publisher source lock alongside it. The ignored frozen package is `data/external/release_qualification_2026_10_30_v4/frozen-v4/`.

- Package manifest SHA256: `36ab8c6f99cbd88385914a12f62139b16c99d76702db337dfe1bb7e0dcad5ce1`.
- Unchanged application/policy generator SHA256: `1a7e4e1e42cbd76c54ebacedd6ec11fae33d12691a1558386be104002ac009f0`.
- Unchanged public retrieval-corpus SHA256: `a98d0c4c9d6b131360213f77f58d8a70ef16ab7b0302f68758a30243d269b20e`.

The model, dependencies, prompts, retrieval ranking, public APIs and approval/export lifecycle are unchanged. New data preparation has not been used to tune the application. Full publisher snapshots remain local and ignored; this document paraphrases their topics rather than redistributing source passages.

## Coverage and continuity

| Case category | Count | Required gate, unchanged |
|---|---:|---|
| Answerable | 10 | At least 9 complete, supported answers |
| Partial | 2 | Both preserve supported partial information |
| Missing | 4 | All four properly abstain |
| Conflict | 2 | Both explicitly distinguish conflicting evidence |
| Adversarial | 2 | Both handle embedded instructions safely |

Zero critical unsupported or wrong-scope/date/unit/scenario claims remain required. Technical failures cannot be credited as proper abstentions.

| Answerable source family | v2 | v3 | v4 |
|---|---:|---:|---:|
| BOT | 5 | 3 | 5 |
| BOI | 2 | 0 | 2 |
| IEA | 3 | 7 | 3 |

The sixteen retained cases r07–r22 are identical as complete frozen case records, including references, checks and resolved evidence locators. The four unused IEA additions r23–r26 remain in the untouched v3 package; they are not deleted or overwritten. New r27–r30 supply two BOT and two BOI cases:

| New case | Topic | Principal distinction |
|---|---|---|
| r27 | December public spending and expenditure drivers | Year-on-year comparison, transfer exclusions, government versus state-enterprise spending |
| r28 | December merchandise imports and composition | Seasonally adjusted value, excluding gold, component-specific origins, aggregate versus consumer-goods movements |
| r29 | Two sectors' BOI applications | Value ranking versus project count, pledged baht amounts versus realized investment |
| r30 | Semiconductor policy and government investment estimate | Policy action versus a conditional forward-looking estimate and its horizon |

The preflight case records p01/p02 and **all** retrieval corpus files are byte-identical to v3. This is a case-selection and provenance change, not a retrieval-data change. The actual manifest/case roster and new continuation metadata identify the live pool; the inherited v3 continuation error is not copied forward as the current roster.

## Source verification and limits

All five publisher files were copied from the existing verified snapshots with matching SHA256 values. Preparation disabled socket connections and the preparer's download function; zero downloads occurred. Every evidence anchor resolves to its pinned normalized source unit at the stored character offsets. BOI source pages were rendered and visually checked at PDF indexes 0 and 1 / reader-facing PDF pages 1 and 2. Poppler reported Symbol/ArialUnicode font warnings; the English passages used here were legible in the rendered pages. The original PDF bytes are unchanged. BOT evidence uses HTML paragraph locators, not invented PDF page numbers.

New question text was screened against the prior public pilot specifications and case files. Distinctive fact signatures were also checked. A digital-sector investment-value candidate overlapped retained r11 and was discarded **before** freeze or generation; r29 instead uses previously unqueried sector comparisons. No replacement was selected from known model success or failure. Within the searched workspace reports, 28 retained attempt files were inspected and none concerned r07–r22. This observation is limited to those report files, not activity outside this workspace.

Fresh questions do not establish statistical independence. The same documents, source families and retrieval corpus were already known. The source author knows the new references; this is not a blinded authoring protocol or a claim that the facts were absent from pretraining. Earlier metadata inspection exposed existing synthetic input text, as disclosed in the prior coverage audit. All references and new source assessments are **assistant-authored and awaiting human adjudication**. No model quality, owner acceptance or external usefulness is inferred from freezing.

## Reproduction and validation

Use the existing preparer with the new specification and a **new** output directory. It refuses to overwrite a frozen or partial package. Supply the five publisher files under the specification's dataset root from the pinned snapshots; verify the source lock before running. This preparation used only verified local copies and disabled downloads. The package reader validates the manifest and its contents independently of the authoring helper.

```powershell
.\.venv-release-check\Scripts\python.exe scripts/prepare_release_evaluation.py --spec data/pilot/release-2026-10-30-v4/spec.json --output data/external/release_qualification_2026_10_30_v4/reproduction-check
.\.venv-release-check\Scripts\python.exe -m pytest -q tests/test_release_preparation.py tests/test_release_qualification.py
```

The preparation/qualification checks passed **18 tests**. Actual package verification also confirmed category counts, source mix, retained case equality, corpus hashes, anchor offsets and unchanged generator identity. A second preparation into a separate directory reproduced all **11 package files byte-for-byte**, including the manifest, with downloads and socket connections disabled. The preceding full offline suite passed 1,017 tests with 15 existing warnings; it was not repeated for this data-only addition. No model, NeMo or Ragas execution is part of either result. The local evidence is under `reports/workflow_pilot/production-readiness-2026-10-27/resume-v32/`.

## Next gates and human review

The owner's latest instruction requests offline work before granting fresh r03–r05 regressions. Those offline checks are complete; the proposed generation allowance remains **unactivated**. No preflight or twenty-case run is authorized by creating v4.

If generation is later authorized, first inspect each consumed regression against source/completeness criteria. Future preflight evidence must bind the final v4 package hash as well as the unchanged application/model identity; a pass on an earlier package is not transferable. Fresh qualification needs a separate concrete protocol and direct budget grant. Do not tune on the new held-out outputs and then report them as unseen successes.

No repeat manual scoring is requested for identical historical outputs. New generated answers need human source/completeness adjudication before owner acceptance; stored drafts still need exact-revision approval before export. Independent reviewer task sessions remain a separate requirement. This frozen pool does not establish portfolio completion, production qualification or permission to publish/deploy.
