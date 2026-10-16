"""Cost-controlled Ragas evaluation over real AMI graph outputs."""

from __future__ import annotations

import json
import hashlib
import math
import os
import time
import uuid
from pathlib import Path
from typing import Any

import mlflow
import pandas as pd
from openai import AsyncOpenAI
from ragas.embeddings import HuggingFaceEmbeddings as RagasHuggingFaceEmbeddings
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    AnswerRelevancy,
    ContextPrecisionWithReference,
    ContextRecall,
    Faithfulness,
)
from ragas.metrics.collections.answer_relevancy.util import AnswerRelevancePrompt

from src.agents.graph import query_agent
from src.utils.env import load_project_environment

load_project_environment()

LOCAL_ANSWER_RELEVANCY_PROMPT_VERSION = "concise-json-v1"


class LocalAnswerRelevancePrompt(AnswerRelevancePrompt):
    """Keep the small local judge focused on values, not the JSON schema."""

    def to_string(self, data):
        response = json.dumps(data.response, ensure_ascii=False)
        return (
            "Generate one question that the answer below would answer. "
            "Set noncommittal to 1 only if the answer is evasive or says it does not know; "
            "otherwise set it to 0. Return only a JSON object with exactly two fields: "
            '{"question":"your question","noncommittal":0}. '
            "Do not return a schema, description, explanation, or markdown.\n"
            f"Answer: {response}\nJSON:"
        )


