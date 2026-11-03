# Reproduce and package the local analyst application

## Current source-only test image — v1.69, 3 November 2026

`ami-pilot:source-cues-v169`, immutable image ID `sha256:934746ec47dcc64a1e85e28aa4ae717160dbdf54fd0f28805c03e94b07c8dd7f`, copies three runtime files over the verified v1.68 full-recipe image. Current Linux checks pass 1,293 tests plus one platform skip; disposable non-root restoration/restart preserves all four cached exports. Windows passes 1,294 tests. Existing dependency versions and source/config/model prerequisites remain unchanged.

[Evidence and limits](unit-source-cues-v169-2026-11-03.md): this is a source overlay, not a new full recipe, fresh installation, actual inference, remote CI or running Desktop-service upgrade. The actual v1.68 qualification failure remains retained. The reduced v1.69 diagnostic needs a new grant; no twenty-case run is proposed.

## Earlier full-recipe verification — v1.68, 3 November 2026

The unchanged Dockerfile directly built `ami-pilot:recipe-v168-final`, image `sha256:7cbe33bc7d099528b707b738088f3d3a639dd87c94edbcfe24db4e159aa8760d`. [Current evidence](full-recipe-v168-2026-11-03.md): 1,275 Linux tests plus one skip, clean dependency check, all 221 installed versions unchanged and disposable non-root restoration/restart preserving four cached exports. Context `c40d14fb0fbbb0fbb2263d867576d14756b4c7e77c7b29e3c6dab31503457227` includes the exact extensionless Modelfile after the hash gate caught its omission from the first temporary context.

Installation layers were cached; normal build mode used registry metadata. A preceding network-disabled build lacked a compatible compiler-install cache and failed before assembly. This is not cache-free reproduction, real inference, current remote CI or deployment. The [actual v1.68 batch](qualification-v168-findings-2026-11-03.md) later passed both preflights and stopped at its first held-out case; that allowance is closed. Future inference needs a new bounded protocol/grant after repair. The Desktop application was not upgraded.

## Earlier source overlay — v1.68, 3 November 2026

The source-only overlay is `ami-pilot:missing-gap-v168`, immutable ID `sha256:77088b7f16b122c0740682bad7ddf5c07a1e5751d93b48e78baee16761ae84e2`. The current sanitized test snapshot passes 1,275 Linux tests plus one platform skip; Windows passes 1,276 tests. Disposable non-root restoration/restart preserved four cached exports. Recovery preceded only synthetic-fixture edits; runtime hashes remain identical. Dependencies are unchanged and reused, not rebuilt. See the [repair evidence](missing-gap-contract-v168-2026-11-03.md).

The Docker engine was stopped on resumption; after starting and verifying it, the offline Linux check passed. There is no v1.68 inference, remote CI, fresh dependency build or upgrade of the running Desktop analyst service. The previous actual v1.67 qualification stopped at p02; its allowance is closed. The [new proposal](fresh-qualification-v168-proposal-2026-11-03.md) is unexecuted and requires a new grant.

## Earlier offline image — v1.67, 2 November 2026

The current tested source overlay is `ami-pilot:composer-v167`, immutable image ID `sha256:26874ad9179b60a0fcf2be5d77d29303d6e649696070830a581d815b5f5ec10c`. It passes 1,256 Linux tests plus one skip and disposable recovery preserving four cached exports. Dependencies are reused unchanged. The side conversation retains 1,257 Windows passes; this is not a fresh dependency build or current remote CI.

The [host-Python qualification](qualification-v167-preflight-findings-2026-11-02.md) stopped at the second preflight. It does not establish actual container inference or fresh quality. The running Desktop service remains unchanged. Earlier image checkpoints below remain historical.

## Earlier offline image — v1.66, retained checkpoint

The locally tested source overlay is `ami-pilot:attributed-prose-v166-final`, immutable image ID `sha256:96eb379f92fac52aee01a6618e1f707c7d6867380627255319d098215e3b68a0`. The [attributed-prose repair](source-attributed-prose-2026-11-02.md) passes 1,253 Windows tests, 1,252 Linux tests plus one skip, clean dependencies and disposable non-root recovery preserving four cached exports. The earlier intermediate layout/image was rejected during engineering inspection and is not the qualified final artifact.

