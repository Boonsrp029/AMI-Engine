# Power quantity development review

Run consumed cq1-a29 once. Verify the direct EIA passage, its hash and offsets, and that the raw composer and exact stored draft give one gigawatt as 1,000,000,000 watts. Check the measure and conversion direction, require final NeMo acceptance and no fallback or editorial change. A block from the power validator is a failed technical gate even if it prevents an incorrect draft from reaching safety.

Only after cq1-a29 passes every gate, run consumed cq1-a43 once. Require the complete attribution with empty mapper context, a raw claim naming Electric Power Monthly as the cited publication, the same source and offsets, final NeMo acceptance and the exact persisted draft. These two consumed development cases never count as fresh qualification successes.

Stop on first failure or the standing usage threshold. 180 seconds, up to four main calls and one NeMo invocation per case. Zero retries or warmups. Preserve all 17 unattempted CQ1 entries for the next roster.
