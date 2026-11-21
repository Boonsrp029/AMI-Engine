# Power quantity development diagnostic, 2026-11-20

Contract SHA-256 `73eb0ad0f7bfca45346661c7267acc9a81533376ae4c4f0242b5d2f220c5d679` pins 258 inputs. [Frozen contract](development-contract.json) · [Source review](source-review-protocol.md)

Run cq1-a29 once. Run cq1-a43 once only after the first passes every check. Combined maximum eight local main calls and two NeMo invocations, 180 seconds per case, zero retries or warmups. Stop at the first failure or standing usage threshold. Development only.

The offline replay rejected the retained wrong conversion before safety. It accepted a complete fixed conversion and retained the correct kilowatt and publication answers. [Replay](../scoped-publication-development-2026-11-20/offline-power-quantity-replay.json)

Reply **Authorize scoped power quantity development diagnostics** to execute.
