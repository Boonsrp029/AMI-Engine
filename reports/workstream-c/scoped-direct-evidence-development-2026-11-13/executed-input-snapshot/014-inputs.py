"""Internal case loading and frozen/live evaluation input capture."""

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable


def load_cases(dataset_path: str, limit: int | None) -> list[dict[str, Any]]:
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


def prepare_inputs(
    cases: list[dict[str, Any]], dataset_sha: str, inputs_path: Path,
    frozen_inputs_path: str | None, query_agent: Callable, new_id: Callable,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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
        temporary_inputs_path = inputs_path.parent / f".eval_inputs_{new_id().hex}.json"
        temporary_inputs_path.write_text(
            json.dumps({"dataset_sha256": dataset_sha, "configuration": input_configuration, "rows": rows}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_inputs_path.replace(inputs_path)

    return rows, input_configuration
