# Qualification model identity

The release supervisor now records the local Ollama model's content digest as well as its tag, settings, code, policy and corpus identities. Ollama's metadata-only [`GET /api/tags`](https://docs.ollama.com/api/tags) returns the model name and digest. This endpoint does not generate an answer.

`python -m src.pilot.qualify --stage verify ...` retains its offline verification behavior: it makes no model or metadata request. Explicit generation stages inspect the fixed local endpoint, pin one full digest before creating the batch directory, and pass it to each owned worker. Optional `--expected-model-digest <64-lowercase-hex>` requires that predeclared digest to match. No model, library version, context/completion limit or application API changes.

Workers verify the pin before and after each workflow call and final NeMo invocation, and again before accepting the completed attempt. The parent also verifies the returned full identity. Metadata requests use fixed loopback, no proxies or redirects, a two-second timeout and a one-megabyte response cap. Missing/duplicate tags, malformed digests, transport failures and changed content fail explicitly; there is no inference retry. A raw result captured before a post-call mismatch remains in the failure evidence.

These checks are necessary consistency observations, not transactional attestation by the inference server. An administrator swapping a model and restoring its tag between observations is outside their proof. Do not modify model tags during qualification. Internal NeMo wire requests/tokens remain incompletely measured; the existing per-case process deadline still bounds the whole attempt.

## Preflight evidence

A passed assessment alone cannot unlock held-out execution. Each actual preflight must have the identical full generator/model/package identity. Its process-result sidecar must also match the assessment's new `process_result_sha256`, reference the unchanged attempt hash, report the expected outcome, confirm identity verification, and show a clean exit without timeout. An answer saved before native-process failure cannot satisfy this gate.

Historical assessments and outputs are preserved. They lack the new model-content/process proof and are not retroactively upgraded. Existing direct `run_attempt()` diagnostics can still be unpinned for compatibility, but unpinned results cannot unlock release qualification. The default supervisor generation path always pins.

This pass has synthetic metadata/gate tests. Passing them does not establish model quality, owner acceptance, a successful fresh evaluation, or historical model identity. Actual generation remains behind a new bounded authorization following the retained diagnostic failure.
