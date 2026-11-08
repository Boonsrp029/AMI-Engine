# Local release candidate: sequential and explicit-plan concurrent workflow

Status as of 6 November 2026: local release-candidate milestone verified. Exact identities and counts are in [candidate-verification.json](candidate-verification.json); the nine-item evidence audit is retained in reports/workstream-f/rc-2026-11-06/release-candidate-verification.json.

This is a local engineering package. Model quality, independent usefulness, remote CI and production qualification are separate gates. Generation remains held. No publication or deployment is performed by these instructions.

## Build and identify the candidate

The build host requires Git, Docker with a running Linux engine, and Python 3.12.10. Git is not required inside the production image. Use the unchanged requirements/constraints. In a fresh development environment:

```powershell
python -m pip install -r requirements.txt -c constraints-pilot.txt
python -m pip check
python -m scripts.prepare_local_release --output .ci-artifacts/NEW-CANDIDATE --image ami-pilot:local
```

The output directory must be new. The helper captures allowlisted build inputs and a sanitized QA snapshot, Git HEAD/dirty status, content hashes, dependency-manifest hashes, revision label, full Docker recipe log, immutable image inspection and installed-package inventory/pip check. A dirty revision needs its source manifest; HEAD alone is insufficient. Keep the QA context hash alongside the image identity because host-side test helpers are not baked into the production image.

The intended recipe is Dockerfile.pilot, not a source-overlay Dockerfile. Normal builds may reuse compiler/package layers. Inspect docker-build.txt: CACHED means cache reuse, not a fresh installation. A deliberate cache-free build must separately retain actual install logs and exact resolved versions; a failed offline cache miss is not an application failure. Capture the resolved base digest from the build log. Do not change package versions to make the build pass.

The build context excludes credentials, owner databases, reports, corpora, virtual environments and Git metadata. Source/configuration and the backup helper are copied explicitly; the Ollama Modelfile is included. Credential-shaped content or private configuration filenames stop preparation. These are bounded checks, not a general secrets guarantee. Never supply secrets via build arguments or copy them into source/configuration.

## Default sequential application prerequisites

The image runs as UID/GID 10001. Provide a prepared JSON corpus read-only at /data/market_chunks.json and writable durable storage at /state; SQLite defaults to /state/pilot.sqlite3. Preserve corpus/source hashes separately from database backup. The local Ollama model must already exist: ami-llama3.1:8b-4k, with its approved digest/settings. The historical local qualification pin was SHA256 `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`, context 4096, completion limit 900, temperature 0. This candidate did not probe or qualify a current model server; reconfirm the approved digest before any separately authorized real generation. No automatic model download or inference is authorized.

For an owner-started local session, set AMI_PILOT_CORPUS_FILE to the absolute prepared corpus path, AMI_PILOT_IMAGE to the reviewed image tag or immutable ID, and use:

```powershell
docker compose -f compose.pilot.yml up -d --no-build
```

Compose binds only localhost, uses a read-only root filesystem/corpus, drops capabilities, disables privilege escalation and preserves state in its named volume. The model route is host.docker.internal:11434; Linux uses the declared host-gateway mapping. /health is liveness; /ready must report unavailable model/storage/runtime truthfully. A 503 does not mean an answer-quality check failed, and a 200 does not prove factual quality.

The default browser remains sequential. Programmatic concurrent execution uses the explicit Plan/run_stored_plan contract and trusted spawn-compatible operation/composition/safety callbacks. It is not enabled merely by selecting an environment variable. Production callback/model wiring needs its applicable design and generation grant. The package includes A/B/C/E interfaces; packaging does not automatically activate browser concurrent submission or configure an executor.

## Offline qualification commands

```powershell
python -m pytest -q tests/test_release_context.py
python scripts/check_linux_container.py --image ami-pilot:local --output .ci-artifacts/NEW-LINUX
python scripts/smoke_subtasks_container.py --image ami-pilot:local --qa .ci-artifacts/NEW-CANDIDATE/qa --output .ci-artifacts/NEW-CONCURRENT
python scripts/smoke_pilot_container.py --image ami-pilot:local --output .ci-artifacts/NEW-SEQUENTIAL
```

Linux runs the integrated suite with networking disabled after matching image source/config hashes. Concurrent smoke imports application code from /app and trusted D callbacks from read-only QA fixtures. It uses barriers to prove overlap, validates ordered aggregation, uses real SQLite review/export rules and verifies cached synthetic export bytes in a second container. Model/safety callbacks are fixed test doubles: logical callback counts are not actual provider calls or safety-quality evidence. Stale and empty approvals/exports must reject.

Sequential smoke checks non-root startup, unavailable-model readiness, invalid-input redaction and persistent restart with zero-call scope rejection. Locally, --review-snapshot may select an explicitly authorized verified backup mounted read-only and restored into disposable state. This preserves historical cached approved exports without creating owner decisions. Never send owner backups to CI. Both smokes remove only their unique disposable resources.

D owns integrated Windows reliability verification. Reuse its exact-source result only after comparing every relevant source/test/config hash; F-only tests are separate. Do not add overlapping targeted counts to the full suite. New integrated runtime changes require D coordination and a fresh qualified snapshot.

## Recovery and rollback

Before changing a real local state volume, explicitly create and verify a backup using scripts/pilot_backup.py. Retain previous image ID, corpus/configuration identities and that backup outside the application volume. Stop the local service without deleting its volume. Select the previous reviewed image with AMI_PILOT_IMAGE and restart with --no-build only if storage compatibility is established. Otherwise restore into a new isolated volume and verify history/export hashes before any switch. Do not overwrite original state or use `down -v` as rollback. No production rollout or timed RTO is established by a disposable restore test.

## Troubleshooting

- Missing Docker Linux pipe: start/repair Docker Desktop and verify engine availability before rerunning a terminal failed build. Never duplicate an active run just because observation timed out.
- Source/image mismatch: rebuild the intended frozen source, including extensionless config files; do not bypass the hash gate.
- Corpus missing: set the absolute corpus path; Compose intentionally refuses creation of an empty bind source.
- Readiness model unavailable: check the approved model's local route/digest manually; do not start generation as a connectivity probe.
- Runtime lease conflict: stop the owner of the database; sequential and programmatic runners must not write as simultaneous whole-request owners.
- Permission denied on state: use correctly owned disposable/named-volume storage, never switch the application to root as a fix.
- Smoke failure: retain stdout/stderr/result files and distinguish fixture errors from runtime defects. Send shared-runtime defects to A; D owns integrated reliability checks.

## Publication actions requiring separate authorization

1. Review the integrated AÃ¢â‚¬â€œF diff, dependency hashes, source/QA manifests, immutable image ID, test results and exclusions. Dirty local evidence is not an exact committed release.
2. Approve the precise files to stage, including shared AÃ¢â‚¬â€œE changes; do not stage unrelated owner artifacts or reports automatically.
3. Authorize creation of the reviewed commit and normal push/PR to the agreed target. No history rewrite.
4. Observe the actual unit, serving-environment and analyst-container jobs for that exact commit. Retain failures and successful artifacts. Remote CI stays pending until those jobs really pass.
5. Authorize image publication, tagging or release publication separately if desired. No registry push is included here.
6. External deployment, real-model qualification, reviewer contact and alerts require their own grants.
