# External filing pilot and local judge consistency, 2026-10-15

## Source and scope

The pilot uses the [FinanceBench open-source sample](https://github.com/patronus-ai/financebench), pinned to Git commit `cc39aeb4afdf33909ee1412188bf89035950c2eb`. Its sample is licensed CC BY-NC 4.0. `scripts/prepare_financebench.py` verifies both JSONL hashes, downloads and verifies the original annual-report PDF hashes, and extracts filing text with `pypdf`. Benchmark answers and evidence snippets are **not** added to the retrieval corpus. Generated data are ignored under `data/external/`.

Three complete filings (AES 2022, Amcor 2023, AMD 2022) yielded 2,507 text chunks and 14 benchmark questions across utilities, materials, and information technology. Six questions were selected before scoring: two per filing, covering extraction, numerical, and logical reasoning. This is a filing-QA pilot, not a sample of the project's real-time news or Thailand/APAC market-intelligence tasks. It is not the full 150-question open FinanceBench sample.

The extracted text covers all 16 benchmark evidence pages for the 14 questions: normalized unique-word overlap with the benchmark's page text ranged from 0.944 to 1.000 (mean 0.986). This checks PDF extraction, not retrieval or answer quality.

## Reproduce

From a Python 3.12 environment with `requirements.txt` installed and Ollama running:

```powershell
python scripts/prepare_financebench.py
ollama pull llama3.1:8b
ollama create ami-llama3.1:8b-4k -f config/ollama/Modelfile
ollama create ami-llama3.1:8b-8k -f config/ollama/Modelfile.judge
$env:RAGAS_JUDGE_MODEL = 'ami-llama3.1:8b-8k'
python -m main --dataset data/external/financebench/prepared/pilot_cases.json --local-corpus data/external/financebench/prepared/filing_chunks.json --local-retriever-mode dense --retriever-backend local --judge-repeats 3 --tracking-uri sqlite:///reports/mlflow.db
```

The agent uses the 4k model; the judge uses the 8k model with a 3,072-token structured-output allowance. `--frozen-inputs reports/eval_inputs_latest.json` reuses the captured agent answers and contexts. By default, scoring resumes a matching per-case checkpoint after failure. Add `--fresh-judge` to perform another independent set of judge passes over the same frozen inputs. The frozen inputs, checkpoints, and final CSV are local ignored artifacts; the completed MLflow run also stores the inputs, checkpoint, and report.

## Completed pilot

MLflow run `440bf3eeafc94d1b817d8584e3a6b347` is `FINISHED` in local SQLite tracking. The original scored report contained 18 rows: six frozen answers × three judge passes. Its SHA-256 was `37118afbb18e9fe62aba4f87d4c8af38fac3050fd6bc033a7b7050f154910065`. The scoring run took 1,356.93 seconds, including local model and embedding startup. A later checkpoint reconstruction with final reporting code produced MLflow run `5cb7af24d9d74fd0baf7036bc15c89a4` (`FINISHED`) and the current report SHA-256 `b98d237705d2756bbe0e964d5fcb8e812c5bc3da9cbc85ec949a4042e5c45de5`. The reconstruction reused all 18 scores; it was not a second judge experiment. It added the explicit evidence-page-hit column and logged the 0.5 hit rate.

| Metric | Mean over 18 scores | Largest within-case range |
|---|---:|---:|
| Faithfulness | 0.4583 | 0.0000 |
| Answer Relevancy | 0.3253 | 0.3232 |
| Context Precision | 0.8424 | 0.0000 |
| Context Recall | 0.4167 | 0.0000 |

The retrieved top-five chunks included a cited evidence page for only **3 of 6** pilot questions. A broader 14-question retrieval check found **0/14** page hits with the original local BM25 setup and **5/14** with the dense embedding setup. These are source-page hit checks, not answer correctness scores. The pilot's poor retrieval coverage is a major contributor to low answer quality and makes the Ragas means unsuitable as general engine performance estimates.

## Judge consistency review

Faithfulness, Context Precision, and Context Recall were unchanged across the three passes for each frozen pilot answer. Answer Relevancy varied on `financebench_id_00799`: `0.3232`, `0.0000`, `0.0000`. This metric generates a question from the answer and measures embedding cosine similarity to the original question; a local judge's generated question can change even with fixed inputs. Its raw cosine score can be negative, so the evaluator accepts `[-1, 1]` for Answer Relevancy and retains the result without clipping.

Manual review of that case found a retrieval failure. The question asked whether Amcor's quick ratio improved between FY2022 and FY2023. The agent answered that the ratio was irrelevant because it was absent from the retrieved excerpts; the benchmark reference states it increased from 0.67 to 0.69. The cited evidence page was not in the retrieved top five. The Ragas Context Precision value of 1.0 for this case should therefore not be interpreted as proof that the correct page was retrieved. The score disagreement is real, but retrieval and answer errors are the larger issue.

The original 0.94 Faithfulness and 0.93 Answer Relevance claims remain unsupported. The result here is an evidence-backed local integration and judge-consistency pilot for historical financial filings. A broader source mix, stronger retrieval, and human-adjudicated cases are needed before making a market-intelligence quality claim.
