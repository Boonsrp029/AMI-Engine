# Repeated local Ragas judge run, 2026-10-15

This run tests scoring reliability on one mock Silver case. It does not estimate performance on representative market intelligence questions.

## Reproduce

```powershell
.\.venv\Scripts\python.exe -m main --dataset data/local_eval_dataset.json --limit 1 --retriever-backend local --judge-repeats 3 --tracking-uri sqlite:///reports/mlflow.db
```

The agent ran once. Each Ragas metric then scored the same question, answer, retrieved contexts, and reference three times. Ragas version: 0.4.3. Judge and generator: local Ollama `ami-llama3.1:8b-4k`. MLflow run ID: `34fc05e3050e4cfb8b5fa3b00995dc89` (FINISHED). Elapsed time: 168.56 seconds. The per-pass CSV is generated at `reports/eval_report_latest.csv` and ignored by Git.

| Judge pass | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---:|---:|---:|---:|
| 1 | 0.5000 | 0.9349 | 0.9167 | 1.0000 |
| 2 | 1.0000 | 0.9349 | 0.9167 | 1.0000 |
| 3 | 1.0000 | 0.9349 | 0.9167 | 1.0000 |

The mean Faithfulness was 0.8333 and its within-case range was 0.5. This is material judge instability. The other metrics had zero range in these three passes only; that does not establish general stability. Earlier 0.94 Faithfulness and 0.93 Answer Relevance claims remain unverified.

## What still prevents a benchmark claim

This particular run used one case selected from the 20-record mock Silver export. Its reference was written from that same record, so it is not a held-out, independently sourced evaluation. The score demonstrates that the local integration executes and records real Ragas outputs. The later [external-filing pilot](financebench-filing-pilot-2026-10-15.md) adds source-backed questions and a multi-case judge-consistency review, but it also exposes poor evidence-page retrieval and does not establish general market-intelligence quality.
