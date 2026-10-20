"""Internal metric invocation, validation and summary calculations."""

import math

import pandas as pd


def score_row(row, metrics) -> dict[str, float]:
    return {
        "faithfulness": float(metrics["faithfulness"].score(
            user_input=row["user_input"], response=row["response"],
            retrieved_contexts=row["retrieved_contexts"],
        ).value),
        "answer_relevancy": float(metrics["answer_relevancy"].score(
            user_input=row["user_input"], response=row["response"],
        ).value),
        "context_precision": float(metrics["context_precision"].score(
            user_input=row["user_input"], reference=row["reference"],
            retrieved_contexts=row["retrieved_contexts"],
        ).value),
        "context_recall": float(metrics["context_recall"].score(
            user_input=row["user_input"], retrieved_contexts=row["retrieved_contexts"],
            reference=row["reference"],
        ).value),
    }


def validate_scores(scores: dict[str, float], index: int) -> None:
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


def summarize(frame, required: list[str]) -> tuple[dict[str, float], dict[str, float]]:
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
    return means, ranges