This reuses unchanged dependency layers, not a fresh dependency build or exact-release remote CI. The [actual r05 v1.66 workflow](r05-prose-v166-findings-2026-11-02.md) ran in host Python and passed real final NeMo, with [owner source/wording acceptance](../pilot/owner-acceptance-r05-v166-2026-11-02.md) now recorded; no stored approval/export or fresh quality claim follows. It is not evidence of inference inside this container; the earlier saved-response replay uses a fake safety result. The running Desktop service remains v1.60. Do not infer current release identity from inherited image labels, upgrade the service or replace its storage automatically.

## Earlier v1.65 evidence — retained checkpoint

The current locally tested source-overlay image is **`ami-pilot:source-excerpt-v165`**, immutable image ID **`sha256:29fb0e531cb63f76f079a9fa00e3e34c87d6f12fd15f0ac82d50abe25036ca73`**. The [source-excerpt record](source-excerpt-presentation-2026-11-02.md) documents 1,238 Windows tests, 1,237 Linux tests with one skip, clean dependencies and non-root disposable restart/restoration preserving four cached exports. This overlay reuses verified dependency layers; it is not a fresh dependency installation or exact-release remote CI result. Its inherited image revision label is not current release identity: use the immutable digest and recorded source hashes.

The [actual v1.65 diagnostic pair](consumed-v165-findings-2026-11-02.md) ran through local Python, not inside this container. It does not establish real container generation, guardrail/cache prerequisites, backend cancellation or sustained-load performance. Owner acceptance of the new exact outputs remains pending.

The repaired **running Docker Desktop service remains v1.60**; it was not upgraded during diagnostics. Follow the [Desktop startup record](docker-desktop-startup-2026-11-01.md) for that installed instance. Do not substitute a newer tag or recreate its storage merely to match this guide. A future chosen image needs its own launch review and storage-preservation checks.

For a fresh checkout, use the reproducible build/launch commands below with the unchanged requirements and explicit corpus/model prerequisites. A local tag is not available automatically on another machine. Keep a fresh setup, the current test overlay, the existing Desktop instance and an externally qualified release distinct.

## Historical image and validation checkpoints

The dated “latest/current” labels below refer to their recorded checkpoints, not the current artifact described above. Retained commands and general setup instructions follow these records; no new build or deployment is implied by this documentation refresh.

> Latest local image: `ami-pilot:literal-v155`, ID `sha256:a991e3fe9ed993dc2a720c42f845417e132e361459b4a9e7dcd0062a107cee93`, context `deb8b83661513e3bf7930f5b26f1803de60de27c5c5c343e6b29554f5955e07d`. The [literal-comparison change](literal-comparison-v155-2026-10-30.md) passes 1,017 Windows / 1,016 Linux tests, clean dependency checks with all 221 image versions unchanged, and no-inference restart/restoration preserving four cached exports. Dependencies were cached; no actual inference, new remote CI or deployment is established.

> Published CI checkpoint: the owner-authorized [focused byte fix](ci-publication-2026-10-30.md) at `e433bd5` passed remote unit, serving-environment and analyst-container jobs. That commit excludes the newer local v1.54 source, so it does not establish remote CI for the image described next.

> Latest full-recipe check: `ami-pilot:recipe-v154`, image ID `sha256:2c12bd3f489da15a0f708d1cbf1fc0bbd54e5ab7aacbfeb2e266f4f1d4f48b52`, builds the current source using the unchanged `Dockerfile.pilot`. [Recorded evidence](full-recipe-v154-2026-10-30.md): 974 Linux tests plus one skip, clean dependency check, all 221 installed package versions identical to the verified overlay, and no-inference restoration/restart preserving four cached exports. Dependency layers were reused from cache; this is not a fresh install, actual inference, remote CI or production qualification. Earlier overlay checkpoints below remain historical.

> Current completeness overlay: `ami-pilot:completeness-v154`, image ID `sha256:27dc411a1932b35d44652df7a20150c6b9462396e962f859210300755e6c5ae5`, context `16a8c6dcb0bc86d7c90ddd60f5f6bee42a58e39102384edadab71668a5d54431`. The [requested-context repair](completeness-v154-2026-10-30.md) passes 975 Windows / 974 Linux tests, one Linux skip and container restart/restoration with four cached exports unchanged. Build and Linux-test networking were disabled; dependencies/model settings remain unchanged. This is a local source overlay, not a fresh dependency build, actual inference, remote CI rerun or production qualification.

