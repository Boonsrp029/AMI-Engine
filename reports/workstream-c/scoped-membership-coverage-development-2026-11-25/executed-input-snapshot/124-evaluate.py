"""Bounded local comparison; freezes attempts and never overwrites old evaluation data."""

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--corpus", default="data/external/market_sources/prepared/market_chunks.json")
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--judge-repeats", type=int, default=2)
    args = parser.parse_args()
    if args.judge_repeats < 1:
        raise ValueError("judge-repeats must be positive")
    from src.utils.env import load_project_environment
    load_project_environment()
    # The comparison is deliberately local; no hosted-model credentials are used.
    os.environ["AGENT_LLM_PROVIDER"] = "ollama"
    os.environ["RAGAS_JUDGE_PROVIDER"] = "ollama"
    os.environ.setdefault("RAGAS_DO_NOT_TRACK", "true")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ["RETRIEVER_BACKEND"] = "local"
    os.environ["LOCAL_RETRIEVER_MODE"] = "bm25"
    os.environ["LOCAL_RETRIEVAL_CORPUS"] = args.corpus
    os.environ.setdefault("RAGAS_JUDGE_MODEL", "ami-llama3.1:8b-8k")
    # Do not reuse the project's 4k judge default for this 8k pilot.
    if os.environ["RAGAS_JUDGE_MODEL"] == "ami-llama3.1:8b-4k":
        os.environ["RAGAS_JUDGE_MODEL"] = "ami-llama3.1:8b-8k"
    from src.agents.graph import query_agent
    from src.pilot.engine import Corpus, PilotEngine, PROMPT_VERSION
    from src.evals.run_ragas import run_evaluation
    import mlflow

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(Path("data/pilot/manifest.json").read_text(encoding="utf-8"))
    case_path = Path("data/pilot/cases.json")
    if hashlib.sha256(case_path.read_bytes()).hexdigest() != manifest["sha256"]["cases.json"]:
        raise ValueError("Pilot case split has changed")
    all_cases = json.loads(case_path.read_text(encoding="utf-8"))
    selected = [next(c for c in all_cases if c["case_id"] == case_id) for case_id in manifest["comparison_ids"]]
    corpus = Corpus(args.corpus)
    engine = PilotEngine(corpus)
    identity = {"case_sha256": manifest["sha256"]["cases.json"], "corpus_sha256": corpus.sha,
                "workflow_prompt": PROMPT_VERSION, "agent_model": os.getenv("AGENT_LLM_MODEL", "ami-llama3.1:8b-4k"),
                "judge_model": os.environ["RAGAS_JUDGE_MODEL"]}
    identity_path = output / "identity.json"
    if identity_path.exists() and json.loads(identity_path.read_text(encoding="utf-8")) != identity:
        raise ValueError("Comparison configuration changed; use a new output directory")
    write_json(identity_path, identity)
    summary = {"identity": identity, "variants": {}, "human_review": "pending", "external_reviewer_usage": "pending"}
    for variant in ("legacy", "workflow"):
        rows, cases, attempts = [], [], []
        for case in selected:
            frozen_path = output / f"freeze_{variant}_{case['case_id']}.json"
            if frozen_path.exists():
                record = json.loads(frozen_path.read_text(encoding="utf-8"))
            else:
                print(f"Generating {variant}: {case['case_id']}", flush=True)
                started = time.perf_counter()
                events = []
                try:
                    if variant == "legacy":
                        result = query_agent(case["query"])
                        response, contexts, citations = result.get("response", ""), result.get("retrieved_contexts", []), result.get("citations", [])
                        details = {"status": result.get("status"), "error": result.get("error")}
                    else:
                        result = engine.run(case["query"], lambda kind, payload: events.append({"kind": kind, "payload": payload}))
                        response = "\n".join(claim["text"] for claim in result["draft"]["claims"])
                        contexts = [source["content"] for source in result["sources"].values()]
                        citations = list(result["sources"].values())
                        details = {"draft": result["draft"], "metrics": result["metrics"], "events": events}
                    record = {"case_id": case["case_id"], "status": "answered" if response.strip() and contexts else "unanswered",
                              "row": {"case_id": case["case_id"], "user_input": case["query"], "reference": case["reference"],
                                  "response": response, "retrieved_contexts": contexts, "citations": citations,
                                  "doc_name": case.get("doc_name"), "evidence_pages": case.get("evidence_pages", [])},
                              "details": details, "elapsed_seconds": time.perf_counter() - started}
                except Exception as exc:
                    record = {"case_id": case["case_id"], "status": "failed", "error_type": type(exc).__name__,
                              "events": events, "elapsed_seconds": time.perf_counter() - started}
                write_json(frozen_path, record)
            attempts.append({key: record[key] for key in ("case_id", "status", "elapsed_seconds")})
            if record["status"] == "answered":
                rows.append(record["row"])
                cases.append(case)
        dataset = output / f"selected_cases_{variant}.json"
        write_json(dataset, cases)
        inputs = output / f"inputs_{variant}.json"
        write_json(inputs, {"dataset_sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(), "rows": rows,
            "configuration": {"retriever_backend": "local", "local_retriever_mode": "bm25", "agent_model": identity["agent_model"],
                              "local_corpus_sha256": corpus.sha}})
        summary["variants"][variant] = {"attempts": attempts, "answered": len(rows), "total": len(selected)}
        write_json(output / "comparison.json", summary)
        if rows and not args.generate_only:
            os.environ["MLFLOW_TRACKING_URI"] = f"sqlite:///{(output / 'tracking.sqlite3').resolve().as_posix()}"
            mlflow.set_tracking_uri(os.environ["MLFLOW_TRACKING_URI"])
            os.environ["MLFLOW_EXPERIMENT_NAME"] = "/AMI_Analyst_Pilot_Comparison"
            if mlflow.get_experiment_by_name(os.environ["MLFLOW_EXPERIMENT_NAME"]) is None:
                mlflow.create_experiment(os.environ["MLFLOW_EXPERIMENT_NAME"],
                    artifact_location=(output / "mlflow_artifacts").resolve().as_uri())
            try:
                summary["variants"][variant]["ragas"] = run_evaluation(
                    str(dataset), str(output / variant), judge_repeats=args.judge_repeats, frozen_inputs_path=str(inputs))
            except Exception as exc:
                summary["variants"][variant]["ragas_error"] = type(exc).__name__
                # This harness permits only the local judge; retain diagnostic causes
                # in its command log while keeping provider failures out of the UI.
                traceback.print_exception(exc)
            write_json(output / "comparison.json", summary)
    rubric_path = output / "human_review.csv"
    if not rubric_path.exists():
        with rubric_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["case_id", "variant", "reviewer", "correctness_1_to_5", "completeness_1_to_5",
                "unsupported_claims", "missing_facts", "citation_support", "notes", "review_status"])
            writer.writeheader()
            for case in selected:
                for variant in ("legacy", "workflow"):
                    writer.writerow({"case_id": case["case_id"], "variant": variant, "review_status": "pending"})
    print(f"Comparison saved to {output}. Human adjudication and external reviewer feedback remain pending.")
    return int(any("ragas_error" in variant for variant in summary["variants"].values()))


if __name__ == "__main__":
    sys.exit(main())
