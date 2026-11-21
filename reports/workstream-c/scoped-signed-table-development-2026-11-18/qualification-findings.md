# CQ1 stopped at mapper self-context

Two of twenty ordered cases ran once. cq1-a39 passed technical, assistant source, completeness, safety and storage checks. cq1-a40 failed semantic evidence validation before composition. Eighteen cases remain unattempted. The allowance is closed. [Exact accounting](qualification-batch-summary.json)

The batch used three local main-model calls and one NeMo wrapper invocation. Captures report 6,007 main-model tokens. Internal NeMo usage and monetary cost remain unmeasured. Owned wall times were 67.27 seconds and 19.25 seconds. No retries, warmups, substitutions or tuning occurred in the batch.

cq1-a39 selected the correct Solar thermal row and the composer selected its verified unit. Application rendering retained 3 billion kWh, 0.1%, the generation measure and the 2023 denominator. NeMo passed. The stored draft remains needs_review. Its U.S. scope is established by the question and pinned table but remains implicit in prose. Owner adjudication for this new qualification output is pending.

cq1-a40 selected the relevant direct span s_379ceb3c45f341ef. It contains the complete definition of at least one megawatt, or 1,000 kilowatts, of total generating capacity. The mapper then put that same identifier in its context array, alongside an unrelated nuclear/renewable-share span. No source material was missing for the requested answer.

Offline replay with sockets blocked reproduced the exact rejection, “Duplicate fact evidence role.” The response passes the generated JSON schema but violates the existing resolver rule prohibiting a span from serving as its own context. There was no composition response, final draft or NeMo invocation for cq1-a40. The model reported normal completion within its output limit. This evidence identifies a schema/validation alignment problem and does not establish a GPU-capacity or inherent open-source-model limitation. [Retained replay](cq1-a40-offline-replay.json)

The current schema groups direct choices by source record. For an unfocused component, both span_id and context draw from the same record-wide span enum. Only focused cases exclude their required direct span from context. The next offline repair should express direct/context disjointness for generic selections while retaining the current wire fields and semantic validator. A direct-span-specific schema branch can exclude that identifier from its context choices. Measure grammar size and request fit before requesting more generation. Do not silently deduplicate or repair the retained invalid output.

All 201 inputs used by this batch were copied and verified in executed-input-snapshot before any future runtime change. The two original failed responses and prior qualification remain intact. Human review is relevant to new assessable drafts; cq1-a40 has no final draft to score. Owner acceptance of earlier development editorial copies is already recorded and remains distinct from current qualification acceptance.