> Current worker overlay: `ami-pilot:worker-output-v1`, image ID `sha256:80d78550bd20333dfdb0ba06a2717b6c0f644c56083d59fbf7e47756ade997e3`, context `28b54ad3faa367d1b814dcdc28c723ba96be3d2da2ec2dc9c86e46aa43533faf`. It adds [worker console isolation](worker-console-2026-10-30.md) to the verified logging image with no dependency or model-setting changes. Final checks pass 956 Windows / 955 Linux tests, one Linux skip; two native privacy cases and non-root container restoration/restart preserve four cached exports without inference or new decisions. This is a local source overlay, not a fresh dependency rebuild, remote CI rerun or deployment qualification.

> Current launcher overlay: `ami-pilot:server-logging-v1`, image ID `sha256:c8f39d1bd148bb0189acdf4639ff836d658bd8fa0eef7ca108ac790239266b56`, context `c2218bc5d2bff5e27a28a9b5bd9f0ede41ea1bbae751ed8f60d0283c308f119c`. It adds [allowlisted server logging](server-logging-2026-10-30.md) to the verified helper image with networking disabled and unchanged dependencies. Windows/Linux checks pass 954/953 plus one Linux skip; non-root startup/restart/recovery preserves four cached exports without inference or new decisions. This remains a local source overlay, not a fresh dependency build, remote CI rerun or deployment qualification.

> Latest backup-helper overlay: `ami-pilot:backup-freshness-v2`, image ID `sha256:565f3a2199e7ddedb2abb3d83ce2dac7d110fa3301b39e6ecf1adf86df9e49ae`, context `db81c395f5ca51e84094a25ffd6fe457681d8e6657218d5e8e18a2aa665d54e6`. It adds the [freshness command](backup-freshness-2026-10-30.md) to the security image below without application/model/dependency changes. Final Windows/Linux results are 945/944 plus one Linux skip. Packaged fresh/stale checks and no-inference restoration of the one-time backup pass. This is a local helper overlay, not a fresh dependency build, scheduled backup service or remote qualification.

> Latest local security overlay: `ami-pilot:validation-redaction-v1`, image ID `sha256:064ad0c4cbab5666e99f8e837c5cb90a424f82e278f447e1675467f7dedfbd37`, source context `60b005d4e909062f91e1aa0006c16faa72e20e3f2e52d7c62c11fdc3b6b6be3a`. The [validation-response repair](validation-redaction-2026-10-30.md) passes 920 Windows / 919 Linux tests, one Linux skip and the no-inference container redaction/restart/recovery check with four cached exports unchanged. It overlays source on verified unchanged dependencies with build networking disabled; it is not a fresh dependency rebuild, remote CI rerun or actual inference qualification. Earlier image checkpoints below remain historical evidence.

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

`scripts/check_linux_container.py --image <exact-image-tag> --output <new-directory>` prepares a sanitized test snapshot, refuses credential-shaped source data, checks packaged source/config hashes and runs offline tests with networking disabled. The current local image `ami-pilot:qualification-4278d28a19803272` passed **825 tests with one Windows-only skip**; Windows passed 826. Its image ID and complete context manifest are retained in `resume-v10/container-smoke-v22/image-inspect.json` and `build-context-v22.json`. The original Linux cancellation failure and failed smoke-parser check are retained alongside their successful repair checks.

A metadata-only container request reached host Ollama and found the configured model. The current digest was recorded; it does not prove that earlier runs used that same digest. Future final-quality qualification should pin/verify model digests as well as model names/settings. No inference was made by this connectivity check. Real container generation/guardrail/cache prerequisites remain a separate bounded gate.

Rebuild and repeat after newer source changes. The CI container job is prepared but no remote GitHub run was initiated. No automatic commit/push, image publication or external deployment is included.

The v1.36 image ID is `sha256:c41b5402837e175c637ccddd07727785f5783e4bebcee90bfd6ef349229e48a5`. Its no-inference recovery smoke again preserved all four cached approved exports and blocked empty d06. This local dirty-checkout artifact does not establish remote CI or real container inference.

On 28 October the daemon was initially stopped. The first build failed before building; that log is retained. Starting the verified installed Docker Desktop restored engine 29.9.2. The same sanitized v1.40 snapshot then built successfully and passed Linux/no-inference recovery checks. No image was published or externally deployed. See [current evidence](context-and-retrieval-2026-10-28.md).

The later v1.43 image also passed the isolated no-inference recovery check, preserving all four cached exports and blocking empty d06. See [evidence-role/comparison repair](evidence-roles-2026-10-28.md). No real container inference or remote CI is established by these checks.

