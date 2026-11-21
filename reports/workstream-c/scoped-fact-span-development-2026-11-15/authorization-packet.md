# Whole-span development authorization

Contract SHA-256 `470276c42b07f8bb1a5c595b90f9d429b4a0dd63c98991dfcfb1ed63180cc859`. Frozen for 15 November 2026, Bangkok time. The runner and CLI verified 107 pinned inputs and neither case has started.

This contract tests the private whole-span path with the pinned local ami-llama3.1:8b-4k model, a 4,096-token context, 900-token completion limit and temperature 0. With sockets blocked, fixed responses reached the stored-draft projection for both cases. The largest development mapper or composer request reserved 3,423 tokens. All 20 frozen CQ1 mapper requests fit, with a maximum reservation of 3,544 tokens. Composer admission for the larger roster depends on the actual mapper selections. [Offline check](offline-request-check.json)

Run cq1-a20 once. Run cq1-a19 once only after the first case passes technical, safety and exact-source review. Maximum eight local model calls and two NeMo checks combined, 180 seconds per case including preparation, zero retries or warmups. Stop on the first failure or at the standing usage threshold. [Review protocol](source-review-protocol.md)

Both cases are consumed development evidence. The closed failures remain on record. This scope covers development only. CQ1 needs both development passes, a finalized contract and its own grant.

Reply **Authorize scoped whole-span development diagnostics** to grant this exact run.
