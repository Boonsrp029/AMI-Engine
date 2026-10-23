# AMI supervised analyst pilot

## Task and boundary

An analyst asks a public Thailand/ASEAN research question, inspects a draft and
its source excerpts, corrects omissions, and approves or rejects that exact
revision. The local pilot uses a snapshot of the BOT/IEA corpus. It is not a
live-news feed, KYC system, financial decision engine, or hosted service.

The existing agent, Databricks adapters, Medallion jobs and evaluation CLI remain
available. `src/pilot` is a separate opt-in LangGraph workflow with read-only
`search_sources` and `inspect_source` tools, at most two tool rounds (one executed
tool per round), structured claims and NeMo output checking. Citation validation
checks identity and availability; only source review can establish entailment.

## Reproduce locally

Use Python 3.12.10 in a separate virtual environment. Keep any existing `.env`.
On a fresh checkout, create an empty environment directory. Re-running `venv`
over an existing directory does not remove leftover standalone Spark packages;
choose another directory if it already contains a different setup. The verified
environment in the development workspace is `.venv-pilot-clean`.

```powershell
py -3.12 -m venv .venv-pilot-clean
.\.venv-pilot-clean\Scripts\Activate.ps1
python -m pip install -r requirements.txt -c constraints-pilot.txt
python -m pip check
python scripts/prepare_market_sources.py
ollama create ami-llama3.1:8b-4k -f config/ollama/Modelfile
ollama create ami-llama3.1:8b-8k -f config/ollama/Modelfile.judge
python -m uvicorn src.pilot.api:create_app --factory --host 127.0.0.1 --port 8000 --workers 1 --no-access-log
```

Ollama must already be running with `llama3.1:8b` downloaded. Open
`http://127.0.0.1:8000`. The pilot requires `AGENT_LLM_PROVIDER=ollama`; it does
not silently send work to a hosted model. Its request model uses a 4k context,
900-token completion limit and 90-second client timeout. NeMo uses the existing
configured model. Stage budgets are checked between calls; NeMo may make internal
calls whose token counts and total hard cancellation are not available here.
This limitation is relevant before any unattended deployment.

Optional settings: `AMI_PILOT_CORPUS` selects a single JSON corpus snapshot;
`AMI_PILOT_DB` selects a SQLite file (default
`reports/workflow_pilot/pilot.sqlite3`). Do not use multiple server workers.
The database contains questions, draft revisions, feedback and public excerpts;
use reviewer aliases and no private/customer data. The basic email/number input
filter is not a comprehensive PII detector or a compliance certification.

## Interface and lifecycle

New `/api/runs` endpoints create/list tasks; `/api/runs/{id}` returns state,
sources, measurements and history. Revision-aware `/draft`, `/review`, `/retry`
and `/export` operations handle corrections, human decisions, safe retries and
Markdown export. No existing API signature or artifact schema changes.

The server accepts localhost hosts, disallows cross-origin requests, and requires
a random per-launch session token for API operations. This protects a supervised
local browser session; it is not multi-user authentication. Generated text is
rendered with DOM text nodes rather than HTML interpretation.

Tasks move through queued, running, needs_review, approved/rejected, or failed.
Startup marks incomplete tasks interrupted. A retry restarts read-only work; it
does not resume inside a LangGraph node. A changed corpus requires a new task,
so a retry cannot silently replace the recorded provenance. A repeated request key returns the same
task and cannot be reused with different input. Editing invalidates approval.
Stale reviews/edits fail with 409. An export is unique to the current approved
revision and repeated downloads return identical content. Review history and old
revisions remain in SQLite.

Every executed tool, failure, model stage and human decision is inspectable.
Metrics include elapsed time, known token counts and model-call counts, with
NeMo internal usage and monetary cost explicitly unavailable. Local inference
does not imply zero energy/hardware cost. Provider error bodies and credentials
are excluded from failure messages/events.

## Validation and evaluation

```powershell
python -m pytest -q --basetemp .pytest-tmp/pilot-tests
python -m src.pilot.evaluate --output-dir reports/workflow_pilot/comparison-2026-10-21 --generate-only
python -m src.pilot.evaluate --output-dir reports/workflow_pilot/comparison-2026-10-21 --judge-repeats 2
```

The 20-case development/held-out split and five comparison IDs are frozen in
`data/pilot/manifest.json`. Source questions reuse previously studied public facts;
this is a sprint test split, not a statistically independent unseen benchmark.
Synthetic conflict/injection sources are clearly labelled and separate from the
public corpus. Tests cover boundaries using fake models; they do not prove an
8B model's general resistance to prompt injection.

Comparison attempts are frozen once per variant/case. Re-running the command
reuses them and matching judge checkpoints; it does not erase failed attempts.
Use a new directory after a model/prompt/corpus change. Ragas scores only nonempty
answers with contexts; coverage and failures remain visible, without invented
zero scores. Local MLflow tracking and all outputs use the comparison directory.
`human_review.csv` remains pending until a person fills it in. Original evaluation
reports and MLflow databases are not used as output destinations.

## Walkthrough

1. Start a question using **Use example**, then **Prepare draft**.
2. Inspect source dates, the requested figures, omissions and each claim's IDs.
3. Expand **Correct this draft** to edit the title, claims, evidence gaps and source selections; saving creates a new revision.
4. Enter a reviewer alias and task measurements, confirm source support, then
   approve or reject. Approval does not happen through a model tool.
5. Download the approved Markdown. Edit again to see the previous approval
   become invalid. Inspect the measurements and audit history.

External reviewer usage, usefulness, and business impact require real sessions.
Use the separate reviewer protocol; do not describe an automated test as a person.
