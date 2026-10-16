"""Command-line entry point for production-style Ragas evaluation."""

import argparse
import os

from src.utils.env import load_project_environment

load_project_environment()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AMI Engine Ragas evaluation")
    parser.add_argument("--dataset", default=None, help="Evaluation dataset; defaults to the corpus-aligned local case for local retrieval")
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--tracking-uri", default=None, help="MLflow tracking URI, for example sqlite:///reports/mlflow.db for local runs")
    parser.add_argument("--limit", type=int, default=None, help="Optional small run limit for cost-controlled smoke evaluation")
    parser.add_argument("--judge-repeats", type=int, default=1, help="Score the same frozen agent outputs repeatedly to measure judge stability")
    parser.add_argument("--local-corpus", default=None, help="JSON corpus for local retrieval")
    parser.add_argument("--local-retriever-mode", choices=("bm25", "dense"), default=None)
    parser.add_argument("--frozen-inputs", default=None, help="Rescore saved agent outputs without rerunning retrieval or generation")
    parser.add_argument("--fresh-judge", action="store_true", help="Start a new judge experiment instead of resuming saved scores")
    parser.add_argument(
        "--retriever-backend",
        choices=("local", "databricks"),
        default=os.getenv("RETRIEVER_BACKEND", "local"),
        help="Use local BM25 over exported JSON or live Databricks Vector Search",
    )
    args = parser.parse_args()
    os.environ["RETRIEVER_BACKEND"] = args.retriever_backend
    if args.local_corpus:
        os.environ["LOCAL_RETRIEVAL_CORPUS"] = args.local_corpus
    if args.local_retriever_mode:
        os.environ["LOCAL_RETRIEVER_MODE"] = args.local_retriever_mode
    if args.tracking_uri:
        os.environ["MLFLOW_TRACKING_URI"] = args.tracking_uri
    elif args.retriever_backend == "local":
        os.environ["MLFLOW_TRACKING_URI"] = "sqlite:///reports/mlflow.db"

    dataset = args.dataset or (
        "data/local_eval_dataset.json" if args.retriever_backend == "local"
        else "data/gold_eval_dataset.json"
    )

    from src.evals.run_ragas import run_evaluation

    run_evaluation(
        dataset, args.output_dir, limit=args.limit,
        judge_repeats=args.judge_repeats, frozen_inputs_path=args.frozen_inputs,
        fresh_judge=args.fresh_judge,
    )


if __name__ == "__main__":
    main()
