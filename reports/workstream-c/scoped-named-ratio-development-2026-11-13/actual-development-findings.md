# Named-ratio development results for 13 November

The authorized development batch passed one of two cases and closed at the table-row technical failure. The qualification roster remains unattempted.

| Case | Result | Wall time |
|---|---|---:|
| cq-focus01 | Execution, safety and exact-source review passed. The raw and stored claims give the generator output and correct capacity-factor denominator. The application supplied the operand wording. The composer named the ratio. | 103.687 s |
| cq-focus02 | The mapper selected the exact natural-gas table span. The composer gave the year and generation amount, then omitted the requested share of total. The focused-claim validator rejected the incomplete raw draft before safety. Revision remained 0. | 26.922 s |

The [socket-blocked replay](cq-focus02-offline-replay.json) reproduced the validation error. The first case reached review-pending revision 1 with zero stored reviews or exports. The failed case has no draft to adjudicate manually. All 147 pinned inputs matched and were saved with their hashes.

The batch used four main-model calls and one NeMo wrapper invocation. Known main-model usage totaled 6,308 tokens. Internal NeMo usage and monetary cost remain unavailable.

The table row and requested fields are already available as a deterministic source-bound unit. For the next offline design pass, assess application rendering of that verified row with its own provenance, or a constrained composer response that selects the verified row without paraphrasing. Keep raw model completeness separate. The current diagnostic required the raw composer to include the share. Any change to that contract needs explicit review before a new generation allowance.
