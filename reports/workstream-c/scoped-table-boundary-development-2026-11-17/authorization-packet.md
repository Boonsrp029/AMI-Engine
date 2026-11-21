# Table boundary development execution request

Contract SHA-256 **f88d251e8e6f86245bd0fc89feef4ba7c02f1eb63dd64e7156090299788b3f64** binds 129 inputs, two consumed questions and their exact source corpora, sidecars, model/settings and a new output directory. The private mapping version is cq-fact-span-selection-v1-complete-table-rows. [Frozen contract](development-contract.json)

Run cq1-a28 once. Advance to cq1-a27 once only after all first-case technical, source, completeness, title, safety and storage gates pass. Total ceiling is eight local main-model calls and two NeMo wrapper invocations. Each workflow has 180 seconds including preparation, zero retries and zero warmups. Stop and close at the first declared failure or standing usage threshold. [Source protocol](source-review-protocol.md)

The model remains ami-llama3.1:8b-4k, digest 6f3154f347c4f96858a9f259e64d96b2675f4cb2f4894b2d9714fb0752aecc23. Settings remain 4,096 context tokens, 900 completion tokens, temperature zero and the local Ollama endpoint. Reverify the pinned local identity within execution admission. This document performs no model access.

Offline targeted checks pass 107 tests, including complete span provenance and duplicate rejection. Socket-blocked fixed-response mapping/composition passed both consumed cases. The largest request reservation is 3,671/4,096 tokens. This proves the fixed contracts, with actual new model quality and final safety still unverified. Read the accompanying engineering results for the full offline suite result before execution.

Manual human review applies to new assessable outputs before owner acceptance and to the exact stored revision before approval/export. The previous CQ1 result remains one pass, one technical failure and eighteen unattempted cases. An editorial wording change does not turn the failed case into a new generation success.

This request covers development generation only. Qualification and subsequent external actions require their applicable grants. All earlier inference allowances are closed. Reply **Authorize scoped table-boundary development diagnostics** for this contract.
