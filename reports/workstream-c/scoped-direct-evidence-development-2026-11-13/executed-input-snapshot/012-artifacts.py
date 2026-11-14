"""Internal checkpoint persistence and atomic evaluation report publishing."""

import json
import os
from pathlib import Path
from typing import Callable


def checkpoint_file(output_path: Path, inputs_sha: str, judge_sha: str, fresh: bool, new_id: Callable) -> Path:
    path = output_path / f"eval_checkpoint_{inputs_sha[:12]}_{judge_sha[:12]}.jsonl"
    if fresh:
        path = output_path / f"eval_checkpoint_{inputs_sha[:12]}_{judge_sha[:12]}_{new_id().hex[:8]}.jsonl"
    return path


def load_checkpoint(path: Path) -> dict[tuple[int, str], dict[str, float]]:
    completed: dict[tuple[int, str], dict[str, float]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                completed[(record["judge_repeat"], record["case_id"])] = record["scores"]
    return completed


def append_checkpoint(path: Path, repeat: int, case_id: str, scores: dict[str, float]) -> None:
    with path.open("a", encoding="utf-8") as checkpoint:
        checkpoint.write(json.dumps({
            "judge_repeat": repeat, "case_id": case_id, "scores": scores,
        }) + "\n")


def publish_report(
    frame, output_path: Path, *, new_id: Callable, tracking, parameters: Callable,
    means: dict[str, float], ranges: dict[str, float], page_hits: list[bool],
    elapsed: float, inputs_path, checkpoint_path: Path,
) -> tuple[str, Path]:
    """Publish only after tracking succeeds; retain the previous report on failure.

    Parameters are evaluated inside the MLflow run, at the original read boundary.
    The caller supplies tracking and ID providers to retain its injection points.
    """
    report_path = output_path / "eval_report_latest.csv"
    pending_report_path = output_path / f".eval_report_{new_id().hex}.csv"
    frame.to_csv(pending_report_path, index=False)
    try:
        tracking.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "/Market_Intelligence_Agent_Evaluation"))
        with tracking.start_run(run_name="AMI_Ragas_Evaluation") as run:
            tracking.log_params(parameters())
            tracking.log_metrics(means)
            tracking.log_metrics(ranges)
            if page_hits:
                tracking.log_metric("evidence_page_hit_at_k", sum(page_hits) / len(page_hits))
            tracking.log_metric("evaluation_elapsed_seconds", elapsed)
            tracking.log_artifact(str(pending_report_path), artifact_path="evaluation")
            tracking.log_artifact(str(inputs_path), artifact_path="evaluation")
            tracking.log_artifact(str(checkpoint_path), artifact_path="evaluation")
            run_id = run.info.run_id
        pending_report_path.replace(report_path)
    finally:
        pending_report_path.unlink(missing_ok=True)
    return run_id, report_path
