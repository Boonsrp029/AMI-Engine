import os
import re
import json
import argparse
import warnings
import pandas as pd
from datasets import Dataset
import mlflow
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Ragas & LangChain imports
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.outputs import ChatResult
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

# Import agent execution function from main.py
from main import query_agent


FALLBACK_LOCAL_MODELS = [
    "llama3.1:8b",
    "qwen2.5:7b",
    "llama3:8b",
    "mistral:7b",
]

FALLBACK_GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama3-70b-8192",
    "qwen/qwen3.6-27b",
]


class CleanReasoningChatOpenAI(ChatOpenAI):
    """Custom ChatOpenAI subclass that strips reasoning tags and markdown code fences."""
    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove <think>...</think> reasoning tags
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Extract content from ```json ... ``` code blocks if present
        json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL)
        if json_match:
            text = json_match.group(1)
        return text.strip()

    def _generate(self, *args, **kwargs) -> ChatResult:
        result = super()._generate(*args, **kwargs)
        for gen in result.generations:
            gen.text = self._clean_text(gen.text)
            if hasattr(gen, "message") and hasattr(gen.message, "content"):
                if isinstance(gen.message.content, str):
                    gen.message.content = self._clean_text(gen.message.content)
        return result

    async def _agenerate(self, *args, **kwargs) -> ChatResult:
        result = await super()._agenerate(*args, **kwargs)
        for gen in result.generations:
            gen.text = self._clean_text(gen.text)
            if hasattr(gen, "message") and hasattr(gen.message, "content"):
                if isinstance(gen.message.content, str):
                    gen.message.content = self._clean_text(gen.message.content)
        return result


class CleanReasoningChatOllama(ChatOllama):
    """Custom ChatOllama subclass that enforces high context windows and strips markdown fencings."""
    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Remove reasoning tags
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Unwrap markdown JSON codeblocks for Ragas parser
        json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL)
        if json_match:
            text = json_match.group(1)
        return text.strip()

    def _generate(self, *args, **kwargs) -> ChatResult:
        result = super()._generate(*args, **kwargs)
        for gen in result.generations:
            gen.text = self._clean_text(gen.text)
            if hasattr(gen, "message") and hasattr(gen.message, "content"):
                if isinstance(gen.message.content, str):
                    gen.message.content = self._clean_text(gen.message.content)
        return result

    async def _agenerate(self, *args, **kwargs) -> ChatResult:
        result = await super()._agenerate(*args, **kwargs)
        for gen in result.generations:
            gen.text = self._clean_text(gen.text)
            if hasattr(gen, "message") and hasattr(gen.message, "content"):
                if isinstance(gen.message.content, str):
                    gen.message.content = self._clean_text(gen.message.content)
        return result


def get_evaluator_llm(model_name: str = None):
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "ollama":
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        target_model = model_name or os.getenv("OLLAMA_MODEL", FALLBACK_LOCAL_MODELS[0])

        llm = CleanReasoningChatOllama(
            base_url=ollama_base_url.rstrip("/"),
            model=target_model,
            temperature=0.0,
            num_ctx=8192,
            num_predict=2048,
        )

    elif provider == "groq":
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY is missing from environment variables.")

        target_model = model_name or os.getenv("GROQ_MODEL", FALLBACK_GROQ_MODELS[0])

        llm = CleanReasoningChatOpenAI(
            base_url="[https://api.groq.com/openai/v1](https://api.groq.com/openai/v1)",
            api_key=groq_api_key,
            model=target_model,
            temperature=0.0,
            max_tokens=4096,
            max_retries=5,
            timeout=120.0,
        )

    else:
        llm = CleanReasoningChatOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.0,
            max_tokens=4096,
        )

    return LangchainLLMWrapper(llm)


def get_evaluator_embeddings():
    lc_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return LangchainEmbeddingsWrapper(lc_embeddings)


def load_eval_dataset(dataset_path: str) -> list:
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Evaluation dataset not found at: {dataset_path}")
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_with_fallback(dataset: Dataset, eval_metrics: list, evaluator_embeddings):
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "ollama":
        env_model = os.getenv("OLLAMA_MODEL")
        candidate_models = (
            [env_model] + [m for m in FALLBACK_LOCAL_MODELS if m != env_model]
            if env_model
            else FALLBACK_LOCAL_MODELS
        )
    elif provider == "groq":
        env_model = os.getenv("GROQ_MODEL")
        candidate_models = (
            [env_model] + [m for m in FALLBACK_GROQ_MODELS if m != env_model]
            if env_model
            else FALLBACK_GROQ_MODELS
        )
    else:
        candidate_models = [None]

    last_exception = None

    for model in candidate_models:
        try:
            print(f"Attempting evaluation with judge model: {model or 'Default Provider Model'}...")
            evaluator_llm = get_evaluator_llm(model_name=model)

            # max_workers=1 prevents parallel overloading of local Ollama
            results = evaluate(
                dataset=dataset,
                metrics=eval_metrics,
                llm=evaluator_llm,
                embeddings=evaluator_embeddings,
                max_workers=1,
                raise_exceptions=False,
            )
            return results

        except Exception as err:
            print(f"[WARNING] Evaluation failed on model '{model}': {err}")
            print("Initiating fallback to next candidate model...")
            last_exception = err

    raise RuntimeError(f"All candidate evaluation models failed. Last error: {last_exception}")


