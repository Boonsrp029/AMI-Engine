# Fact-selection development stopped at cq1-a20

The authorized run attempted one of two cases. The model returned one mapper response in 97.48 seconds of outer wall time. It marked both requested facts supported and supplied empty evidence groups for both. The existing wire schema allowed that state. Application validation rejected it with “Invalid fact evidence groups,” as reproduced by a socket-blocked replay of the exact captured response. [Raw mapper](actual-development-v1/cq1-a20.mapping.raw.json) · [Offline replay](offline-failure-replay.json)

Composition and NeMo did not run. No draft was produced and cq1-a19 remains unattempted. The allowance is closed under the first-failure rule. Neither semantic support nor answer quality was assessable. This failure needs no manual wording review.

One local model call reported 2,396 tokens. No retries or warmups occurred. Monetary cost was unmeasured. All 103 pinned inputs were verified and copied to the executed-input snapshot. [Batch summary](batch-summary.json)

The next offline change should encode evidence-group cardinality by fact state directly in the mapper schema. Preserve the application checks and test the captured invalid response plus nonempty support, explicit absence and multi-record conflict. The revised schema must be verified with the actual decoder before another full workflow or qualification run. A subsequent actual diagnostic requires a new frozen authorization.
