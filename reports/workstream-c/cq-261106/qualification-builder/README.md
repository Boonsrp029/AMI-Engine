# Offline future CQ1 contract builder

This preparation tool **does not execute a model, create an execution grant or start a qualification attempt**. It is outside the currently frozen v7 runtime package; that package remains unchanged. No real CQ1 execution contract has been produced because current passing development evidence is absent.

## Inputs and refusal conditions

`build_qualification.py` requires the exact development contract identity, retained result/start/source-assessment records for both cases, the predeclared CQ1 manifest identity and reviewed plan identity, a fresh contract destination, a sibling fresh execution-output location and an explicit as-of date.

It refuses a failed/closed batch, missing/failed/stale source records, mismatched current code/configuration/model/settings, pool/plan/corpus drift and existing destinations. The live development-lineage validator checks the completed chain. No grant-shaped object is constructed by the real compiler for validation.

The compiled metadata preserves the exact twenty-case roster and thresholds: 9/10 answerable, 2/2 partial, 4/4 missing, 2/2 conflict, 2/2 injection and zero critical errors. It declares at most 80 main calls and 20 NeMo invocations, 180 seconds per case, no warmups/retries, and the existing stop/source-review/owner-adjudication rules. These limits describe a **future proposal**, not authorization. Reference findings are not copied into the model-facing case dictionaries or roster.

Future compilation must still be reviewed, independently authorized and reverified before any attempt. Passing compilation proves consistent metadata, not semantic support, model quality, human usefulness or production readiness. The v7 two-case grant, if later given, would not authorize CQ1.

## Verification

`../cq1-builder-tests-v2.txt`: **9 synthetic checks passed**. Tests cover positive linked compilation, missing/failed/closed development evidence, runtime drift, frozen pool/plan/corpus identity and preservation of existing files. The one synthetic in-memory grant used by a test is explicitly labeled test-only; the compiler creates no grants.

The standalone CLI was also invoked against the **real current v7 package**. It refused with:

> Two passing current development results/assessments are missing

No real qualification contract, output directory, grant or attempt was created. `preparation-audit.json` and `real-refusal.txt` retain this result. This is intended fail-closed behavior, not a quality success. The real v7 development grant is still absent.

## Scoped extension — 7 November 2026

The owner has explicitly kept current generation held. The compiler is outside the
106 frozen development inputs; these preparation-only edits do not alter the held
contract, application runtime, model settings or dependencies.

For `cq-scoped-composition-v1` development, supply both
`--scope-manifest-path` and `--expected-scopes-sha256`. The scope manifest has:

```json
{
  "version": "cq1-requested-scopes-v1",
  "pool_manifest_sha256": "<predeclared CQ1 manifest SHA>",
  "plans_sha256": "<reviewed plan SHA>",
  "case_ids": ["<the exact twenty IDs in roster order>"],
  "cases": {"<case-id>": {"path": "<relative scope sidecar>", "sha256": "<file SHA>"}}
}
```

Every sidecar must remain inside the manifest directory, hash-match and validate
as `DisclosureScopes` against that case's plan, whole question, corpus and exact
component/branch bindings. This verifies provenance/membership, not interpretation
or source support. Scope declarations require their own review; source findings
and reference answers are never copied into model-facing cases.

The compiler validates pinned development sidecars, carries and pins all twenty
qualification sidecars, and emits a separate qualification authorization label.
It normalizes corpus locators to their verified absolute paths. Missing scope
manifests, changed roster/order/identities, scope drift/path escape and attempts to
silently change legacy development into scoped composition are refused.

**20 distinct offline checks passed across two targeted runs:** the previous nine
legacy checks, ten scoped validation checks and one additional full synthetic
scoped compilation check. `scoped-compiler-tests.txt` and
`scoped-positive-compilation.txt` retain the results. These are synthetic metadata
tests, not actual-model qualification, human review or a grant.

The real current held development contract was checked again. Compilation refused
because **two passing current development results/assessments are missing**;
`scoped-real-refusal.txt` preserves the error. No real CQ1 contract/output was made.
Actual scope annotations for the real twenty-case pool are not fabricated by this
extension and must be frozen before any later compilation/authorization.

Current development execution still needs the owner to explicitly reopen
generation and grant its bounded purpose. Do not repeat the permission request
while held. The larger qualification remains behind its passing-development,
frozen-scope, source-adjudication and separate authorization gates.

Reproduce the synthetic checks from the repository root:

```powershell
.venv-release-check/Scripts/python.exe -m pytest -q reports/workstream-c/concurrent-qualification-2026-11-06/qualification-builder/test_builder.py --basetemp .pytest-tmp/cq1-builder-review
```

The builder CLI's `--help` documents the required compilation inputs. Use the actual captured Bangkok date when preparing a future execution contract. Do not compile from test records or substitute a different pool without an explicit new predeclaration. The current source remains bound to v7 contract `63aadb35493d68c78e2988c8e675ffb5ee5769ae9ff0a92e8daaf6a6da8ed92f`; its model execution awaits the existing authorization question.
