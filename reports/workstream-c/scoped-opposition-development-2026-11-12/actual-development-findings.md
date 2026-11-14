# Opposing publication-status diagnostic results

Both cases passed technical and assistant exact-source review on 12 November 2026. The previous failed batches remain preserved. Both new revisions await review and have zero stored reviews or exports.

| Case | Outcome | Main calls | NeMo invocations | Wall time |
|---|---|---:|---:|---:|
| cq-status01 | Both the raw and stored drafts cite the 2019 Peru rail amount and provisional status. No false conflict, fallback or editorial correction. | 2 | 1 | 48.765 s |
| cq-status02 | The raw mapper selected only the provisional notice. The application found the opposed final notice, retained both exact statements and source IDs, and stored a conflict disclosure without a status claim. | 1 | 0 | 20.219 s |

The second result demonstrates the integrated application check on this consumed fixture. The raw model selection remains incomplete and inspectable. The batch used 2,037 known main input tokens and 461 output tokens, totaling 2,498. Internal NeMo usage and monetary cost remain unmeasured. Owner acceptance remains pending.
