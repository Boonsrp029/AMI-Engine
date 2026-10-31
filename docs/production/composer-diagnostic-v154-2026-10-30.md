# Proposed r06 composer diagnostic — v1.54

**Historical frozen proposal, subsequently authorized and executed: [failed composer diagnostic](composer-v154-findings-2026-10-30.md). The conditional workflow did not run and this allowance is closed.** The [offline completeness repair](completeness-v154-2026-10-30.md) passes tests and consumed-response replay. This protocol tests actual new behavior; earlier owner acceptance applies only to the historical editorial candidate.

The protocol is `reports/workflow_pilot/production-readiness-2026-10-27/resume-v23/composer-proposal-v154/contract.json`, SHA256 `21c394616cd1c66bc307980a10cbae36981006e7ab8d4ce333c7608b16e1437c`. Expected code/policy identity: `bd45906fa9f625c98c2329169b3005599dc0aeb240345b80c46ac6220779f7b6`. Its current messages/schema, request options, sources, consumed stage records, helper/controller and acceptance criteria are hashed. At preparation the authorization file was deliberately absent; the later direct owner grant was saved separately without changing the frozen contract.

## Scope and budget

1. One local composer request. Its earlier two tool turns and mapper are fixed replays, not new inference. Deadline **95 seconds total**: service at most 60 seconds, offline engine validation at most 30 seconds, orchestration reserve five seconds. No preflight NeMo call.
2. Only if transport, current engine validation and a hash-linked assistant source/completeness assessment all pass: one complete r06 workflow, **180 seconds maximum**, at most four main calls and one NeMo invocation. NeMo internal calls/tokens remain separately reported and incompletely measured.
3. Combined ceiling: **five main calls and one NeMo invocation**. Stop at the first technical/source/completeness failure. No retries, warm-up generation, tuning during the run or reuse of unused allowance.

Use only `ami-llama3.1:8b-4k`, digest `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23`, context 4096, completion 900, temperature 0. Verify identity before/after as the existing transport/controller requires. No hosted inference, Ragas, twenty-case batch, approvals/exports, deployment or reviewer contact is authorized by this proposal. Client termination is not proof of backend cancellation; missing usage is not zero.

## Source and reporting gate

The consumed BOI question asks for the FDI share of 2024 total application value, the source leading by value, and whether Singapore or China had more projects. Keep the original strict development criteria: 73% with its total-value denominator; Singapore with 357.5 billion baht and 43% of FDI application value/context; correctly assigned 305/810 counts and an explicit China-more conclusion. Application values must not become realized investments, and scope/date/scenario cannot be inferred from publication date or the question alone.

Assess raw composer output and projected output separately. Identify extractive substitutions and arithmetic explicitly; they do not prove general semantic support. Inspect whether the value basis is clear, all requested parts are answered and warnings are useful. A failed gate remains failed even if an editorial correction is later accepted.

Save raw/parsed output, selected sources, code/model/prompt/corpus identities, stage attribution, available token usage, timings, finish reasons and failures in new directories. Preflight target: `composer-only-r06-v154`; conditional workflow: `development-v154`. Neither exists until execution. Source assessment must refer to the new outputs and matching hashes; an old passed review cannot open the transition.

## Human checkpoints

A **new direct budget grant** is required before running this proposal. Any technically assessable new generated draft needs owner source/completeness review before calling it owner-accepted. That review is separate from approval of an exact stored revision before export. Independent reviewer usefulness and production rollout acceptance remain later requirements. No repeated manual scoring is requested for technical failures.

Offline protocol inspection and validation rehearsal use zero new model calls. The full Goal remains incomplete regardless of a successful single-case diagnostic; fresh qualification, independent usage, remote CI and deployment/operations gates remain open.
