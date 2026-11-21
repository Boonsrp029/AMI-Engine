# Power attribution development results

Both consumed cases passed all technical, source, safety and storage checks once. The mapper selected the complete cited span with no additional context. The composer authored the exact stored text, with no fallback or editorial correction. Both raw NeMo fact verdicts were YES. The capacity-specific evidence view put the exact conversion excerpt before the full evidence for cq1-a29. The publication case used the full evidence without a leading excerpt.

| Case | Exact stored claim | Wall time |
|---|---|---:|
| cq1-a29 | One gigawatt is equivalent to 1,000,000,000 watts in the EIA measurement guide. | 54.36 s |
| cq1-a43 | The table cites Electric Power Monthly as its data source. | 44.77 s |

[Conversion assessment](actual-development-v1/cq1-a29.assessment.json) · [Publication assessment](actual-development-v1/cq1-a43.assessment.json)

The pair used four main calls and two NeMo invocations, with 6,356 recorded input and 383 output tokens, zero retries, and unknown internal NeMo usage and cost. The earlier standalone wrong-scale false acceptance remains failed. Owner source and wording review is pending for these exact drafts. Both are saved at revision 1 awaiting review.
