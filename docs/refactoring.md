# Behavior-preserving refactor record

## Baseline and scope

Baseline commit: `9ecebb7db8f569a7cf348efac6a842c68b3afd85` (clean checkout).
The pre-refactor offline suite passed 17 tests with one Unity Catalog Pydantic
deprecation warning. All validation for these passes uses synthetic responses,
mocked clients, and temporary output directories. Existing data, reports,
checkpoints, and MLflow stores must remain untouched.

Dependency manifest SHA-256 values (must remain unchanged):

| Manifest | SHA-256 |
|---|---|
| `requirements.txt` | `9b9866f61485297125d78f9d6a787b801e23b0d92ea2d2032ad1fd803883d1c7` |
| `requirements-serving.txt` | `559077d80389dae7f5fbfbbc1ee0d505e8a3d5940c05061be63b8455369b031d` |

The baseline environment's `pip check` fails: `openai-agents 0.22.0` requires
OpenAI >=3,<4 but OpenAI 1.109.1 is installed; Databricks SDK 0.94.0 and the
older installed vectorsearch package reject installed protobuf 7.36.0. These
pre-existing conflicts are outside this refactor. Do not repair or upgrade
packages while establishing structural parity.

## Inventory and decisions

| Finding | Decision |
|---|---|
| Ragas runner: 328 lines, input capture through MLflow publishing in one function | Extract internal input and artifact helpers, then simplify orchestration. |
| Repeated judge defaults and token settings | Share private resolution helpers while preserving read timing, defaults, and error order. |
| Equivalent source-script whitespace/chunking loops | Share the text algorithm; keep script-specific downloads, limits, checks and serialization. |
| Unused deployment result binding and registration run binding | Remove bindings; retain both SDK call and context manager. |
| Superseded commented NeMo configuration | Remove comments; compare parsed active YAML. |
| `notebooks/01_pyspark_etl.ipynb` | Historical Databricks source text with its own ETL/index path and simulated predictions. Preserve its path and contents; do not execute as parity evidence. |
| `config/agent_config.yaml` | Reference defaults, not a runtime configuration loader. Preserve file and current environment-based runtime behavior; correct README description. |
| `src/evals/evaluate_run.py` and indexer exports | Compatibility interfaces, not dead modules. Retain. |
| Lower-level retriever's formatted context vs graph's plain context | Distinct observable contracts. Preserve both. |
| One-use `VectorSearchSyncManager`, warning filters, legacy typing spellings | No behavior-preserving benefit justifies removal or style churn in these passes. |

### Dependency inventory (no removals or version changes)

`datasets` and `langchain-community` have no direct application imports but are
Ragas requirements. `mcp` constrains a transitive integration and is not evidence
of an implemented MCP feature. `langchain-huggingface` has no application import
and is a removal candidate only after a separate dependency review. PySpark is
used by the ETL job and historical notebook; pypdf by source preparation;
sentence-transformers by local dense retrieval and Ragas embeddings. The
Databricks, LangChain, NeMo, MLflow, OpenAI, pandas, Pydantic, dotenv, YAML, and
pytest declarations support active integrations or tests. Preserve both complete
manifests, including comments and constraints.

## Behavior contracts and parity evidence

- **CLI/environment:** retain arguments, defaults, help text, import paths, and
  process > Databricks env file > general env file precedence. CLI local mode
  still selects local dataset and SQLite tracking before evaluator import.
- **Graph/retrieval:** retain state keys, prompts and structured schema, node
  order, citation order, no-context short circuit, fail-closed errors, ranking
  and ties, dense cache key, SDK arguments, and both context representations.
- **Evaluation inputs:** retain aliases, normalization, validation order and
  messages, JSON field order/encoding/indentation, live call counts, frozen
  dataset/count checks, and input replacement timing.
- **Checkpoints:** hash rows before evidence-page annotation, retain judge
  identity and prompt version, filenames, fresh-run suffix, JSONL order,
  score bounds/tolerance, and resume behavior. Resume without frozen inputs
  still runs the agent; every case still emits its scoring progress message.
- **Reporting/tracking:** retain CSV column and row order, metric order and
  calculations, temporary artifact basename, MLflow experiment/run names,
  parameters, metrics and artifact call order, stdout, return dictionary,
  atomic report replacement and cleanup. A scoring/tracking failure preserves
  the previously published report.
