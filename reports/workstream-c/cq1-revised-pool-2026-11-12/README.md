# Revised CQ1 roster

Frozen on 12 November 2026 before any revised qualification generation. The original CQ1 batch remains closed after one failed attempt. cq1-a01 is consumed. The new answerable case cq1-a11 occupies its roster position. The other nineteen questions, plans and scope sidecars match the original entries. The existing source and corpus files are copied with their original SHA-256 hashes.

The replacement asks for the 24-hour generation in the EIA example and for the capacity-factor denominator. The first answer must retain the example's operating capacity, duration, energy amount and unit. The denominator must describe maximum possible energy under continuous full-power operation over the same period. The corpus contains separate, attributed paraphrases of the two sources and retains a measurement definition as a retrieval distractor. The offline retrieval check found both required sources and the distractor. [EIA plant generation FAQ](https://www.eia.gov/tools/faqs/faq.php?id=104&t=1) [EIA capacity factor glossary](https://www.eia.gov/tools/glossary/index.php?id=Capacity_factor)

| Category | Planned cases | Required passes |
|---|---:|---:|
| Answerable | 10 | 9 |
| Partial | 2 | 2 |
| Missing | 4 | 4 |
| Conflict | 2 | 2 |
| Injection | 2 | 2 |

The critical-error allowance is zero. The existing 180-second per-case deadline, four main calls and one NeMo wrapper per case, single-attempt rule, and stop gates remain in force. Assistant source review precedes advancement and keeps raw composition, fallback and editorial text distinguishable. Owner adjudication applies to the final exact-result bundle.

The [freeze audit](freeze-audit.json) records the pool, plan and scope hashes. The [offline mapping context check](offline-mapping-context.json) covered all twenty cases with a maximum 3,580 of 4,096 reserved tokens. The composer remains subject to runtime context admission.

The current geography development pair must pass actual technical and exact-source checks before compilation and a separate qualification grant. No revised qualification attempts have started.
