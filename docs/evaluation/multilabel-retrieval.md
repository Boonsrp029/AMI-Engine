# Offline multi-label retrieval evaluation

Use this benchmark to check which labeled documents the parallel analyst
workflow can retrieve before mapping or composition. It complements the
existing answer-quality qualification and Ragas evaluation.

From the repository root, using the existing application environment:

```powershell
python -m src.evals.retrieval
```

The defaults use `data/silver_level/silver_market_feeds.json` and the
14-query `data/retrieval_eval/market_multilabel.json`. The labels were extracted
from the Databricks portfolio handoff without running its notebook and retain
the export hash. Use `--corpus` and `--labels` to select other matching files.
The command emits JSON to standard output with corpus and label hashes, ranked
IDs, missing relevant IDs and the exact query denominator. It calls the existing
`LocalBM25Adapter` in isolation, with no model, database, workspace or MLflow call.

## Reading the results

- Metrics are means over queries. Each relevant `feed_id` counts once.
- Precision@k divides by k even when the adapter returns fewer hits. The report
  includes the label-imposed precision ceiling. Recall divides by the number of
  labeled relevant IDs. MRR uses the rank of the first relevant ID and scores
  no-hit queries as zero.
- Empty retrieval remains in the denominator. Unlabeled queries, duplicate
  labels, and gold IDs absent from the corpus fail validation rather than
  producing a misleading score.
- The current adapter returns at most five sources. Compare ranks 1, 3 and 5
  with the handoff. Its Databricks @10 results need a separate ranking run.

## Initial local result

On the checked-in mock Silver snapshot, the adapter scored all 14 queries,
including nine with multiple labels:

| Rank depth | Precision | Recall | Label-imposed precision ceiling |
|---:|---:|---:|---:|
| 1 | 1.000 | 0.619 | 1.000 |
| 3 | 0.524 | 0.845 | 0.643 |
| 5 | 0.357 | 0.917 | 0.414 |

MRR was 1.000. In this fixture, top-1 alone hides missed relevant documents.
Treat the imported labels as development judgments on a small mock corpus.
Recall measures coverage of those labels. Unlabeled alternatives may also be
relevant. Cloud strategy scores in the handoff are reported evidence. A direct
comparison needs the frozen cloud corpus version and per-query rankings.
Keep these queries separate from the held-out answer qualification pool.
