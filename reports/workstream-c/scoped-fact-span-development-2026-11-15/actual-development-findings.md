# Whole-span diagnostic stopped at cq1-a20

The authorized run attempted one of two cases and closed on the first technical failure. The biomass case cq1-a19 remains unattempted. There is no stored draft for manual review. [Batch summary](batch-summary.json)

Both mapper decisions selected the correct direct span, s_6af27ac482a98ade, covering what earlier automated meters could report periodically and to whom. Both used a valid same-record context ID, s_2845cfa10cf8e534, for generic metering background. The reference is structurally valid but unnecessary to interpret the selected sentence. No wireless-reporting span was selected. [Raw mapping](actual-development-v1/cq1-a20.mapping.raw.json)

The raw composer wrote “Automated electricity meters report electricity use periodically to the utility.” It retained the reported information, cadence and recipient, but made a present-tense assertion from the source's historical capability. The exact saved responses reproduced the capability-retention rejection with sockets blocked. The runner stopped before final NeMo or publication. [Raw composition](actual-development-v1/cq1-a20.composition.raw.json) · [Offline replay](offline-failure-replay.json)

The attempt took 45.19 seconds and used two local model calls with 3,313 reported tokens. Zero NeMo invocations, retries or warmups. Monetary cost is unmeasured. All 107 pinned inputs were verified and copied.

The whole-span wire resolved the prior invalid context ID and offset symptoms on this attempt. It did not establish composition quality. Next, investigate a general capability-preservation method that retains the source's subject, temporal framing and modality without adding unrelated context or using owner editorial wording as model evidence. Keep the current fail-closed check and old failed outputs. A future model diagnostic needs a separate applicable grant.
