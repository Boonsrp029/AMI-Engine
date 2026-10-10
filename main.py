"""Command-line entry point for production-style Ragas evaluation."""

import argparse

from src.utils.env import load_project_environment

load_project_environment()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AMI Engine Ragas evaluation")
    parser.add_argument("--dataset", default="data/gold_eval_dataset.json")
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--limit", type=int, default=None, help="Optional small run limit for cost-controlled smoke evaluation")
    args = parser.parse_args()

    from src.evals.run_ragas import run_evaluation

    run_evaluation(args.dataset, args.output_dir, limit=args.limit)


if __name__ == "__main__":
    main()
