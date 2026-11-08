# Repaired constrained-decoder diagnostic — pending validation

Prepared, not authorized. Final integrated repair suite passed1,549tests with14warnings. Source/contract/protected hashes verified after the run. Actual repaired generation remains unverified.

Contract: development-contract-v4.json
SHA-256: `af23323de0515807aaa390a5dd365df4c193f45a9f5956f10b81516dbe133022`
Protocol: diagnostic-protocol-v3.json
New output: actual-development-v3/

Run cq-p01 once, then cq-p02 once only after all first-case technical/source/completeness/safety checks pass. New ceiling eight local main-model calls and two NeMo invocations,180seconds per case including preparation, no retries/warmups. Stop at first failure. Model/context/completion/temperature, diagnostic inputs and acceptance criteria are unchanged. The mapper now uses the existing constrained-state decoder, and schema-format accounting reflects the actual transport. No validation was relaxed.

Prior interrupted/failed batches remain closed and preserved. Two main-request starts and zero NeMo invocations have been recorded across them; the proposed additional allowance would bring the cumulative ceiling to ten main starts and two NeMo invocations. Known completed-response usage is471input+141output; interrupted usage and monetary costs are unknown. cq-p01 remains consumed development evidence.

The no-information/partial-answer and full source-support gates remain strict. Schema success will not establish semantic completeness; the previously omitted Japan forecast and observation/forecast distinction must be inspected. No CQ1 twenty-case run, Ragas, hosted inference, approval/export, publication or deployment is included.

No manual review of the prior technical failure is requested. After new assessable outputs, owner review is required before owner-acceptance claims. Overall quality and production qualification remain incomplete.
