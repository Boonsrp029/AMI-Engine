# Pilot dependency repair — 2026-10-21

## Scope and evidence

The refactor baseline remains commit `25ce2ed`. This is a separate dependency
repair for the new analyst pilot. The existing `.venv` was not modified.
Python **3.12.10**, a new `.venv-pilot-clean`, and the application manifest plus
`constraints-pilot.txt` were used for a real installation, not just a resolver
simulation. `pip check` reports **No broken requirements found**. The initial
clean-environment suite passed **82 tests** (three warnings); later pilot tests
are recorded in the validation report. No GitHub run or container build is
claimed by this local result.

## Necessary version changes

| Package | Previously installed | Selected | Reason |
|---|---|---|---|
| openai | 1.109.1 | 2.45.0 | Satisfies the declared application OpenAI 2 range and the compatible Agents release. |
| openai-agents | 0.22.0 | 0.19.3 | 0.22 requires OpenAI 3; the NeMo integration requires OpenAI below 3. |
| instructor | 1.3.2 | 1.16.0 | Old Instructor requires OpenAI below 2. This compatible release preserves baseline aiohttp. |
| jiter | 0.16.0 | 0.14.0 | Instructor's supported range is below 0.15. |
| protobuf | 7.36.0 | 5.29.5 | Common supported version for the Databricks and Google/gRPC dependencies. |
| googleapis-common-protos | 1.75.1 | 1.75.0 | Avoids the newer protobuf minimum. |
| grpcio-status | 1.83.0 | 1.71.2 | Compatible with protobuf 5. |

FastAPI 0.141.1, Uvicorn 0.52.1 and httpx 0.28.1 are now direct dependencies
because the pilot imports them. They were already installed at those versions.
All other baseline installed versions are retained where applicable by the
constraints file. Constraints select versions without forcing unused optional
packages to be installed. The machine-readable change inventory is
`dependency-changes.json`.

The initial unconstrained resolver selected older Unity Catalog packages. A
subsequent full resolution proved that the original `unitycatalog-langchain
0.4.0`, `unitycatalog-ai 0.4.0` and `unitycatalog-client 0.4.1` can be retained.
Those unnecessary downgrades were reverted; `pip check` and all 88 tests pass
after alignment. Thus the final runtime version changes are the seven rows
above. The virtual environment uses Python's seeded pip 25.0.1, compared with
26.2.1 in the original environment; this bootstrap-tool difference is recorded
separately and is not an application dependency repair.

The live comparison was collected before that final Unity Catalog alignment;
[package snapshots](evidence/package-versions.json) record both environments.
The local generation, NeMo, OpenAI/Instructor and Ragas scoring versions are
unchanged by the alignment. Original evaluation artifacts were preserved.

The serving manifest shares OpenAI 2.45.0, Agents 0.19.3 and protobuf 5.29.5.
Its resolver check succeeds under the shared constraints. This is package
resolution evidence, not a verified Unity Catalog registration or serving run.
The existing model registration API remains unchanged; reproduce the serving
environment with the shared constraints before deployment.

## Spark namespace isolation

The selected Databricks integration installs **databricks-connect 17.0.10** via
the Unity Catalog Databricks extra. It supplies a `pyspark` import namespace.
Installing standalone `pyspark==4.2.0` alongside it caused the distribution
metadata and imported Spark implementation to disagree. `pip check` alone
cannot detect this file ownership collision.

Standalone PySpark 4.2.0 therefore moves unchanged to `requirements-etl.txt`.
Do not install that file in the application environment. Databricks jobs retain
their workspace-provided Spark/Delta runtime. Local standalone Spark needs its
own environment and Java; this pilot did not run a standalone Spark job.

```powershell
py -3.12 -m venv .venv-etl
.\.venv-etl\Scripts\python.exe -m pip install -r requirements-etl.txt
```

## Reproduce the application check

```powershell
py -3.12 -m venv .venv-pilot-clean
.\.venv-pilot-clean\Scripts\python.exe -m pip install -r requirements.txt -c constraints-pilot.txt
.\.venv-pilot-clean\Scripts\python.exe -m pip check
.\.venv-pilot-clean\Scripts\python.exe -m pytest -q --basetemp .pytest-tmp/pilot
.\.venv-pilot-clean\Scripts\python.exe -m pip install --dry-run --ignore-installed -r requirements-serving.txt -c constraints-pilot.txt
```

Local install reports and logs are under ignored `.pilot-work/`. The constraints
were validated on Windows; GitHub Actions now applies the same constraints and
runs `pip check`, but an actual Linux CI run remains required after the owner
pushes this change. No automatic commit or push was performed.
