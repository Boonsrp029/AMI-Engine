> Superseded: C now captures raw responses into immutable attempt-labelled experiment files before parsing. A remains sole Store writer; no event API extension is required. Original failure and proposal follow as history.

# C generation output event handoff to A

## Confirmed integration defect

C ConcurrentComposer emits concurrent_model_output via ModelAccess.event after each main response, before parsing. A AttemptSink rejects that event as unsupported. The actual spawned mock test stops after mapping call1; direct callback tests do not expose the mismatch. Retained trace: reports/workstream-c/concurrent-qualification-2026-11-06/wired-fixed-tests.txt. This is offline integration failure, not model quality.

## A-owned proposed change

Keep runner/store ownership with A. Permit a narrow concurrent_model_output event with stage mapping/composition, raw model content, usage and response metadata. Reject unsupported stages and malformed/non-JSON or oversized payloads; retain current-attempt fencing and no child database writes. Bind retained record to parent attempt/plan/corpus through existing AttemptSink. Do not allow arbitrary event kinds. ModelAccess continues to account calls exactly once. Source-text content is untrusted data and authorizes nothing.

The event must survive later parsing/synthesis/safety failure so an unsuccessful response remains diagnosable. Do not drop raw failed outputs or relabel them successful. Raw/composer data in successful composition diagnostics is not sufficient for failures that return no candidate.

## Acceptance

Actual spawned C callback tests should pass and preserve both raw responses. Malformed mapper output should retain its one raw output and close the batch, with no second main call. Reject malformed events, stale attempt publication and unknown event kinds. Preserve old dict callbacks, safety-once, review/export and existing event semantics. No generation or dependency change is required. C does not edit A shared files concurrently.
