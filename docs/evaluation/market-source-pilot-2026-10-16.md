# Thailand and Southeast Asia source pilot, 2026-10-16

## Representative source slice

This small pilot adds two primary sources closer to AMI Engine's market-intelligence use case than the earlier financial-filing pilot: the [Bank of Thailand's August 2026 economic release](https://www.bot.or.th/en/news-and-media/news/news-20260930.html) and the [IEA Southeast Asia Energy Outlook 2024](https://www.iea.org/reports/southeast-asia-energy-outlook-2024). `scripts/prepare_market_sources.py` pins the source PDF SHA-256 hashes, extracts complete page text, and checks that reference evidence terms occur on the cited pages. It produced 528 chunks from seven BOT and 200 IEA PDF pages. The six selected questions cover Thai exports, inflation, and demand, plus regional electricity, battery materials, and grids. They include extraction, numerical, and multi-claim tasks. This is a deliberately small source slice, not a representative statistical sample of live news or market queries.

The downloaded PDFs, extracted corpus, frozen answers, checkpoints, and scored CSV stay in ignored local paths. The IEA report is CC BY 4.0; the BOT PDF is retained locally for evaluation rather than redistributed. No evaluation reference answer is included in the retrieval corpus.

## Reproduce

Use Python 3.12 with `requirements.txt` installed and local Ollama running:

```powershell
python scripts/prepare_market_sources.py
ollama pull llama3.1:8b
ollama create ami-llama3.1:8b-4k -f config/ollama/Modelfile
ollama create ami-llama3.1:8b-8k -f config/ollama/Modelfile.judge
$env:RAGAS_JUDGE_MODEL = 'ami-llama3.1:8b-8k'
python -m main --dataset data/external/market_sources/prepared/market_cases.json --local-corpus data/external/market_sources/prepared/market_chunks.json --retriever-backend local --judge-repeats 3 --tracking-uri sqlite:///reports/mlflow.db
```

The agent runs once per question with local BM25 retrieval and `ami-llama3.1:8b-4k` generation. Ragas 0.4.3 then scores the same frozen answers and contexts three times with the 8k local judge. To repeat judging without regenerating answers, add `--frozen-inputs reports/eval_inputs_market_2026-10-16.json`; to start independent passes, add `--fresh-judge`. A matching checkpoint resumes completed passes after an interrupted run. The local Ollama Answer Relevancy prompt is versioned as `concise-json-v1` in the checkpoint identity and MLflow parameters. This prompt was introduced after the default Ragas prompt repeatedly caused the 8B judge to output a JSON schema instead of the required question and noncommittal fields; scores from the two prompt versions are not combined.

## Recorded run

The completed SQLite MLflow run is `b5663c48e4814a19961afdc22db99087` (`FINISHED`). It logged six frozen cases, three judge passes per case, and 607.08 seconds of evaluation time after the answers were frozen. The dataset SHA-256 is `0116879fe4dee340fe4ec3fcdd253890b14f1e52c6f6b0b39609635ff20cdd4c`; the frozen-input file SHA-256 is `85ab70a6f0a4f21bb79015d04938d8d08312f0d8c837470a80f33f053e088aad`; and the 18-row report SHA-256 is `a763ea019b286e2ea0653e92429e3ff86a45ae98b0b53ca11eaf3e33f930498d`. The run stores the scored CSV, frozen inputs, and checkpoint as MLflow artifacts.

| Metric | Mean over 18 scores | Largest within-case range |
|---|---:|---:|
| Faithfulness | 0.6056 | 0.1000 |
| Answer Relevancy | 0.6306 | 0.0000 |
| Context Precision | 1.0000 | 0.0000 |
| Context Recall | 0.8333 | 0.0000 |

The retriever placed a cited evidence page in its top five chunks for **5/6** questions. The IEA electricity question missed its cited page, and its answer omitted the reference's 4% annual growth and 1,300-to-2,000 TWh figures. The BOT exports answer omitted the moderation in technology-related exports. The nickel answer discussed a 10 GWh plant and Indonesia but omitted the requested regional 16 GWh capacity, planned almost 40 GWh, and Indonesia/Philippines 65% nickel share. A 1.0000 Ragas Context Precision mean therefore does **not** establish complete evidence retrieval or correct answers. Faithfulness checks grounding of what was said, not whether every part of the question was answered.

## Judge consistency and limits

All three passes gave identical Answer Relevancy, Context Precision, and Context Recall scores for each frozen case. Faithfulness for `bot-aug-2026-demand` was 0.8, 0.7, and 0.7; all other case-level Faithfulness scores were unchanged. This is modest evidence of repeatability for this exact local model, prompt, and six-answer sample. It does not validate the judge against human labels, measure run-to-run generator variation, or prove the local judge will parse every future answer. The earlier filing pilot used Ragas's default Answer Relevancy prompt and should not be merged into these metric means or treated as a direct model comparison.

The earlier 0.94 Faithfulness and 0.93 Answer Relevance claims remain unverified. These pilots demonstrate a reproducible local evaluation workflow and expose retrieval and answer-completeness failures; they do not support a production-quality or sustained-performance claim.
