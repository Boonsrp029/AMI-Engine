# Power conversion evidence placement diagnostic results

The frozen standalone pair ran once per case. Both raw verdicts were YES in the required format. NeMo accepted the supported one-billion-watt report without changing it. It also accepted the one-million-watt control. The second result is a critical false acceptance, so the experiment failed. [Supported result](actual/power-supported.result.json) · [Wrong-scale result](actual/power-wrong-scale.result.json) · [Stop record](actual/stopped.json)

Both prompts retain the same complete retrieved evidence after the exact EIA excerpt. The wrong-scale report differs only in the amount. The excerpt states 1,000,000,000 watts per gigawatt. The preceding integrated workflow failure and the independent offline quantity rejection remain as recorded. Evidence placement alone does not provide a reliable standalone check for this conversion.

Two NeMo wrappers ran with zero workflow model calls or retries. Recorded worker times were 3.54 and 1.13 seconds. Internal usage and cost were unavailable. No new stored draft or owner review resulted. The allowance closed.
