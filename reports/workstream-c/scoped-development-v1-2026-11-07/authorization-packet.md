# Scoped two-case development v1 — authorization pending

Prepared 7 November 2026. **No new generation ran and no grant file exists.**

Contract SHA-256:
`f5eb8a4de2eecf482746e5e513525ceeef4e37fc951b8d1e43506c2780391405`.
See [development-contract.json](development-contract.json) and the frozen
[source-review protocol](source-review-protocol.md).

A's activation is applied: the development entry now explicitly selects the
scoped callback only for `cq-scoped-composition-v1`. Old contracts retain the old
callback. The checked adapter preserves declared/executed identities when reserving
preparation time. No public API, dependency or sequential default changed.

## Proposed authorization

| Item | Frozen scope |
|---|---|
| Sequence | cq-p01 once; cq-p02 once only after all first-case gates pass |
| Main calls | At most four per case; **eight total**; currently one mapper plus one composer for a supported answer |
| Safety | At most one NeMo wrapper invocation per case; **two total**; internal request/token usage remains incompletely measured |
| Time | **180 seconds per case**, owned operator interval including pin checks and child CLI startup/preparation, retrieval, generation, safety and persistence |
| Retry/warmup | **None**; stop at first declared failure and retain unattempted cases |
| Model | Local `ami-llama3.1:8b-4k`, digest `6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23` |
| Settings | Context 4,096; completion 900; temperature 0; serialized local inference |
| Output | Fresh `actual-development-v1/` beside this packet; does not exist yet |

The expected model identity will be checked before actual requests; no model
change/download is authorized. There is no Ragas, hosted inference, Databricks
work, CQ1 run, stored approval/export, publication, deployment or reviewer contact.

## Predeclared request scopes

| Case/branch | Caller-declared exact original-question scope |
|---|---|
| cq-p01 / s01 | observed electricity demand in Canada in 2016 |
| cq-p01 / s02 | projected electricity demand in Japan through 2036 |
| cq-p02 / s01 | wind generation in Denmark in 2015 |
| cq-p02 / s02 | Denmark retail electricity prices yesterday |

The questions, synthetic source corpus and bindings are unchanged consumed
development material. These scope labels are application/planning data, not source
facts or model-generated gap answers. Membership is checked; their interpretation
must remain reviewable. Sidecars retain their caller-declaration provenance.

All **106 execution inputs** are hash pinned, including current runtime/config,
unchanged dependency declarations, scope files, tokenizer, source corpora, operator
and source protocol. Conservative mapper context budgets are **1,706 / 1,616**,
including framing and 900 completion reservations. New server-observed counts,
grammar performance and model quality are unverified.

## Gates and preserved history

Require correct raw and final source support/completeness, scope/number/period/
measure/forecast binding, appropriate title and gaps, final safety and persisted
review-pending revision. Keep raw mapper/composer, application disclosures,
fallback and editorial correction separate. Source fallback cannot hide raw
omissions for this development gate. No editorial rescue or automatic approval.

Technical success alone cannot advance the batch. An assistant source assessment
must bind the exact first result SHA and pass before cq-p02. A failure closes the
allowance; no retry or unused-call reuse. Inspect source/identity drift and retain
normally finished, failed, interrupted and unattempted outcomes honestly.

The original r07, nineteen reserved original cases, previous `and` failure and owner
judgments remain unchanged. CQ1 is still **0/20 attempted** with unchanged category
thresholds; no larger-run permission is bundled. Its old compiler still needs
proper scoped-case sidecars before a later qualification contract can be prepared.

## Offline evidence

- Applied combined revision: **1,731 Windows offline tests passed, 14 warnings**.
- Activated entry, scoped callback and legacy/CLI checks: **61 passed**.
- Operator: **four mocked-process checks passed**, including refusal without a
  grant, once-only execution, timeout/stop and exhausted-preparation handling.
- CLI and operator default verification both pass with **no inference**.
- No library version/constraint change or current production qualification claim.

At 10% remaining in either standing usage window, checkpoint and pause rather than
start another case. An interrupted active attempt must be retained and not retried.
Process termination does not establish backend cancellation; report unknown usage.

## Human review

Execution authorization is separate from source/wording acceptance. New assessable
drafts require owner judgment before being called owner-accepted. Stored approval/
export still needs approval of the exact revision and is outside this allowance.
No repeated numerical scoring of historical technical failures is requested.

After a direct grant, the operator records the actual reply/reference in a new
grant file and runs only the selected case:

```powershell
.venv-release-check/Scripts/python.exe reports/workstream-c/scoped-development-v1-2026-11-07/run_case.py --contract-sha256 f5eb8a4de2eecf482746e5e513525ceeef4e37fc951b8d1e43506c2780391405 --execute --grant <new-direct-user-grant.json> --case cq-p01
```

The source gate controls whether the same command may later select cq-p02.
The contract's frozen as-of date is 7 November 2026; date/source changes require
re-freezing and a new matching grant rather than reusing this one.
