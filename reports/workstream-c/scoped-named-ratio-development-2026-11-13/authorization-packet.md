# Named-ratio development diagnostic for 13 November

The 12 November contract ended the day with cq-focus01 passed and cq-focus02 unattempted. The runner checks the frozen Bangkok date. The qualification compiler requires both development passes to bind to one execution contract. Today's pair is a fresh batch using the same two consumed fixtures, source bytes, model, generation settings and application revision.

Contract SHA-256 `e016d82252beb9c0f88207e0a3a0cd09c923ecafe3506dfda59a656e8848dd93`. The operator and CLI checked all 147 pins. The contract also pins yesterday's result and passing source assessment as historical evidence. Today's output directory has zero attempts.

Run cq-focus01 once and run cq-focus02 once only after the first passes technical, safety and exact-source checks. Each case has 180 seconds including preparation. The ceiling is eight local main calls and two NeMo wrapper invocations total, with zero retries and warmups. Stop on the first failure or at the standing usage threshold. Record application-supplied claim wording and raw composition separately. Follow the [source review protocol](source-review-protocol.md).

This contract requires its own explicit grant. Its scope excludes qualification, Ragas, hosted inference, Databricks, approval/export, publication and deployment.
