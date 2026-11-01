# Docker Desktop startup repair — 1 November 2026

The local analyst app is running at **http://127.0.0.1:8000** under Compose project `ami-engine-desktop`, container `market-intelligence-agent`.

## Confirmed cause

The obsolete container ran `python main.py` from `/app` and bind-mounted this old folder over the entire application:

`D:\Learning for jobs\Autonomous-Market-Intelligence-Engine-main\Autonomous-Market-Intelligence-Engine-main`

That folder was empty and its recorded Compose file no longer existed. The bind hid the image's application directory. A separate no-network check also confirmed that the old image itself lacked `/app/main.py`, so merely removing the bind would not fix its startup command. An `on-failure` policy repeatedly restarted the failing command.

The maintained browser application starts with `python -m src.pilot.launch --host 0.0.0.0`. The repository's `main.py` is a separate evaluation CLI, not the browser server.

## Applied repair

- Preserved the obsolete container as `market-intelligence-agent-legacy-20261101`, stopped with automatic restart disabled. It remains available for inspection, not normal startup.
- Started the current app from the already validated local image `ami-pilot:source-selection-v160-final`, immutable ID `sha256:47fb831899a71bac4c945ec95f69fe3d95e8d3a8af61d73f2dfc4f5497d87d2c`. No dependencies were installed or changed.
- Added `compose.desktop.yml`, extending the existing analyst configuration. Application code comes from the image; the corpus is mounted read-only as a single file. State persists in the separate `ami-engine-desktop_pilot-state` volume. Existing owner-review files were not imported, moved or overwritten.
- Published port 8000 to localhost only. The existing MLflow container retained its ID and start time.

## Reproducible launch

Run from the current repository root, using a Python interpreter:

```powershell
Set-Location -LiteralPath "D:\Learning for jobs\Autonomous-Market-Intelligence-Engine-main\AMI-Engine"
python -m scripts.start_pilot_desktop --image ami-pilot:source-selection-v160-final --check
python -m scripts.start_pilot_desktop --image ami-pilot:source-selection-v160-final
```

The default corpus is `data/external/market_sources/prepared/market_chunks.json` under that checkout. Use `--corpus "D:\path\to\corpus.json"` for another existing JSON file. The image must already exist locally and use the analyst launcher. The command performs no build, registry pull, evaluation or research request. Starting the service does not approve a draft or authorize additional model tests.

For a future image built from changed source, choose its actual local tag with `--image`. The recorded v1.60 tag qualifies only the source already tested; changing a tag's contents does not preserve that qualification. Fresh-machine installation/build remains covered by the existing release instructions and its own validation.

In Docker Desktop, use the new **ami-engine-desktop** project. The old legacy container is intentionally stopped. Do not remove the `pilot-state` volume when stopping/restarting the app if you want to preserve work created in this instance.

## Missing-source protection

The base pilot configuration now specifies `create_host_path: false`. A direct negative check on this Windows Docker Desktop setup still created a directory for a nonexistent source and returned success for the test's harmless launcher-help command. This flag alone is therefore not claimed as sufficient protection here.

The new host launcher checks for an existing regular JSON file **before invoking Docker**, rejecting missing paths, directories and invalid JSON. It also rejects an image whose default command is the obsolete evaluation entry point. This guards the documented launch path; direct Docker commands and host-file changes after validation remain outside that preflight guarantee. The app's own corpus loading and readiness checks remain necessary.

The empty directory produced by the negative check was verified to be inside the workspace and empty, then removed. No user data or Docker volume was deleted.

## Verification and limits

Observed after the repair:

| Check | Result |
|---|---|
| Container | Running, Docker health `healthy`, zero restarts |
| `/health` | HTTP 200; corpus loaded |
| `/ready` | HTTP 200; storage, runtime and model metadata ready |
| `/` | HTTP 200; browser HTML served |
| Repeated documented startup | Reused the same running container |
| New state | Zero research runs and zero exports |
| MLflow | Existing container ID and start time unchanged |
| Launcher regressions | Five targeted tests passed |
| Real missing-file launcher check | Rejected before Docker; no empty path created |

Readiness uses model metadata only: **no inference, Ragas or NeMo policy check ran**. This fixes local startup; it does not establish answer quality, fresh qualification or production readiness. No human adjudication or approval/export occurred.

Detailed ignored evidence is in `reports/workflow_pilot/production-readiness-2026-10-27/resume-v64/`, including selected non-secret startup metadata, the direct-Compose negative result, launcher checks and final runtime verification.
