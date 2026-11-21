# Capacity fact-check diagnostic

The previous workflow remains failed. The reconstructed NeMo prompt is 5,554 characters and contains 4,342 characters of evidence from the generation and measurement records, including the exact threshold footnote. Fixed YES passed. Fixed NO and YES followed by prose both blocked. The historical rail result cannot identify which kind of verdict caused the block. The offline replay used the real Colang flow and a fixed judge. [Prompt and results](safety-prompt-replay.json)

Run one standalone NeMo wrapper on the retained report and complete evidence, with the unchanged policy and pinned local model. The existing standalone harness supplies its standard verification question. The fact-check template itself interpolates only the report and evidence. Capture the raw parser input, rendered prompt, execution time and rail decision. A single supported YES or YES. with an unchanged accepted report passes. A NO indicates disagreement with the source on this case. Non-verdict prose or missing parser input requires separate diagnosis. A pass would show this isolated check succeeded once and leaves the original workflow failure in place.

Maximum 60 seconds for the worker, one NeMo wrapper invocation, zero analyst workflow calls, zero retries and warmups. The wrapper ceiling does not measure provider-internal calls or usage. Development diagnosis only. Output goes to actual-fact-check. Exact contract SHA-256 560fb2516b73e7899389e053b8dc224b46c14e4b098b313dd7b2443ad59ebfc7. [Frozen contract](fact-check-contract.json) · [Runner](run_fact_check.py)

Reply **Authorize one capacity fact-check diagnostic** to execute the frozen check.
