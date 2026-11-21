# One mapper-only fact decoder diagnostic

Protocol SHA-256 `52acafba3197eb6f13702d333e85f1211314b2c560063701f044f435ed278019`, frozen for 14 November 2026 in Bangkok. All 102 input pins verified. The request uses the same local model and settings as the stopped development attempt and reserves 3,435 of 4,096 tokens.

The response schema now requires one nonempty group for supported facts, no groups for missing facts, and two or three nonempty groups for conflicting facts. Application validation still checks exact spans, offsets, roles and branch bindings. The revised schema rejected the saved empty-support response. A socket-blocked fixed response reached the composition boundary with both requested facts, and 102 targeted tests passed. Real decoding remains unverified.

Run the consumed cq1-a20 mapper once. Allow 120 seconds overall, with a service limit of 60 seconds and an offline validation limit of 25 seconds. Zero composer calls, NeMo invocations, retries or warmups. Stop on failure or the standing usage threshold. The runner retains raw transport output under actual-mapper, then validates it with sockets blocked. For a source pass, both decisions must identify the information and recipient from the historical capability sentence, and any context must stay separate. A passing mapper result does not by itself assess final wording or meet the two-case development gate.

The earlier failure remains closed. This grant covers one new mapper request only. CQ1, full workflows, hosted inference, Ragas, Databricks, publication, deployment, approval and export are outside its scope.

Reply **Authorize one scoped fact-decoder mapper diagnostic** to grant this exact run.
