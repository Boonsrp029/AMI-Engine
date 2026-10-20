"""Synthetic observations captured before the behavior-preserving refactor.

All services are replaced before execution. Fixtures compare artifact contents,
messages, exceptions and service calls rather than an implementation's helpers.
"""

import io
import json
import os
import uuid
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.evals import run_ragas


FIXTURE = Path(__file__).parent / "fixtures" / "refactor" / "evaluation.json"
SCENARIOS = (
    "live", "resume", "frozen", "fresh", "scoring_failure", "mlflow_failure",
    "invalid_score", "no_answer", "no_context", "frozen_revision", "frozen_count",
    "partial_resume", "artifact_failure",
)


def observe_evaluation(root, monkeypatch, scenario):
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(root)
    for key in list(os.environ):
        if key.startswith(("AGENT_", "LLM_", "OLLAMA_", "RAGAS_", "LOCAL_", "RETRIEVER_", "MLFLOW_")):
            monkeypatch.delenv(key)
    for key, value in {
        "RETRIEVER_BACKEND": "local", "LOCAL_RETRIEVAL_CORPUS": "corpus.json",
        "RAGAS_JUDGE_PROVIDER": "ollama", "RAGAS_JUDGE_MODEL": "test-judge",
    }.items():
        monkeypatch.setenv(key, value)
    Path("dataset.json").write_text(json.dumps([
        {"case_id": "a", "query": " Question A ", "reference": ["Fact A", None],
         "doc_name": "sample", "evidence_pages": [0]},
        {"financebench_id": "b", "question": "Question B", "ground_truth": "Fact B"},
    ]), encoding="utf-8")
    Path("corpus.json").write_text('[{"clean_content":"Synthetic evidence"}]', encoding="utf-8")
    events = []
    counts = {}
    fail_scoring = {"enabled": scenario in {"scoring_failure", "partial_resume"}}
    sequence = iter(range(1, 100))
    monkeypatch.setattr(run_ragas.uuid, "uuid4", lambda: uuid.UUID(int=next(sequence)))
    ticks = iter(range(0, 1000, 10))
    monkeypatch.setattr(run_ragas.time, "perf_counter", lambda: next(ticks))

    def query(text):
        events.append(["query", text])
        if scenario == "no_answer":
            return {"response": "", "retrieved_contexts": [], "status": "failed", "error": "example"}
        if scenario == "no_context":
            return {"response": "Answer", "retrieved_contexts": []}
        return {"response": f" Answer {text[-1]} ", "retrieved_contexts": [" Evidence ", ""],
                "citations": [{"doc_name": "sample", "page_num": 0}]}

    def judge():
        events.append(["judge"])
        return object()

    def embeddings(**kwargs):
        events.append(["embeddings", kwargs])
        return object()

    def metric(name):
        class Metric:
            def __init__(self, **kwargs):
                events.append(["metric", name, {k: v for k, v in kwargs.items() if k not in {"llm", "embeddings"}}])

            def score(self, **kwargs):
                events.append(["score", name, kwargs])
                counts[name] = counts.get(name, 0) + 1
                if fail_scoring["enabled"] and name == "faithfulness" and counts[name] == 2:
                    raise RuntimeError("synthetic scoring failure")
                if scenario == "invalid_score" and name == "faithfulness":
                    return SimpleNamespace(value=float("nan"))
                values = {"faithfulness": 0.5, "answer_relevancy": -0.1,
                          "context_precision": 0.75, "context_recall": 1.0}
                value = values[name]
                if name == "faithfulness" and counts[name] > 2:
                    value = 0.75
                return SimpleNamespace(value=value)
        return Metric

    monkeypatch.setattr(run_ragas, "query_agent", query)
    monkeypatch.setattr(run_ragas, "_judge_llm", judge)
    monkeypatch.setattr(run_ragas, "RagasHuggingFaceEmbeddings", embeddings)
    for name, symbol in (("faithfulness", "Faithfulness"), ("answer_relevancy", "AnswerRelevancy"),
                         ("context_precision", "ContextPrecisionWithReference"), ("context_recall", "ContextRecall")):
        monkeypatch.setattr(run_ragas, symbol, metric(name))

    @contextmanager
    def start_run(**kwargs):
        events.append(["start_run", kwargs])
        try:
            yield SimpleNamespace(info=SimpleNamespace(run_id="fixed-run"))
        except Exception as exc:
            events.append(["end_run", type(exc).__name__])
            raise
        else:
            events.append(["end_run", None])

    def log_metrics(values):
        events.append(["log_metrics", values])
        if scenario == "mlflow_failure":
            raise RuntimeError("synthetic tracking failure")

    def log_artifact(path, **kwargs):
        events.append(["artifact", Path(path).as_posix(), kwargs, Path(path).read_text(encoding="utf-8")])
        if scenario == "artifact_failure":
            raise RuntimeError("synthetic artifact failure")

    monkeypatch.setattr(run_ragas.mlflow, "set_experiment", lambda value: events.append(["experiment", value]))
    monkeypatch.setattr(run_ragas.mlflow, "start_run", start_run)
    monkeypatch.setattr(run_ragas.mlflow, "log_params", lambda values: events.append(["params", values]))
    monkeypatch.setattr(run_ragas.mlflow, "log_metrics", log_metrics)
    monkeypatch.setattr(run_ragas.mlflow, "log_metric", lambda *args: events.append(["log_metric", *args]))
    monkeypatch.setattr(run_ragas.mlflow, "log_artifact", log_artifact)

    kwargs = {"judge_repeats": 2}
    if scenario in {"resume", "frozen", "fresh", "frozen_revision", "frozen_count", "partial_resume"}:
        with redirect_stdout(io.StringIO()):
            if scenario == "partial_resume":
                with pytest.raises(RuntimeError, match="synthetic scoring failure"):
                    run_ragas.run_evaluation("dataset.json", "reports", **kwargs)
                fail_scoring["enabled"] = False
            else:
                run_ragas.run_evaluation("dataset.json", "reports", **kwargs)
        events.clear()
        counts.clear()
        if scenario != "resume":
            kwargs["frozen_inputs_path"] = "reports/eval_inputs_latest.json"
        if scenario == "fresh":
            kwargs["fresh_judge"] = True
        if scenario in {"frozen_revision", "frozen_count"}:
            path = Path(kwargs["frozen_inputs_path"])
            data = json.loads(path.read_text(encoding="utf-8"))
            if scenario == "frozen_revision":
                data["dataset_sha256"] = "wrong-revision"
            else:
                data["rows"].pop()
            path.write_text(json.dumps(data), encoding="utf-8")
    if scenario in {"mlflow_failure", "scoring_failure", "invalid_score", "artifact_failure"}:
        Path("reports").mkdir(exist_ok=True)
        Path("reports/eval_report_latest.csv").write_text("previous report\n", encoding="utf-8")
    output = io.StringIO()
    result = error = None
    with redirect_stdout(output):
        try:
            result = run_ragas.run_evaluation("dataset.json", "reports", **kwargs)
        except Exception as exc:
            error = [type(exc).__name__, str(exc)]
    files = {p.name: p.read_text(encoding="utf-8") for p in sorted(Path("reports").iterdir())}
    for name, text in files.items():
        assert (Path("reports") / name).read_bytes() == text.replace("\n", os.linesep).encode("utf-8")
    if result:
        result["report_path"] = Path(result["report_path"]).as_posix()
    stdout = output.getvalue().replace(str(Path("reports/eval_report_latest.csv")), "reports/eval_report_latest.csv")
    return {"result": result, "error": error, "stdout": stdout, "events": events, "files": files}


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_evaluation_matches_pre_refactor_observations(tmp_path, monkeypatch, scenario):
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))[scenario]
    assert observe_evaluation(tmp_path, monkeypatch, scenario) == expected


@pytest.mark.parametrize("payload,message", [
    ([], "Evaluation dataset must be a non-empty JSON array"),
    ({"query": "Q"}, "Evaluation dataset must be a non-empty JSON array"),
    ([1], "Evaluation dataset row 1 must be a JSON object"),
    ([{"question": "Q"}], "Dataset row 1 must include a query and reference/ground_truth"),
])
def test_case_validation_messages(tmp_path, payload, message):
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError) as error:
        run_ragas._load_cases(str(path), None)
    assert str(error.value) == message


def test_case_aliases_and_limit(tmp_path):
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps([
        {"user_input": " Q ", "ground_truth": ["Fact", None, 2]},
        {"question": "Other", "reference": "Unused"},
    ]), encoding="utf-8")
    assert run_ragas._load_cases(str(path), 1) == [{"user_input": " Q ", "ground_truth": ["Fact", None, 2],
        "_normalized_query": "Q", "_normalized_reference": "Fact\n2"}]
