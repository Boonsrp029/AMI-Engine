# Two-case concurrent development diagnostic — authorization packet

Status: preparation ready; 1,543 offline tests passed with 14 warnings. All91frozen input/source hashes verified after the suite. No generation grant exists. Actual quality remains unverified.

Contract: development-contract-v2.json
Contract SHA-256: `16fc7cb7396496445f26c9f3a5c76c000967a345abfd832eaa693cdcdf16eb08`
Purpose, per-case acceptance and source-review rules: diagnostic-protocol-v1.json

Run cq-p01 once, source-review its exact claims against its frozen synthetic sources, and only if it passes run cq-p02 once. Total ceiling eight main-model calls and two NeMo invocations; each attempt at most180seconds including preparation; zero retries, warmups or extra cases. Keep local inference serialized and at most two retrieval branches concurrent. No hosted inference, Ragas, approval/export, publication or deployment. Stop and close on the first technical/source/coverage/safety/identity/context/budget failure. NeMo internal request/token counts and energy/monetary cost remain unknown unless exposed.

The model remains ami-llama3.1:8b-4k at the pinned digest, temperature0, context4096 and completion900. Mapping prompt cq-mapper-v2 is a concurrent-only contract; no sequential prompt or library version changed. Raw outputs, application extracts/fallback and later editorial changes are separate records. Source reviews gate advancement; owner acceptance remains pending until actually provided.

## Commands

Offline input verification (no metadata/model access):

```powershell
.venv-release-check/Scripts/python.exe -m src.pilot.subtasks.qualify_cli --contract reports/workstream-c/concurrent-qualification-2026-11-06/development-contract-v2.json
```

After applicable explicit authorization only, the operator records the actual user-grant reference in a separate matching grant file. The template with null reference is not a grant. Run one named case with --mode attempt --grant PATH --case cq-p01; record its exact source assessment using --mode assess --assessment PATH before cq-p02. The CLI does not automatically batch or grade sources. A started or failed case cannot be rerun.

Output: actual-development-v1/ beneath this packet directory; no run directory has been created by verification.

## Larger qualification

CQ1 content and plans are predeclared separately (10answerable/2partial/4missing/2conflict/2injection;9/10andfull-passcategory thresholds; zero critical errors). It is a narrow, correlated electricity-domain pool with explicitly synthetic adversarial records. This proposed development grant does not authorize CQ1. A matching immutable larger-phase contract/grant and both source-passing diagnostics are required. Old r07 remains failed/consumed; old nineteen reserved cases remain untouched.

## Human checkpoints

Before execution: applicable purpose/scope/budget grant. After actual assessable diagnostic outputs: owner source/wording review before owner-acceptance claims. Technical failures need engineering diagnosis, not repeated human scoring. Exact stored approval/export and independent reviewer/production qualification are separate.
