# Fact-selection development gate

Run consumed cq1-a20 once. Require the raw factual decisions to identify electricity use and the utility from the historical capability sentence. Keep any necessary context separate. Require raw and final claims to preserve historical capability, periodic cadence and recipient, with no unrelated background. Then run consumed cq1-a19 once only after technical, safety and exact-source review pass. Require a verified biomass row selection preserving 47 billion kWh and 1.1% of total U.S. utility-scale generation in 2023.

Maximum eight main model calls and two NeMo invocations across both cases, 180 seconds per case including preparation, zero retries or warmups. Stop on first failure or the standing usage threshold. Bind findings to exact results and separate raw selection, row rendering, fallback and owner editing. This development run does not authorize CQ1 qualification or approval/export.
