# Reproduce and package the local analyst application

Use Python 3.12.10 and the unchanged requirements/constraints. Install into a fresh environment, run `pip check`, and run `python -m pytest -q --basetemp .pytest-tmp/release`. `pytest.ini` selects maintained offline tests and excludes archived copies and live SDK command modules from discovery. `.venv-release-check` is the newly installed qualification environment; it is separate from the existing working environment.

## Windows/local launch

```powershell
$env:AGENT_LLM_PROVIDER='ollama'
$env:AMI_PILOT_DB='reports/workflow_pilot/local-release.sqlite3'
.\.venv-release-check\Scripts\python.exe -m src.pilot.launch
```

Start the existing Ollama model first; prepare/pin the corpus using the existing source instructions. The launcher preserves one worker, no access logs and localhost binding. Its Windows Selector event-loop bootstrap is the controlled mitigation for the recorded native cleanup error; Linux is unchanged. Existing approved databases are not the default output destination for this launch.

`/health` retains the old liveness/corpus response. New `/ready` checks an actual SQLite write transaction rolled back without touching rows, and a bounded Ollama `/api/tags` request for the configured model. It returns 503 when either prerequisite is unavailable, without inference, credential output or task-history changes. A 200 response establishes metadata/storage readiness only: it does not establish inference quality, completed grounding checks or production security.

## Container (local build and no-inference recovery smoke verified)

```powershell
$env:AMI_PILOT_CORPUS_FILE=(Resolve-Path data/external/market_sources/prepared/market_chunks.json).Path
docker compose --env-file .env.example -f compose.pilot.yml config --quiet
docker compose --env-file .env.example -f compose.pilot.yml up --build -d
```

The service publishes only to localhost, uses a non-root user, mounts the corpus read-only, and keeps SQLite in the `pilot-state` volume. The root filesystem is read-only with a temporary cache filesystem; capabilities are dropped. Source/config and the existing dependency set are copied explicitly; secrets, data, reports and virtual environments are excluded from the build context. No credential-bearing `.env` is passed to the service. Model access uses host Ollama, not a cloud fallback. Auxiliary model/cache prerequisites still require a live inference/guardrail smoke before qualification.

Do not delete the state volume when stopping a real review session. The isolated smoke command below creates/removes its own uniquely named disposable volume and never uses the owner review database:

```powershell
docker build -f Dockerfile.pilot -t ami-pilot:qualification .
python scripts/smoke_pilot_container.py --image ami-pilot:qualification --output reports/workflow_pilot/production-readiness-2026-10-27/container-smoke
```

This no-inference smoke verifies non-root startup, loaded synthetic corpus, truthful readiness failure when Ollama is unavailable, persistent task history, actual worker scope rejection with zero model calls, and interruption recovery after restart. It creates no human decision or approved export. An optional `--review-snapshot <verified-backup-directory>` restores into its own disposable state volume and checks all existing cached exports byte-for-byte. The original review database/backup remains unchanged. The [recovery utility](recovery.md) is copied into the analyst image; local and container restoration passed, while target deployment restoration, live inference, safety, quality and sustained-load gates remain separate.

The image records a supplied source revision label; an uncommitted local image must not be attributed solely to HEAD. CI supplies its exact GitHub revision and retains image inspection/smoke evidence. Base tags and dependency downloads are not evidence of an immutable build by themselves; preserve actual image/base digests and resolver output when the build runs.

Docker Desktop is now working (29.9.2); its pipe is inaccessible to this task's restricted shell without an approved local Docker command. The earlier missing-engine diagnosis no longer describes current state. Actual local images were built and the recovery smoke passed. The full existing dependency set produces an approximately 9.59 GB image because Linux resolution includes Torch/CUDA dependencies; no package/version was removed to reduce it. A separate lean runtime proposal requires deployment/dependency evidence.

`scripts/check_linux_container.py --image <exact-image-tag> --output <new-directory>` prepares a sanitized test snapshot, refuses credential-shaped source data, checks packaged source/config hashes and runs offline tests with networking disabled. The final local image `ami-pilot:qualification-a4c2334b2465513c` passed **502 tests with one Windows-only skip**; Windows passed 503. Its image ID and complete context manifest are retained in `resume-v2/image-id-v6.txt` and `build-context-v6.json`. The original Linux cancellation failure and failed smoke-parser check are retained alongside their successful repair checks.

A metadata-only container request reached host Ollama and found the configured model. The current digest was recorded; it does not prove that earlier runs used that same digest. Future final-quality qualification should pin/verify model digests as well as model names/settings. No inference was made by this connectivity check. Real container generation/guardrail/cache prerequisites remain a separate bounded gate.

Rebuild and repeat after newer source changes. The CI container job is prepared but no remote GitHub run was initiated. No automatic commit/push, image publication or external deployment is included.

The v1.36 image ID is `sha256:c41b5402837e175c637ccddd07727785f5783e4bebcee90bfd6ef349229e48a5`. Its no-inference recovery smoke again preserved all four cached approved exports and blocked empty d06. This local dirty-checkout artifact does not establish remote CI or real container inference.
