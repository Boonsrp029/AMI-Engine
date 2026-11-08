# Concurrent unit-local composition — offline implementation

This implements the instruction-only portion of `composition-unit-scope-proposal.md` after the closed v6 failure. No further actual generation is authorized or performed. The earlier proposal and failed outputs remain historical records.

## Current behavior and deliberate change

The concurrent callback previously reused the sequential instruction, including several specialized rules unrelated to many concurrent requests. Actual v6 selected both requested source spans but repeated an unsupported whole-question relative comparison in each unit. Its strict numeric guard rejected before safety or persistence.

C now owns a private `src/pilot/subtasks/_composition_instruction.py` contract, version `cq-composer-v2-unit-local`. It tells the model to answer each unit independently, use the global request only as task context, report observations/projections side by side, and avoid inventing level differences from rates or comparing incompatible measures/periods. Applicable completeness, count/value distinctions, negation, causal, scope, source-instruction and JSON rules remain. The callback records this version in diagnostics.

This is an explicit private instruction change. It does not prove factual support or change the response schema, selected evidence, source-literal cues, free-prose field, validators, omission fallback, final safety, call ceiling or stored approval/export lifecycle. The sequential `engine.DRAFT_INSTRUCTION` still references the unchanged shared instruction. No library, dependency, model, context/completion limit, public API, schema, retrieval or architecture changes are included.

## Offline verification

The initial targeted check had 61 passes and one test-expectation mismatch for an existing empty tuple. The assertion was corrected without changing serialization or behavior. The corrected run passes **62 tests** (`unit-local-targeted-v2.txt`), including private instruction wiring, unchanged sequential prompt, accepted free paraphrase, unchanged fallback disclosure, and rejection of invalid nonempty claims without repair or safety calls.

The new `scripts/_concurrent_composer_capture.py` accepts pinned contract, mapper-response and corpus hashes. It replays one frozen mapper and either captures the composer schema/messages or validates a fixed composer response. It creates no model/safety client, writes no Store data and cannot establish safety or approval. Logical access slots are reported separately from its zero actual requests. **Seven tests** pass (`concurrent-composer-capture-tests.txt`), covering capture, valid prose, invalid number/unit rejection and all three input-identity changes.

`unit-local-composer-v2/` retains the exact new input/native request, identity manifest, old failed-response replay and tokenizer audit. The retained v6 composer still rejects unchanged. Its human-message payload and schema are unchanged; the system instruction changes. For this frozen request only, message content shrinks from **904 to 671 tokens**. Including 256 framing allowance and 900 completion reserve yields **1,827/4,096 tokens**. Format grammar remains separately counted at457tokens. These are offline counts, not observed latency, cost or model-quality improvements.

`unit-local-full.txt` records **1,583 passes,14warnings,463.42seconds**, terminal exit zero, for the integrated application/capture suite. The later-added diagnostic controller has **six separate mocked checks**, recorded in `concurrent-composer-controller-tests.txt`; these six are not included in the1583total. No actual generation is implied by either run.

## Next execution preparation

Prepare a **single composer-only diagnostic** over the retained correct mapper output before spending another full workflow. It must freeze current code/messages/schema/native body/model digest, new output location, one-request/no-retry limits, and a bounded lightweight service plus network-blocked offline validation. The existing stdlib `_mapper_transport` can supply request inspection/one-shot local service mechanics; its inspect mode already confirms this frozen body's options without importing the engine or making a request.

The concurrent capture helper is not interchangeable with the old sequential `_composer_capture` graph harness. Do not reuse that old validation path or its grant. A concurrent-specific controller now exists at `scripts/concurrent_composer_check.py`: default inspection is offline; execution needs a new direct grant, an exclusive output directory, pinned request/source files, one lightweight service request and socket-blocked validation. It retains timeout/failure evidence without retry or automatic workflow advancement. The6mockedchecks cover inspect/refusal, identity drift, missing user reference, timeout/once-only behavior, successful fixed-response validation and invalid prose rejection. Model use remains zero in these checks.

The initial protocol preparation was rejected offline because it omitted the service-helper pin. It remains as `protocol.json`; no service started. The corrected `unit-local-composer-v2/protocol-v2.json` pins119projectinputs plus6request artifacts and passes current inspection. SHA-256: `8da1a51cd9239cd54ec5617dff9d7859ddd39b419cd0d743823eb59d24811b37`. A fresh subprocess validates the explicitly synthetic service fixture with socket connections/DNS blocked; its transport flags are fixtures, not real model-identity or generation evidence. No authorization file or actual output directory exists. See the separate authorization packet for the exact single-request budget.

If new raw prose passes technical checks, assess source support and completeness before proposing a conditional workflow. Owner source/wording review applies to new assessable outputs. Hard failures need no manual rescoring. CQ1 and the nineteen original reserved cases remain untouched/unattempted. Actual quality Goal, post-NeMo publication, owner acceptance, independent usefulness and production qualification remain incomplete.
