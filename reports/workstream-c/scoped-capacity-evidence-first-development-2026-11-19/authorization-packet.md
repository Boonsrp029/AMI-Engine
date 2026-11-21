# Integrated capacity evidence placement diagnostic

Contract SHA-256 `8f24be443acc1f94a536fcedd690d82973cf2fe39e6df0073b1090adf5504bdb` binds 206 inputs. [Contract](development-contract.json) · [Source review](source-review-protocol.md)

Run consumed cq1-a40 once. Run consumed cq1-a39 once only after the first passes technical, exact-source, completeness, final safety and storage checks. Maximum eight local main calls and two NeMo invocations, 180 seconds per case including preparation, zero retries and warmups. Stop at first failure or the standing usage threshold. Development only.

Offline verification confirmed exact payload parity with the successful standalone capacity check and byte-identical full context for the signed table. The final safety callback still controls publication. Qualification requires passing integrated development evidence and separate authorization.

Reply **Authorize scoped capacity evidence-first development diagnostics** to execute.
