# Missing-evidence contract repair — v1.68, 3 November 2026

**Offline engineering checks passed; actual model quality remains unverified.** The previous [v1.67 batch](qualification-v167-preflight-findings-2026-11-02.md) remains failed at p02, with zero held-out cases attempted and its allowance closed. No additional inference was used during this repair.

## Failure and focused change

The p02 mapper selected missing evidence but copied the instruction example's generic “requested dated observation” into a field that downstream validation required to occur in the question. The decoder allowed a free string. This was a schema/instruction mismatch, before composition or NeMo; the recorded completion showed no timeout or GPU-memory failure.

The workflow now opts into a question-bound missing-state branch. Its required gap is a literal copy of the supplied request anchor and its required evidence list is empty. Partial components retain exact unanswered fragments and supported evidence; conflicting components retain their distinct state and evidence requirements. Invalid responses are rejected, never silently filled or repaired. The instruction example supplies an explicit synthetic question/request and matching gap. Mapping is requested-evidence-v44, prompt analyst-pilot-v1.68; the private source-selection wire remains v1. The v1.67 composer coverage change is retained unchanged.

The older decoder default and legacy callers remain compatible. Public Draft/API, model digest/settings, dependencies, retrieval and approval/export controls remain unchanged. A private successor controller now exits nonzero and closes its allowance on worker/process/identity/budget failure, rather than relying on printed status alone. The controller frozen with the failed batch is untouched.

## Validation and limits

| Evidence | Result | What it establishes |
|---|---|---|
| Full Windows suite | **1,276 passed**, 15 warnings | Current offline application contracts |
| Full Linux suite, networking disabled | **1,275 passed, one platform skip**, 15 warnings | Current sanitized source context against the existing dependency image |
| New private controller suite | **32 passed** | Grant/admission/stop rules and nonzero failure exit, including a synthetic subprocess |
| Dependency check | No broken requirements | Current Windows environment consistency; versions unchanged |
| Disposable non-root restoration/restart | Passed; four cached export hashes preserved | Existing review history survives recovery without new decisions or generation |
| Retained-response replay, sockets blocked | Bad placeholder rejects at parsing; separate literal-only counterfactual returns empty-claims abstention/full-question gap | Diagnosis and contract behavior, **not** a real-model pass |
| Integrity | 96 protected historical/owner/source paths and 20 retained actual-run paths match | Historical evidence unchanged |

The initial full suites found four obsolete synthetic-fixture failures, corrected by explicitly supplying required question anchors. Negative fixtures and validators were not relaxed. Failed logs are retained. On resumption, one Linux launch could not reach the stopped Docker engine; it did not execute tests. After the engine was started and verified, the new offline run passed. These observations are not remote CI.

The source-only image is `ami-pilot:missing-gap-v168`, immutable ID `sha256:77088b7f16b122c0740682bad7ddf5c07a1e5751d93b48e78baee16761ae84e2`, based on the verified v1.67 image. Dependencies were reused, not rebuilt or upgraded. The current full Linux test snapshot includes the corrected test fixtures. Recovery preceded those fixture-only edits; runtime hashes are unchanged. The running Desktop analyst service was not upgraded.

## Next gate and human review

A [new bounded proposal](fresh-qualification-v168-proposal-2026-11-03.md) is prepared. It needs a new direct grant because the previous allowance closed at its technical failure. Both preflights must pass before the unchanged reserved twenty-case set can run. No raw-composer financial improvement is claimed: the previous preflights did not exercise its financial checklist.

No manual rescoring is needed for the technical p02 defect or these synthetic tests. New assessable outputs require source/wording adjudication before being called owner-accepted. Stored-revision approval/export and independent reviewer sessions remain separate human actions. Portfolio completion, exact-release remote CI and actual scoped Databricks production qualification remain incomplete.

Local ignored evidence: `reports/workflow_pilot/production-readiness-2026-10-27/resume-v107/` contains baseline/change scope, failed and final test logs, image/recovery records, zero-call replay and integrity checks; `resume-v108/` contains the new unexecuted protocol and review packet. No Ragas, hosted inference, new model calls, approval/export, commit/push, deployment or reviewer contact occurred.
