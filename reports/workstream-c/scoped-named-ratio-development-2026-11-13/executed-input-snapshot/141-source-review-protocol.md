# Named ratio and table row development gate

Apply the [prior request-focus checks](../scoped-request-focus-development-2026-11-12/source-review-protocol.md) to both consumed development cases. In cq-focus01 the exact ratio name may follow the requested operand role. The operand must remain identical to the pinned source text. The table-row rules for cq-focus02 are unchanged.

Run cq-focus01 once. Run cq-focus02 once only if cq-focus01 passes the technical, exact-source, completeness and safety checks. The batch allows at most eight local main-model calls and two NeMo wrapper invocations. Each case has 180 seconds including preparation, at most four main calls and one NeMo invocation, with zero retries and warmups. Stop at the first failure.

Record the raw mapper response, application-supplied focus, raw composer response and stored claims. Separate application wording assistance from fallback, editorial correction and owner acceptance. Bind each assessment to the exact result hash. The previous technical failure and both consumed qualification results remain preserved. Revised qualification requires a separately frozen roster and grant.
