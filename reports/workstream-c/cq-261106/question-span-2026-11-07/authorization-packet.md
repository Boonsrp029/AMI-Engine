# One mapper-only diagnostic — authorization pending

Prepared 7 November 2026. **No new generation has run and no new grant exists.**

Protocol: [execution-protocol.json](execution-protocol.json).
SHA-256: `18f0cb6c0081602d17a6870f7ed245b488e6070948a85ad59d9fe562c51ce7dc`.

## Purpose and evidence

The closed v7 batch passed cq-p01, then cq-p02 copied a source sentence into its
question-only partial-gap field. Strict validation stopped it before composition.
The original failure and all results remain unchanged. This is a consumed
synthetic development fixture, not a held-out quality benchmark.

The new concurrent-only mapper selects question positions. The application resolves
those positions to the original text and still runs the existing exact-source and
coverage validators. Valid positions do not establish correct missingness. Test
that remaining semantic uncertainty with one mapper call before spending calls on
a workflow pair. The same model/settings/question/corpus and captured as-of date
(7 November 2026) are retained; no real current-price data is requested externally.

## Frozen scope

| Item | Bound |
|---|---|
| Case | cq-p02 only; wind generation in Denmark in 2015 plus unavailable dated retail electricity prices |
| Model | Local `ami-llama3.1:8b-4k`, digest `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23` |
| Settings | Context 4,096; completion 900; temperature 0; one serialized request |
| Call ceiling | **One mapper call, zero composer calls, zero NeMo invocations** |
| Time | **95-second owned-controller envelope:** service at most 60 seconds, offline validation at most 30, remaining time for preparation/coordination |
| Attempts | Once; no retries, warmups, tuning or replacement cases |
| Source | Pinned local cq-p02 corpus; no new retrieval algorithm or remote data access |
| Output | Fresh `operator-envelope/` and `actual-mapper/` beside this packet; neither exists yet |

`mapper-input.json` freezes schema/messages. `mapper-request-body.json` freezes
the native Ollama request. `mapper-preflight-proposal.json` binds 87 runtime files,
source identity, acceptance criteria and exclusions. The protocol additionally
pins the controller, process envelope, transport and test files. The source must
still match all pins immediately before and after execution.

The exact request's offline message budget is **1,871 tokens**, including a 256
framing reservation and 900 completion reservation. The schema-format count is
1,069 separate tokens, not prompt content. Actual server prompt count and grammar
processing latency remain unverified. See [context audit](mapper-context-audit.json).

## Acceptance and stop rules

1. Require one complete normally finished response from the pinned local model,
   strict current wire, valid source spans and exact original-question positions.
2. Require supported wind share **29%**, total electricity **generation** as its
   denominator, **Denmark**, and **2015** to remain bound together.
3. Require partial status with the actual unanswered request for **Denmark retail
   electricity prices yesterday**. Selecting the known wind fact as a gap fails.
   A valid but semantically wrong question range also fails the source review.
4. Do not invent prices, discard available wind evidence or substitute background.
5. Retain raw response, finish metadata, usage/timing, resolved extracts, errors and
   assessment separately. Parse/technical validity is not semantic acceptance.
6. Stop and close this allowance after this one attempt, whether it passes or
   fails. A passing mapper does not authorize a full workflow or CQ1.

The validator replays the response through the real concurrent callback with all
sockets blocked, intercepting composition before any composer request. Its
composition payload is retained for inspection; it is not a generated brief or a
stored reviewable revision. No fallback/editorial text can be counted as raw
mapper success. Owner acceptance is never inferred from the engineering result.

## Completed offline preparation

- Previous application integration: **1,657 passed, 14 warnings**. This predates
  the separate diagnostic-controller files; it is not misreported as their full
  integrated run.
- Controller, process-envelope and existing transport checks: **47 passed in
  4.57 seconds**, using mocked services/owned fake processes. Includes the new
  22 controller/envelope checks; these counts overlap the previous suite.
- Separate real Python validation subprocess: fixed explicitly synthetic response
  passed schema/source plumbing with sockets blocked, zero actual model/safety
  calls and semantic assessment still pending. This is not a real-model result.
- Request/body parity, default offline inspection, current runtime pins and
  preservation checks pass. No repeated full suite was needed: application
  runtime is unchanged since its integration check.

The Windows envelope terminates only its owned controller process tree at the
deadline. Server-side cancellation is unproven; a timeout may leave unknown
backend usage. The response and observed request-start count are retained when
available. No monetary/hardware cost measurement is claimed.

## Execution after a direct grant

Only after an explicit reply approving this protocol may the operator create a
grant file containing this exact protocol SHA, the actual user reply and its
conversation reference. No real grant file is included in this packet.

The reviewed operator command is:

```powershell
.venv-release-check/Scripts/python.exe -m scripts.concurrent_mapper_envelope --protocol reports/workstream-c/concurrent-qualification-2026-11-06/question-span-2026-11-07/execution-protocol.json --sha256 18f0cb6c0081602d17a6870f7ed245b488e6070948a85ad59d9fe562c51ce7dc --authorization <new-direct-user-grant.json>
```

## Human review and exclusions

No repeated human scoring is requested for cq-p02's earlier technical failure.
The assistant will inspect the new mapper selection against the explicit source
criteria; any later assessable draft needs its own semantic/wording review.
Existing cq-p01 owner review remains pending, separate from this mapper request.

This grants no workflow pair, CQ1 twenty-case run, Ragas, hosted inference,
Databricks operation, approval/export, publication, deployment or reviewer contact.
The original r07, nineteen reserved cases and all historical judgments stay
unchanged. Stop and checkpoint at the standing usage threshold.
