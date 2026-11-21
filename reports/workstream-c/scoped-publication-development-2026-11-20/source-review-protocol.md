# Publication attribution development review

Run consumed cq1-a43 once. Require the raw mapper to select the complete same-record citation, including Electric Power Monthly and its line-broken attribution, with empty context. Require one source-backed claim naming Electric Power Monthly as the cited publication. Verify full source offsets, raw composition, no fallback or editorial change, final NeMo acceptance and the exact persisted draft.

Only after cq1-a43 passes every gate, run consumed cq1-a42 once. Verify the raw table selection, exact EIA row and heading, explicitly stated U.S. scope, 2023, 162 billion kWh and 3.9% of total U.S. utility-scale generation. Require final NeMo acceptance and the exact persisted draft.

Stop on first failure or standing usage threshold. Each case allows 180 seconds, up to four main calls and one NeMo invocation. Zero retries or warmups. Both cases are development evidence. The 19 unattempted qualification cases remain reserved.
