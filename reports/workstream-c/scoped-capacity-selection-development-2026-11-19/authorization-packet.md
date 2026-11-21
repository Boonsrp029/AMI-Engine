# Capacity selection diagnostic, 19 November 2026

Contract SHA-256 `7ea14f8ef8268f3a4c6d0bf254f242f34b40ad8c7061f03e9534b891762fa165` binds 193 frozen inputs. [Model, settings, source identities and output location](development-contract.json)

Run consumed cq1-a40 once, then cq1-a39 once only after all first-case checks pass. Maximum eight local main calls and two NeMo invocations combined, 180 seconds per case including preparation, zero retries and warmups. Stop at the first failure or the standing usage threshold. Development only. [Source review protocol](source-review-protocol.md)

101 targeted tests passed. A socket-blocked replay rejected the retained free-text composer output, rendered both quantities with a fixed selection and reproduced the historical signed-table claim. The historical failure remains failed. Actual generation under this contract is pending. [Replay](offline-replay.json)

Reply **Authorize scoped capacity-selection development diagnostics** to authorize execution.
