"""Cost-controlled Ragas evaluation over real AMI graph outputs."""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Any

import mlflow
import pandas as pd
from openai import OpenAI
from ragas import EvaluationDataset, evaluate
from ragas.embeddings import HuggingFaceEmbeddings as RagasHuggingFaceEmbeddings
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    AnswerRelevancy,
    ContextPrecisionWithReference,
    ContextRecall,
    Faithfulness,
)
from ragas.run_config import RunConfig

from src.agents.graph import query_agent
from src.utils.env import load_project_environment

load_project_environment()


def _judge_llm():
    provider = os.getenv("RAGAS_JUDGE_PROVIDER", os.getenv("LLM_PROVIDER", "ollama")).lower()
    timeout = float(os.getenv("RAGAS_TIMEOUT_SECONDS", "90"))
    retries = int(os.getenv("RAGAS_MAX_RETRIES", "1"))
    if provider == "ollama":
        model = os.getenv("RAGAS_JUDGE_MODEL", os.getenv("OLLAMA_MODEL", "qwen2.5:14b"))
        client = OpenAI(
            api_key="ollama",
            base_url=f"{os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')}/v1",
            timeout=timeout,
            max_retries=0,
        )
    elif provider in {"groq", "openai"}:
        if provider == "groq":
            key = os.getenv("GROQ_API_KEY")
            if not key:
                raise ValueError("GROQ_API_KEY is required for the Ragas judge")
            client = OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=key,
                max_retries=0,
                timeout=timeout,
            )
            model = os.getenv("RAGAS_JUDGE_MODEL", "llama-3.3-70b-versatile")
        else:
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("OPENAI_API_KEY is required for the Ragas judge")
            client = OpenAI(
                api_key=key,
                max_retries=0,
                timeout=timeout,
            )
            model = os.getenv("RAGAS_JUDGE_MODEL", "gpt-4o-mini")
    else:
        raise ValueError(f"Unsupported RAGAS_JUDGE_PROVIDER: {provider!r}")
    return llm_factory(
        model=model,
        provider="openai",
        client=client,
        run_config=RunConfig(max_retries=retries, timeout=timeout),
    )


def _load_cases(dataset_path: str, limit: int | None) -> list[dict[str, Any]]:
    path = Path(dataset_path)
    if not path.is_file():
        raise FileNotFoundError(f"Evaluation dataset not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("Evaluation dataset must be a non-empty JSON array")
    cases = data[:limit] if limit else data
    for idx, item in enumerate(cases, 1):
        if not isinstance(item, dict):
            raise ValueError(f"Evaluation dataset row {idx} must be a JSON object")
        query = item.get("query") or item.get("user_input") or item.get("question")
        reference = item.get("reference") or item.get("ground_truth")
        if isinstance(reference, list):
            reference = "\n".join(str(part) for part in reference if part is not None)
        if not str(query or "").strip() or not str(reference or "").strip():
            raise ValueError(f"Dataset row {idx} must include a query and reference/ground_truth")
        item["_normalized_query"] = str(query).strip()
        item["_normalized_reference"] = str(reference).strip()
    return cases


def run_evaluation(dataset_path: str, output_dir: str, limit: int | None = None) -> dict[str, Any]:
    """Evaluate live graph results. Missing retrieval or incomplete metrics fail the run."""
    if limit is not None and limit < 1:
        raise ValueError("limit must be a positive integer")
    cases = _load_cases(dataset_path, limit)
    rows: list[dict[str, Any]] = []
    started = time.perf_counter()

    for index, case in enumerate(cases, 1):
        query = case["_normalized_query"]
        print(f"Running live agent query {index}/{len(cases)}")
        result = query_agent(query)
        answer = (result.get("response") or "").strip()
        contexts = [str(c).strip() for c in result.get("retrieved_contexts", []) if str(c).strip()]
        if not answer:
            raise RuntimeError(f"Live agent returned no answer for row {index}; status={result.get('status')!r}")
        if not contexts:
            raise RuntimeError(f"Live agent retrieved no usable context for row {index}; evaluation aborted")
        rows.append({
            "user_input": query,
            "response": answer,
            "retrieved_contexts": contexts,
            "reference": case["_normalized_reference"],
        })

    judge = _judge_llm()
    embeddings = RagasHuggingFaceEmbeddings(
        model=os.getenv("RAGAS_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    )
    metrics = [
        Faithfulness(llm=judge),
        AnswerRelevancy(llm=judge, embeddings=embeddings, strictness=1),
        ContextPrecisionWithReference(llm=judge, name="context_precision"),
        ContextRecall(llm=judge),
    ]
    evaluation_dataset = EvaluationDataset.from_list(rows)
    result = evaluate(
        dataset=evaluation_dataset,
        metrics=metrics,
        raise_exceptions=True,
        show_progress=False,
        batch_size=1,
    )
    frame = result.to_pandas()
    required = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    missing = [name for name in required if name not in frame.columns]
    if missing:
        raise RuntimeError(f"Ragas did not return required metrics: {', '.join(missing)}")
    means = {name: float(pd.to_numeric(frame[name], errors="coerce").mean()) for name in required}
    invalid = [name for name, score in means.items() if not math.isfinite(score)]
    if invalid:
        raise RuntimeError(f"Ragas returned no valid scores for: {', '.join(invalid)}")

    elapsed = time.perf_counter() - started
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    report_path = output_path / "eval_report_latest.csv"
    frame.to_csv(report_path, index=False)
    provider = os.getenv("RAGAS_JUDGE_PROVIDER", os.getenv("LLM_PROVIDER", "ollama")).lower()
    model_defaults = {
        "ollama": os.getenv("OLLAMA_MODEL", "qwen2.5:14b"),
        "groq": "llama-3.3-70b-versatile",
        "openai": "gpt-4o-mini",
    }
    model_name = os.getenv("RAGAS_JUDGE_MODEL", model_defaults.get(provider, ""))
    mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "/Market_Intelligence_Agent_Evaluation"))
    with mlflow.start_run(run_name="AMI_Ragas_Evaluation") as run:
        mlflow.log_params({
            "dataset_path": str(Path(dataset_path)),
            "dataset_size": len(rows),
            "evaluation_mode": "live_agent_ragas",
            "ragas_version": __import__("ragas").__version__,
            "judge_provider": provider,
            "judge_model": model_name,
        })
        mlflow.log_metrics(means)
        mlflow.log_metric("evaluation_elapsed_seconds", elapsed)
        mlflow.log_artifact(str(report_path))
        run_id = run.info.run_id

    print("RAGAS LIVE EVALUATION COMPLETE")
    print(f"Examples: {len(rows)} | elapsed: {elapsed:.2f}s | MLflow run: {run_id}")
    for metric, score in means.items():
        print(f"{metric}: {score:.4f}")
    print(f"Report: {report_path}")
    return {"scores": means, "run_id": run_id, "report_path": str(report_path), "elapsed_seconds": elapsed}
