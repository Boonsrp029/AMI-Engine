# Owner adjudication of the r06 editorial wording — 30 October 2026

The project owner accepted the separate editorial proposal for Claims 2 and 3, rejected the original projected wording for those claims, and confirmed source support for all three claims. This completes the requested **owner source/wording review**. It does not approve a stored workflow revision, create an export, establish independent reviewer usage or turn the failed generation diagnostic into a pass.

| Claim | Owner decision | Accepted content and source location |
|---|---|---|
| 1: FDI share | Source support confirmed; unchanged in the editorial candidate | FDI represented 73% of total application value in 2024. BOI PDF index 1 / PDF page 2, `BOI_2024:unit:1:2`. |
| 2: leading source | Editorial accepted; original wording rejected | Singapore led by application value: 357.5 billion baht, 43% of total FDI application value. Same page/source ID. The owner explains that the question asks for leadership by valuation and the additional value figures help complete the answer. |
| 3: project comparison | Editorial accepted; original wording rejected | China had more projects: 810 versus Singapore's 305. Same page, source IDs `BOI_2024:unit:1:2` and `BOI_2024:unit:1:3`. The owner requires the comparison's conclusion to be explicit. |

Source: the pinned [BOI investment applications release](https://osos.boi.go.th/article_attach/PR4_2568EN.pdf). These are source-supported historical application figures, not completed investments or a current-market observation.

The short reply **“Use editorial wording; source support confirmed”** and the subsequent detailed adjudication are preserved verbatim in a new local record. The accepted candidate is a byte-identical copy of the reviewed editorial proposal, SHA256 `6aadef88fe00f76a74a630590660b52aedf074ec9079f039b84d3acb845a6e0a`. Its source assignments and warnings are unchanged. The owner did not adjudicate or waive the warnings in this response.

Local provenance: `reports/workflow_pilot/production-readiness-2026-10-27/resume-v22/owner-adjudication/` contains `owner-comments.txt`, `adjudication.json` and `accepted-editorial.json`, including hashes of the original packet/proposal. The original packet, raw model response, projected draft, source gate, historical CSV and prior approvals/exports remain unchanged; their pending fields describe their original state, superseded for wording review by this separate record. No numerical rating or new reviewer identity was invented.

The [actual composer diagnostic](../production/composer-v153-findings-2026-10-30.md) still **failed its frozen completeness gate**, and its allowance remains closed. The editorial candidate is human-reviewed wording, not fresh model output. Future checks should require an explicit requested measure and comparison conclusion; case-specific contextual figures must not become a blanket requirement to invent unrequested numbers. Do not hardcode this BOI answer into runtime.

No further human review is needed to record these decisions. New generated outputs still require source/quality assessment, and saving any brief as approved/exportable requires approval of that exact stored revision. Independent reviewer tasks and production rollout acceptance remain pending. No additional model calls, deployment or contact was authorized by this adjudication.
