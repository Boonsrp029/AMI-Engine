# Evidence placement diagnostic results

Both frozen standalone cases ran once in order and met their expected outcomes. The supported 1,000-kilowatt report returned YES and NeMo accepted it without altering the text. The 1,500-kilowatt control returned NO and the fact-check rail blocked it. Both raw verdicts used the required format. The same complete retrieved evidence was present after the selected EIA excerpt in each prompt. [Supported result](actual/result-0.json) · [Negative control](actual/result-1.json)

The earlier full-evidence false rejection remains on record. The new result supports the evidence placement hypothesis on this pair. No integrated workflow, storage or qualification test ran under this grant. No manual draft review is required.

Two NeMo wrappers ran. Worker timings were 2.89 and 1.40 seconds, excluding outer identity checks. Zero analyst model calls, retries or warmups. Internal usage and monetary cost were unavailable. The allowance is exhausted.