- **Serving/indexing:** retain public classes/functions, DataFrame/dict/sequence
  inputs, response column, registration signature/code paths/dependencies, and
  endpoint create/update request shapes and printed messages.
- **Sources:** retain whitespace normalization, overlap, page/chunk IDs,
  synthetic fixture corpus/case/manifest bytes, and direct/module script use.

`tests/fixtures/refactor/evaluation.json` records observations made against the
original evaluator before extraction. Clocks, identifiers and services are
controlled; fixtures use only synthetic data. Text readers normalize native
line endings for portable fixture storage; parity tests also check native
artifact bytes. Existing artifacts have a separate ignored SHA-256 snapshot
under `.pytest-tmp/refactor-baseline/` for the implementation-session audit.

## Pass checklist

- [x] Baseline synthetic fixtures captured and passing before production edits.
- [x] Pass 1: dead bindings/comments removed; configuration and SDK parity checked.
- [x] Pass 2: input preparation extracted; input/failure fixtures unchanged.
- [x] Pass 3: checkpoint/artifact handling extracted; resume/publish fixtures unchanged.
- [x] Pass 4: scoring/configuration helpers extracted; calls/prompts/results unchanged.
- [x] Pass 5: source chunking shared; script outputs and invocation forms unchanged.
- [x] Full offline suite, diff checks, manifest hashes and existing-artifact hashes verified.

### Implementation results, 2026-10-20

| Checkpoint | Validation |
|---|---|
| Before production edits | Original 17 tests plus new parity contracts: 42 passed. |
| Pass 1 | 14 runtime contract tests passed, including create/update SDK requests and active YAML. |
| Pass 2 | 29 evaluator/input/provider checks passed after correcting an extracted variable scope. |
| Pass 3 | 22 evaluation/input checks passed with original artifact and tracking observations. |
| Pass 4 | Full suite: 54 passed. |
| Pass 5 | 10 source checks passed before and after extraction using original synthetic output fixtures. |
| Final integration | 66 passed in 8.68 seconds; `git diff --check` passed. |

The final suite retains the original 17 tests and adds contracts for 13 evaluation
scenarios, including partial checkpoint resume and artifact upload failure.
Those last two observations were captured from the ignored original-code snapshot,
not regenerated from the refactored implementation. The source fixtures capture
the original scripts' outputs against tiny synthetic PDF stand-ins. No live model,
Databricks, source download, or existing MLflow store was used for validation.

All 42 protected existing data/report artifacts matched their pre-refactor hashes.
Both requirements files matched the exact hashes above. `pip check` still reports
the same three baseline conflicts; no packages were installed or changed. The
expanded suite emits the original Unity Catalog warning and an existing MLflow
type-hint warning exposed by newly importing the serving model for its contract
tests. No warning filter was changed.

The public evaluator is still `src/evals/run_ragas.py:run_evaluation`, with the same
signature, return shape and compatibility entry point. Its orchestration function
shrunk from 212 to 99 lines. Internal modules now own input preparation (`inputs`),
checkpoint/report persistence (`artifacts`), and score calculations (`scoring`).
The graph, retrievers, environment loader, ETL, indexer, notebook, CLI, deployment
configuration and dependency manifests have no code changes. The two serving
utilities only lost unused bindings.

To rerun offline validation from the repository root:

```powershell
python -m pytest -q --basetemp .pytest-tmp/refactor-tests
git diff --check
```

The session finished at 22% of the five-hour window used (78% remaining), below
the agreed pause threshold. Changes were saved without a commit or push.

## Separate migration backlog

Dependency conflict repair and serving dependency alignment; dependency removal;
activating YAML configuration; aligning agent/judge/guardrail model defaults;
converting or retiring the historical notebook; retrieval or prompt changes;
new graph architecture; framework/API upgrades; live deployment qualification.
These changes require their own acceptance criteria and are not smuggled into
structural cleanup.

## Usage checkpoint

Check the five-hour usage window before each pass and lengthy validation. At
90% used (10% remaining), save files and a handoff recording completed passes,
checks, unfinished work, and the exact next step, then pause. No automatic
commit or push. Offline parity proves bounded equivalence, not production readiness.