The later [HTTP intake repair](request-intake-2026-10-28.md) passed the current image tests and actual chunked rejection check; recovery evidence is in container-smoke-v10 and container-body-http-v1.

Historical v1.46 image/recovery evidence remains in resume-v4/linux-suite-v12 and container-smoke-v12. Image ID `sha256:a8edac04886405d4546d544fc12f15ed696c6c21404ee4d36919e8f0f59474fd`; build context `31eaf5d21672bf11af67905d8c3204e0df5e26d4d335630e532ed38b07dd2530`.

Historical v1.47 evidence remains in resume-v5/linux-suite-v14 and container-smoke-v14. Image ID `sha256:06031a4412d686314c87397dfe37868ba075df89051ba779f77ba836f2192c52`; build context `0a29a0fafae4471743bba3fc614882a76a098913fa30e6cc952e97c5438a2e46`.

Historical v1.48 evidence remains in resume-v6/linux-suite-v15 and container-smoke-v15. Image ID `sha256:a5e6f453be55bc2f21bc54fd6f52a3ce29ec4f4af1d7c19bc8bf4416132d7bc3`; build context `74b75212101c45eb34e4bcf7af0f08234fb89bee7ddf116ecb6ed1d2319f4967`.

Historical v1.49 evidence is in resume-v8/linux-suite-v17 and container-smoke-v17. Image ID `sha256:8d7f8e42937f14ac5a28ab1347903b7c3e7faa6977ec705d376a49cdc6871593`; build context `f1e6e6826fa4611d527cfc28b910d308402d4bff305b3445ce4f38b5b1180833`. Recovery preserves all four exact approved exports and keeps empty d06 blocked. See [mapped-answer repair](mapped-answer-alignment-2026-10-28.md). Actual container inference, quality and remote CI remain unqualified.

Historical v1.50 evidence is in resume-v9/linux-suite-v18 and container-smoke-v18. Image ID `sha256:46717c8b7f3047861cf5daab42ccc7bc50b6a62f54b3a32e9aa771789e333603`; build context `8b9d2b87bec170a6299c4b1751b98d3e49388e3bb70b6ce50152f08667c965d2`. The normal-network build reused dependency layers; initial engine/cache permission and network-disabled build failures are retained. Recovery preserves all four exact cached exports using a read-only backup and disposable storage. See [quantity-slot repair](quantity-slots-2026-10-28.md). No actual model generation, container inference qualification, remote CI or deployment is established by this repair.

Historical v1.51 evidence is in resume-v10/linux-suite-v22 and container-smoke-v22. Image ID `sha256:943289b4621b5594898d79d336fb8678e2cbf8be4600275ff68cde7da7fc5d5e`; context `4278d28a19803272520c4463a4d22810d764a27558e11e1a495c3800d494da80`. Docker was initially stopped; the CLI start and subsequent build succeeded. Intermediate source/test checkpoints remain retained. Recovery preserves four cached exports with no inference or approval. See [entity/count repair](entity-count-coverage-2026-10-29.md); actual container inference, quality and remote CI remain unqualified.

Current v1.53 uses a clearly labeled source overlay on those verified dependencies: `ami-pilot:qualification-v153-overlay`, ID `sha256:cb4d56bb6daf2d9210cf33567238670c5415f3725412c3ea6e92f3009958e6f2`, source context `8a37574125067080c124ccab6d79b2542b7c26d79642e6e515284addb0844b31`. Actual Linux tests pass 887 plus one skip; Windows passes 888. No-inference recovery again preserves four exports and blocks empty d06. A fresh network-disabled full build failed at package installation without cached layers; that failure remains in resume-v12. The overlay is not a fresh dependency rebuild. See [request-context repair](composition-request-context-2026-10-29.md); inference, quality, remote CI and deployment remain unqualified.

On 30 October the existing v1.53 image was reused for diagnostic-only harness checks: **899 Linux tests plus one Windows-only skip** passed with networking disabled and current application hashes verified; Windows passed900. No runtime image rebuild or recovery rerun was needed because application/configuration/dependencies were unchanged. Docker was initially stopped; the installed CLI started it successfully. Separately, [remote CI at 11a3599](ci-observation-2026-10-30.md) passed its analyst-image build/synthetic smoke and serving-environment jobs, while unit pytest failed. This is actual remote packaging evidence for that commit, not a green overall pipeline or actual model inference. New diagnostic-harness changes remain unpushed.
