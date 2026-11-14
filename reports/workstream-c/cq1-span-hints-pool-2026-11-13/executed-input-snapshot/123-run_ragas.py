"""Cost-controlled Ragas evaluation over real AMI graph outputs."""

from __future__ import annotations

import asyncio
import json
import hashlib
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
from src.evals.inputs import load_cases as _load_cases, prepare_inputs
from src.evals.artifacts import append_checkpoint, checkpoint_file, load_checkpoint, publish_report
from src.evals.scoring import score_row, summarize, validate_scores
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


def _judge_provider() -> str:
    return os.getenv("RAGAS_JUDGE_PROVIDER", os.getenv("LLM_PROVIDER", "ollama")).lower()


def _judge_model(provider: str) -> str:
    defaults = {"groq": "llama-3.3-70b-versatile", "openai": "gpt-4o-mini"}
    default = os.getenv("OLLAMA_MODEL", "ami-llama3.1:8b-4k") if provider == "ollama" else defaults.get(provider, "")
    return os.getenv("RAGAS_JUDGE_MODEL", default)


def _judge_max_tokens(provider: str) -> int:
    return int(os.getenv("RAGAS_MAX_TOKENS", "3072" if provider == "ollama" else "1024"))


def _prompt_version(provider: str) -> str:
    return LOCAL_ANSWER_RELEVANCY_PROMPT_VERSION if provider == "ollama" else "ragas-default"


def _judge_llm(*, return_client=False):
    provider = _judge_provider()
    timeout = float(os.getenv("RAGAS_TIMEOUT_SECONDS", "90"))
    retries = int(os.getenv("RAGAS_MAX_RETRIES", "2"))
    if provider == "ollama":
        model = _judge_model(provider)
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
            model = _judge_model(provider)
        else:
            key = os.getenv("OPENAI_API_KEY")
            if not key:
                raise ValueError("OPENAI_API_KEY is required for the Ragas judge")
            client = AsyncOpenAI(
                api_key=key,
                max_retries=0,
                timeout=timeout,
            )
            model = _judge_model(provider)
    else:
        raise ValueError(f"Unsupported RAGAS_JUDGE_PROVIDER: {provider!r}")
    judge = llm_factory(
        model=model,
        provider="openai",
        client=client,
        max_retries=retries,
        max_tokens=_judge_max_tokens(provider),
    )
    return (judge, client) if return_client else judge


def _metrics(judge, embeddings, provider: str):
    faithfulness = Faithfulness(llm=judge)
    answer_relevancy = AnswerRelevancy(llm=judge, embeddings=embeddings, strictness=1)
    if provider == "ollama":
        answer_relevancy.prompt = LocalAnswerRelevancePrompt()
    context_precision = ContextPrecisionWithReference(llm=judge, name="context_precision")
    context_recall = ContextRecall(llm=judge)
    return {
        "faithfulness": faithfulness, "answer_relevancy": answer_relevancy,
        "context_precision": context_precision, "context_recall": context_recall,
    }


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
    started = time.perf_counter()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    inputs_path = output_path / "eval_inputs_latest.json"
    rows, input_configuration = prepare_inputs(
        cases, dataset_sha, inputs_path, frozen_inputs_path, query_agent, uuid.uuid4,
    )

    judge, judge_client = _judge_llm(return_client=True)
    embeddings = RagasHuggingFaceEmbeddings(
        model=os.getenv("RAGAS_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    )
    provider = _judge_provider()
    model_name = _judge_model(provider)
    inputs_sha = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    judge_config = json.dumps({
        "provider": provider, "model": model_name,
        "answer_relevancy_prompt": _prompt_version(provider),
        "embedding": os.getenv("RAGAS_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "ragas": __import__("ragas").__version__,
        "max_tokens": _judge_max_tokens(provider),
    }, sort_keys=True)
    judge_sha = hashlib.sha256(judge_config.encode("utf-8")).hexdigest()
    checkpoint_path = checkpoint_file(output_path, inputs_sha, judge_sha, fresh_judge, uuid.uuid4)
    completed = load_checkpoint(checkpoint_path)
    required = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    metrics = _metrics(judge, embeddings, provider)
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
    # Keep pooled async connections on one loop across metrics, rows and repeats.
    with asyncio.Runner() as runner:
        try:
            for repeat in range(1, judge_repeats + 1):
                for index, row in enumerate(rows, 1):
                    print(f"Scoring Ragas case {index}/{len(rows)}, judge repeat {repeat}/{judge_repeats}", flush=True)
                    checkpoint_key = (repeat, row["case_id"])
                    if checkpoint_key in completed:
                        scores = completed[checkpoint_key]
                    else:
                        scores = score_row(row, metrics, runner=runner)
                    validate_scores(scores, index)
                    if checkpoint_key not in completed:
                        append_checkpoint(checkpoint_path, repeat, row["case_id"], scores)
                    scored_rows.append({**row, "judge_repeat": repeat, **scores})
        finally:
            runner.run(judge_client.close())
    frame = pd.DataFrame(scored_rows)
    means, ranges = summarize(frame, required)

    elapsed = time.perf_counter() - started
    run_id, report_path = publish_report(
        frame, output_path, new_id=uuid.uuid4, tracking=mlflow,
        parameters=lambda: {
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
            "answer_relevancy_prompt": _prompt_version(provider),
            "frozen_inputs_sha256": inputs_sha,
            "local_corpus_sha256": input_configuration.get("local_corpus_sha256", "unknown"),
            "local_retriever_mode": input_configuration.get("local_retriever_mode", "unknown"),
            "agent_model": input_configuration.get("agent_model", "unknown"),
            "judge_max_tokens": _judge_max_tokens(provider),
        },
        means=means, ranges=ranges, page_hits=page_hits, elapsed=elapsed,
        inputs_path=frozen_inputs_path or inputs_path, checkpoint_path=checkpoint_path,
    )

    print("RAGAS LIVE EVALUATION COMPLETE")
    print(f"Examples: {len(rows)} | elapsed: {elapsed:.2f}s | MLflow run: {run_id}")
    for metric, score in means.items():
        print(f"{metric}: {score:.4f}")
    if judge_repeats > 1:
        for metric, value in ranges.items():
            print(f"{metric}: {value:.4f}")
    print(f"Report: {report_path}")
    return {"scores": means, "ranges": ranges, "run_id": run_id, "report_path": str(report_path), "elapsed_seconds": elapsed}