def run_dynamic_evaluation(dataset_path: str, output_dir: str):
    print(f"Loading evaluation dataset from: {dataset_path}")
    raw_data = load_eval_dataset(dataset_path)

    questions = []
    answers = []
    contexts_list = []
    ground_truths = []

    print(f"Executing agent pipeline across {len(raw_data)} eval queries...")
    for idx, item in enumerate(raw_data, 1):
        query = item.get("query") or item.get("question") or item.get("user_input", "")

        raw_gt = item.get("ground_truth") or item.get("reference", "")
        if isinstance(raw_gt, list):
            ground_truth_str = raw_gt[0] if raw_gt else ""
        else:
            ground_truth_str = str(raw_gt)

        if "answer" in item and "contexts" in item:
            answer = item["answer"]
            retrieved_contexts = item["contexts"]
        elif "response" in item and "retrieved_contexts" in item:
            answer = item["response"]
            retrieved_contexts = item["retrieved_contexts"]
        else:
            response_payload = query_agent(query)
            answer = response_payload.get("answer") or response_payload.get("response", "")
            retrieved_contexts = response_payload.get("retrieved_contexts") or response_payload.get("contexts", [])

        if isinstance(retrieved_contexts, str):
            retrieved_contexts = [retrieved_contexts]

        clean_contexts = []
        for ctx in retrieved_contexts:
            if isinstance(ctx, dict):
                text_val = ctx.get("content") or ctx.get("text") or ctx.get("page_content") or str(ctx)
                clean_contexts.append(text_val)
            elif ctx is not None:
                clean_contexts.append(str(ctx))

        if not clean_contexts:
            clean_contexts = ["No context retrieved."]

        questions.append(query)
        answers.append(answer)
        contexts_list.append(clean_contexts)
        ground_truths.append(ground_truth_str)

    eval_dict = {
        "user_input": questions,
        "question": questions,
        "response": answers,
        "answer": answers,
        "retrieved_contexts": contexts_list,
        "contexts": contexts_list,
        "reference": ground_truths,
        "ground_truth": ground_truths,
    }
    dataset = Dataset.from_dict(eval_dict)

    evaluator_embeddings = get_evaluator_embeddings()

    answer_relevancy.strictness = 1

    eval_metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ]

    print("Computing metrics via Ragas...")
    results = evaluate_with_fallback(dataset, eval_metrics, evaluator_embeddings)

    result_df = results.to_pandas()

    faith_col = "faithfulness" if "faithfulness" in result_df.columns else result_df.columns[0]
    rel_col = "answer_relevancy" if "answer_relevancy" in result_df.columns else result_df.columns[1]
    prec_col = "context_precision" if "context_precision" in result_df.columns else result_df.columns[2]
    rec_col = "context_recall" if "context_recall" in result_df.columns else result_df.columns[3]

    mean_faithfulness = float(result_df[faith_col].fillna(0).mean())
    mean_relevance = float(result_df[rel_col].fillna(0).mean())
    mean_precision = float(result_df[prec_col].fillna(0).mean())
    mean_recall = float(result_df[rec_col].fillna(0).mean())

    passed = (
        mean_faithfulness >= 0.90
        and mean_relevance >= 0.90
        and mean_precision >= 0.90
        and mean_recall >= 0.85
    )
    status_str = "PASSED (CI Gate Approved)" if passed else "FAILED (Threshold Missed)"

    os.makedirs(output_dir, exist_ok=True)
    report_csv_path = os.path.join(output_dir, "eval_report_latest.csv")
    result_df.to_csv(report_csv_path, index=False)

    mlflow.set_experiment("/Market_Intelligence_Agent_Tracing")
    with mlflow.start_run() as run:
        mlflow.log_param("dataset_path", dataset_path)
        mlflow.log_param("dataset_size", len(raw_data))
        mlflow.log_metric("faithfulness", mean_faithfulness)
        mlflow.log_metric("answer_relevance", mean_relevance)
        mlflow.log_metric("context_precision", mean_precision)
        mlflow.log_metric("context_recall", mean_recall)
        mlflow.log_artifact(report_csv_path)

        run_id = run.info.run_id

    print("\n" + "=" * 50)
    print("RAGAS DYNAMIC EVALUATION COMPLETE")
    print("=" * 50)
    print(f"Faithfulness Score     : {mean_faithfulness:.4f}")
    print(f"Answer Relevancy Score : {mean_relevance:.4f}")
    print(f"Context Precision      : {mean_precision:.4f}")
    print(f"Context Recall         : {mean_recall:.4f}")
    print("-" * 50)
    print(f"Status                 : {status_str}")
    print(f"MLflow Run ID          : {run_id}")
    print(f"Detailed Report        : {report_csv_path}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dynamic Ragas Evaluation Pipeline")
    parser.add_argument("--dataset", required=True, help="Path to evaluation JSON dataset")
    parser.add_argument("--output-dir", required=True, help="Directory to save evaluation reports")

    args = parser.parse_args()
    run_dynamic_evaluation(args.dataset, args.output_dir)