# Power attribution development diagnostic, 2026-11-20

Contract SHA-256 `1f13d50964bd6b8460ecf4b302ff796326b42e2eeda722ca7df3ef739e3e1a1b` pins 286 files. [Frozen contract](development-contract.json) · [Source review](source-review-protocol.md)

The retained cq1-a29 correctly named 1,000,000,000 watts but failed a wording check before NeMo. Composition and safety now share an allowlist of attribution wording derived from the exact selected source. All 164 targeted tests passed. Offline replay accepted the retained sentence unchanged, attached the verified source excerpt, rejected false attribution and the wrong scale, and reproduced publication attribution. Earlier failed results remain on record. [Offline replay](../scoped-directed-power-development-2026-11-20/verified-attribution-offline-replay.json)

Run consumed cq1-a29 once. Run consumed cq1-a43 once only if cq1-a29 passes all technical, source, safety and storage checks. Maximum eight main-model calls and two local NeMo invocations combined, 180 seconds per case including preparation, zero retries or warmups. Stop on the first failure or standing usage threshold. Development only. Seventeen CQ1 cases remain reserved and three replacements remain predeclared.

Reply **Authorize scoped power attribution development diagnostics** to execute.