def _judge_llm():
    provider = os.getenv("RAGAS_JUDGE_PROVIDER", os.getenv("LLM_PROVIDER", "ollama")).lower()
    timeout = float(os.getenv("RAGAS_TIMEOUT_SECONDS", "90"))
    retries = int(os.getenv("RAGAS_MAX_RETRIES", "2"))
    if provider == "ollama":
        model = os.getenv("RAGAS_JUDGE_MODEL", os.getenv("OLLAMA_MODEL", "ami-llama3.1:8b-4k"))
        client = AsyncOpenAI(
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
            client = AsyncOpenAI(
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
            client = AsyncOpenAI(
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
        max_retries=retries,
        max_tokens=int(os.getenv("RAGAS_MAX_TOKENS", "3072" if provider == "ollama" else "1024")),
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


def run_evaluation(
    dataset_path: str, output_dir: str, limit: int | None = None,
    judge_repeats: int = 1, frozen_inputs_path: str | None = None,
    fresh_judge: bool = False,
) -> dict[str, Any]:
    """Evaluate live graph results. Missing retrieval or incomplete metrics fail the run."""
    if limit is not None and limit < 1:
        raise ValueError("limit must be a positive integer")
    if judge_repeats < 1:
        raise ValueError("judge_repeats must be a positive integer")
    cases = _load_cases(dataset_path, limit)
    dataset_sha = hashlib.sha256(Path(dataset_path).read_bytes()).hexdigest()
    rows: list[dict[str, Any]] = []
    started = time.perf_counter()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    inputs_path = output_path / "eval_inputs_latest.json"
    if frozen_inputs_path:
        frozen = json.loads(Path(frozen_inputs_path).read_text(encoding="utf-8"))
        if frozen.get("dataset_sha256") != dataset_sha:
            raise ValueError("Frozen inputs were generated from a different dataset revision")
        rows = frozen["rows"]
        input_configuration = frozen.get("configuration", {})
        if len(rows) != len(cases):
            raise ValueError("Frozen input count does not match the requested evaluation cases")
    else:
        corpus_path = Path(os.getenv("LOCAL_RETRIEVAL_CORPUS", "data/silver_level"))
        input_configuration = {
            "retriever_backend": os.getenv("RETRIEVER_BACKEND", "databricks"),
            "local_retriever_mode": os.getenv("LOCAL_RETRIEVER_MODE", "bm25"),
            "local_corpus": str(corpus_path),
            "local_corpus_sha256": hashlib.sha256(corpus_path.read_bytes()).hexdigest()
            if corpus_path.is_file() else "not_single_file",
            "agent_provider": os.getenv("AGENT_LLM_PROVIDER", os.getenv("LLM_PROVIDER", "ollama")),
            "agent_model": os.getenv("AGENT_LLM_MODEL", os.getenv("OLLAMA_MODEL", "ami-llama3.1:8b-4k")),
        }
        for index, case in enumerate(cases, 1):
            query = case["_normalized_query"]
            print(f"Running live agent query {index}/{len(cases)}", flush=True)
            result = query_agent(query)
            answer = (result.get("response") or "").strip()
            contexts = [str(c).strip() for c in result.get("retrieved_contexts", []) if str(c).strip()]
            if not answer:
                raise RuntimeError(
                    f"Live agent returned no answer for row {index}; "
                    f"status={result.get('status')!r}; error={result.get('error')!r}"
                )
            if not contexts:
                raise RuntimeError(f"Live agent retrieved no usable context for row {index}; evaluation aborted")
            rows.append({
                "case_id": str(case.get("case_id") or case.get("financebench_id") or index),
                "user_input": query,
                "response": answer,
                "retrieved_contexts": contexts,
                "reference": case["_normalized_reference"],
                "doc_name": case.get("doc_name"),
                "evidence_pages": case.get("evidence_pages", []),
                "citations": result.get("citations", []),
            })
        temporary_inputs_path = output_path / f".eval_inputs_{uuid.uuid4().hex}.json"
        temporary_inputs_path.write_text(
            json.dumps({"dataset_sha256": dataset_sha, "configuration": input_configuration, "rows": rows}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_inputs_path.replace(inputs_path)

    judge = _judge_llm()
    embeddings = RagasHuggingFaceEmbeddings(
        model=os.getenv("RAGAS_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    )
    provider = os.getenv("RAGAS_JUDGE_PROVIDER", os.getenv("LLM_PROVIDER", "ollama")).lower()
    model_defaults = {
        "ollama": os.getenv("OLLAMA_MODEL", "ami-llama3.1:8b-4k"),
        "groq": "llama-3.3-70b-versatile",
        "openai": "gpt-4o-mini",
    }
    model_name = os.getenv("RAGAS_JUDGE_MODEL", model_defaults.get(provider, ""))
    inputs_sha = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    judge_config = json.dumps({
        "provider": provider, "model": model_name,
        "answer_relevancy_prompt": LOCAL_ANSWER_RELEVANCY_PROMPT_VERSION if provider == "ollama" else "ragas-default",
        "embedding": os.getenv("RAGAS_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "ragas": __import__("ragas").__version__,
        "max_tokens": int(os.getenv("RAGAS_MAX_TOKENS", "3072" if provider == "ollama" else "1024")),
    }, sort_keys=True)
    judge_sha = hashlib.sha256(judge_config.encode("utf-8")).hexdigest()
    checkpoint_path = output_path / f"eval_checkpoint_{inputs_sha[:12]}_{judge_sha[:12]}.jsonl"
    if fresh_judge:
        checkpoint_path = output_path / f"eval_checkpoint_{inputs_sha[:12]}_{judge_sha[:12]}_{uuid.uuid4().hex[:8]}.jsonl"
    completed: dict[tuple[int, str], dict[str, float]] = {}
    if checkpoint_path.exists():
        for line in checkpoint_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                completed[(record["judge_repeat"], record["case_id"])] = record["scores"]
    required = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    faithfulness = Faithfulness(llm=judge)
    answer_relevancy = AnswerRelevancy(llm=judge, embeddings=embeddings, strictness=1)
    if provider == "ollama":
        answer_relevancy.prompt = LocalAnswerRelevancePrompt()
    context_precision = ContextPrecisionWithReference(llm=judge, name="context_precision")
    context_recall = ContextRecall(llm=judge)
    scored_rows = []
    page_hits = []
    for row in rows:
        if row.get("doc_name") and row.get("evidence_pages"):
            hit = any(
                citation.get("doc_name") == row["doc_name"]
                and citation.get("page_num") in row["evidence_pages"]
                for citation in row.get("citations", [])
            )
            page_hits.append(hit)
            row["evidence_page_hit_at_k"] = int(hit)
    for repeat in range(1, judge_repeats + 1):
        for index, row in enumerate(rows, 1):
            print(f"Scoring Ragas case {index}/{len(rows)}, judge repeat {repeat}/{judge_repeats}", flush=True)
            checkpoint_key = (repeat, row["case_id"])
            if checkpoint_key in completed:
                scores = completed[checkpoint_key]
            else:
                scores = {
                    "faithfulness": float(faithfulness.score(
                        user_input=row["user_input"], response=row["response"],
                        retrieved_contexts=row["retrieved_contexts"],
                    ).value),
                    "answer_relevancy": float(answer_relevancy.score(
                        user_input=row["user_input"], response=row["response"],
                    ).value),
                    "context_precision": float(context_precision.score(
                        user_input=row["user_input"], reference=row["reference"],
                        retrieved_contexts=row["retrieved_contexts"],
                    ).value),
                    "context_recall": float(context_recall.score(
                        user_input=row["user_input"], retrieved_contexts=row["retrieved_contexts"],
                        reference=row["reference"],
                    ).value),
                }
            bounds = {"answer_relevancy": (-1.0, 1.0)}
            invalid = [
                f"{name}={score!r}" for name, score in scores.items()
                if not math.isfinite(score) or not (
                    bounds.get(name, (0.0, 1.0))[0] - 1e-6
                    <= score <= bounds.get(name, (0.0, 1.0))[1] + 1e-6
                )
            ]
            if invalid:
                raise RuntimeError(f"Ragas returned invalid scores for case {index}: {', '.join(invalid)}")
            if checkpoint_key not in completed:
                with checkpoint_path.open("a", encoding="utf-8") as checkpoint:
                    checkpoint.write(json.dumps({
                        "judge_repeat": repeat, "case_id": row["case_id"], "scores": scores,
                    }) + "\n")
            scored_rows.append({**row, "judge_repeat": repeat, **scores})
    frame = pd.DataFrame(scored_rows)
    means = {name: float(pd.to_numeric(frame[name], errors="coerce").mean()) for name in required}
    ranges = {
        f"{name}_max_case_range": float(
            frame.groupby("case_id")[name].agg(lambda values: values.max() - values.min()).max()
        )
        for name in required
    }
    invalid = [name for name, score in means.items() if not math.isfinite(score)]
    if invalid:
        raise RuntimeError(f"Ragas returned no valid scores for: {', '.join(invalid)}")

    elapsed = time.perf_counter() - started
    report_path = output_path / "eval_report_latest.csv"
    pending_report_path = output_path / f".eval_report_{uuid.uuid4().hex}.csv"
    frame.to_csv(pending_report_path, index=False)
    try:
        mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "/Market_Intelligence_Agent_Evaluation"))
        with mlflow.start_run(run_name="AMI_Ragas_Evaluation") as run:
            mlflow.log_params({
                "dataset_path": str(Path(dataset_path)),
                "dataset_sha256": dataset_sha,
                "dataset_size": len(rows),
                "judge_repeats": judge_repeats,
                "fresh_judge": fresh_judge,
                "evaluation_mode": "frozen_agent_ragas" if frozen_inputs_path else "live_agent_ragas",
                "retriever_backend": os.getenv("RETRIEVER_BACKEND", "databricks"),
                "ragas_version": __import__("ragas").__version__,
                "judge_provider": provider,
                "judge_model": model_name,
                "answer_relevancy_prompt": LOCAL_ANSWER_RELEVANCY_PROMPT_VERSION if provider == "ollama" else "ragas-default",
                "frozen_inputs_sha256": inputs_sha,
                "local_corpus_sha256": input_configuration.get("local_corpus_sha256", "unknown"),
                "local_retriever_mode": input_configuration.get("local_retriever_mode", "unknown"),
                "agent_model": input_configuration.get("agent_model", "unknown"),
                "judge_max_tokens": int(os.getenv("RAGAS_MAX_TOKENS", "3072" if provider == "ollama" else "1024")),
            })
            mlflow.log_metrics(means)
            mlflow.log_metrics(ranges)
            if page_hits:
                mlflow.log_metric("evidence_page_hit_at_k", sum(page_hits) / len(page_hits))
            mlflow.log_metric("evaluation_elapsed_seconds", elapsed)
            mlflow.log_artifact(str(pending_report_path), artifact_path="evaluation")
            mlflow.log_artifact(str(frozen_inputs_path or inputs_path), artifact_path="evaluation")
            mlflow.log_artifact(str(checkpoint_path), artifact_path="evaluation")
            run_id = run.info.run_id
        pending_report_path.replace(report_path)
    finally:
        pending_report_path.unlink(missing_ok=True)

    print("RAGAS LIVE EVALUATION COMPLETE")
    print(f"Examples: {len(rows)} | elapsed: {elapsed:.2f}s | MLflow run: {run_id}")
    for metric, score in means.items():
        print(f"{metric}: {score:.4f}")
    if judge_repeats > 1:
        for metric, value in ranges.items():
            print(f"{metric}: {value:.4f}")
    print(f"Report: {report_path}")
    return {"scores": means, "ranges": ranges, "run_id": run_id, "report_path": str(report_path), "elapsed_seconds": elapsed}
