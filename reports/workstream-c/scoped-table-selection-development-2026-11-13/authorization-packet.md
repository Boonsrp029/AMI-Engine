# Composer table-row selection diagnostic

The selected contract makes the composer return the exact component and unit IDs for verified table rows. The application renders the pinned fields and retains the source hash, span offsets and unit lineage. The raw response records the model's selection separately. The same final projection and safety path handles both application-rendered rows and prose. A table-only request still uses a mapper and a composer call.

113 targeted tests passed. The socket-blocked replay accepted the retained ratio response and a synthetic table-ID response through normal projection. The table-ID response was supplied by the test. The retained failed generation remains unchanged. The operator and CLI verified all 154 pins for contract `bd4c66afabf91cacbcc77139162f95eef227b704bc68c52dacd516a653f0ec95`.

Run cq-focus01 once, then cq-focus02 once only if the first passes. Follow the [source review protocol](source-review-protocol.md). The total ceiling is eight local main calls and two NeMo wrapper invocations, 180 seconds per case, with zero retries or warmups. Stop on the first failure or standing usage threshold. The frozen date is 13 November 2026 in Bangkok. This grant covers development only.
