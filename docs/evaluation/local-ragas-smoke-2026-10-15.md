# Local Ragas smoke evaluation, 2026-10-15

This is one mock-corpus integration case, not a held-out benchmark or a production performance claim.

## Reproduce

Create the Ollama model described in `config/ollama/Modelfile`, install `requirements.txt`, and run from the repository root:

```powershell
python -m main --dataset data/local_eval_dataset.json --limit 1 --retriever-backend local --tracking-uri sqlite:///reports/mlflow.db
```

The case is sourced from exported Silver record `feed_113`. Dataset SHA-256: `a4f4969ebf652deff8c3f4a6dd78768ff18a13ba0797f95277afb8244a5a3dae`.

## Completed run

| Field | Value |
|---|---|
| MLflow run ID | `65363b39a6d54e9d83709d683853dfab` |
| Status | `FINISHED` in local SQLite tracking store |
| Retriever | Local BM25 over exported Silver JSON, top 5 |
| Generator and judge | Ollama `ami-llama3.1:8b-4k` |
| Ragas | 0.4.3 collection metrics |
| Cases | 1 |
| Faithfulness | 1.0000 |
| Answer Relevancy | 0.9349 |
| Context Precision | 0.9167 |
| Context Recall | 1.0000 |

The CSV is written to `reports/eval_report_latest.csv` after all four scores and MLflow logging complete. The local SQLite database is `reports/mlflow.db`. Both are generated artifacts and ignored by Git.

## Limits

The Silver export is a small mock corpus, and the question was selected from its own content. A prior attempt to score the same case produced Faithfulness 0.5 before MLflow tracking failed; the completed run produced 1.0. This shows that the local 8B judge's score stability needs repeat runs and human review. The agent passed NeMo's configured output check, but this run does not prove that the conditional hallucination flow performed a factuality check. The original `data/gold_eval_dataset.json` references facts absent from the Silver export, so it is not an appropriate local benchmark until the matching source material is available. No latency distribution, cost, or deployment performance was measured.
