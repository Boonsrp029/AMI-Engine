# Serving dependency reproduction boundary

A fresh `.venv-release-serving` on Windows Python 3.12.10 installed the existing `requirements-serving.txt` with existing `constraints-pilot.txt`. `pip check` passed. Its 183 distributions are a subset of the fresh application's 205 distributions, with **zero common version differences**. No requirement or constraint file was edited, and no package was removed from the project.

Offline imports of the registry wrapper, legacy graph, Databricks retrieval adapter, indexer and NeMo runner succeeded. A fixed graph response preserved the wrapper's `response` DataFrame contract. These checks performed no inference, Databricks request or registration. Evidence is in ignored `reports/workflow_pilot/production-readiness-2026-10-27/serving-*.json` and installation/check logs.

An initial unconstrained resolver began backtracking and was interrupted; its log is retained. The successful installation explicitly supplied the repository's baseline constraints to preserve shared versions. This is the reproducible command for the isolated local check:

```powershell
python -m pip install -r requirements-serving.txt -c constraints-pilot.txt
python -m pip check
python -m scripts.smoke_serving_environment --output reports/workflow_pilot/NEW-OUTPUT/serving-environment.json
```

The registration utility now supplies the existing serving pins plus the unchanged baseline constraints to MLflow. MLflow copies the resolved constraints into the saved artifact and rewrites the environment reference to relative `-c constraints.txt`; the artifact does not depend on the owner's absolute workspace path. Missing constraints fail before registry/experiment calls. The model name, signature, code paths, wrapper response and normal console output are unchanged.

An actual local `save_model` test, with networking forbidden, compared every normalized constraint against the repository baseline. It copied the artifact and loaded it in a fresh isolated interpreter from another directory, using its bundled `src`/`config` rather than repository imports. A fixed graph response verified the `response` DataFrame without model inference, registration or an endpoint request. The saved artifact intentionally has no input example in this test to prevent MLflow from invoking the real graph; the registration entry point retains its original example. The initial sandbox temporary-directory failure and the successful workspace-local retest are retained under `resume-v1/` in the evidence directory.

This proves local artifact portability and environment packaging, not successful resolution by the actual Databricks serving builder. Keep that live gate open until the authorized target verifies it.

A Linux CI job for the constrained install and fixed-response smoke is prepared. It has not run remotely for the release revision. Linux native dependencies, exact registered artifact/version/signature, reachable inference provider, serving authorization and Databricks runtime remain separate target-environment gates. The legacy registered graph is still distinct from the analyst application's persistent review lifecycle.
