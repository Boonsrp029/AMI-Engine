"""Small, dependency-free BM25 retriever for exported Medallion JSON data."""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOKEN_PATTERN = re.compile(r"[\w]+", re.UNICODE)


def _read_records(corpus_path: Path) -> list[tuple[dict[str, Any], str]]:
    files = sorted(corpus_path.rglob("*.json")) if corpus_path.is_dir() else [corpus_path]
    records: list[tuple[dict[str, Any], str]] = []
    for file_path in files:
        if not file_path.is_file():
            continue
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list):
            continue
        layer = file_path.parent.name.removesuffix("_level")
        for row in payload:
            if not isinstance(row, dict):
                continue
            content = (
                row.get("clean_content")
                or row.get("raw_content")
                or row.get("aggregated_context")
            )
            if not isinstance(content, str) or not content.strip():
                continue
            metadata = {
                "feed_id": row.get("feed_id") or f"{layer}:{len(records) + 1}",
                "title": row.get("title") or "; ".join(row.get("source_titles", [])),
                "source": row.get("source"),
                "sector": row.get("sector"),
                "medallion_layer": layer,
                "doc_name": row.get("doc_name"),
                "page_num": row.get("page_num"),
            }
            metadata = {key: value for key, value in metadata.items() if value not in (None, "")}
            search_text = f"{metadata.get('title', '')} {content}".strip()
            records.append((metadata, search_text))
    if not records:
        raise ValueError(f"No searchable records found in local corpus: {corpus_path}")
    return records


def _tokens(text: str) -> list[str]:
    return [token.casefold() for token in TOKEN_PATTERN.findall(text)]


def _bm25_scores(query: str, documents: list[list[str]]) -> list[float]:
    query_terms = _tokens(query)
    if not query_terms:
        return [0.0] * len(documents)

    doc_freq = Counter(term for doc in documents for term in set(doc))
    average_length = sum(map(len, documents)) / max(len(documents), 1)
    k1, b = 1.5, 0.75
    scores: list[float] = []
    for doc in documents:
        term_freq = Counter(doc)
        score = 0.0
        for term in query_terms:
            frequency = term_freq.get(term, 0)
            if not frequency:
                continue
            inverse_frequency = math.log1p(
                (len(documents) - doc_freq[term] + 0.5) / (doc_freq[term] + 0.5)
            )
            length_norm = k1 * (1 - b + b * len(doc) / max(average_length, 1))
            score += inverse_frequency * frequency * (k1 + 1) / (frequency + length_norm)
        scores.append(score)
    return scores


@lru_cache(maxsize=2)
def _dense_index(corpus_path: str, corpus_mtime: int, model_name: str):
    """Cache a local embedding index across agent queries in one evaluation run."""
    from sentence_transformers import SentenceTransformer

    records = _read_records(Path(corpus_path))
    model = SentenceTransformer(model_name, local_files_only=True)
    vectors = model.encode(
        [search_text for _, search_text in records],
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    documents = [Document(page_content=text, metadata=metadata) for metadata, text in records]
    return model, vectors, documents


def create_local_retriever(top_k: int = 5) -> RunnableLambda:
    """Create a BM25 retriever over a JSON file or folder of exported JSON files."""
    if top_k < 1:
        raise ValueError("top_k must be a positive integer")

    configured_path = Path(os.getenv("LOCAL_RETRIEVAL_CORPUS", "data/silver_level"))
    corpus_path = configured_path if configured_path.is_absolute() else PROJECT_ROOT / configured_path
    mode = os.getenv("LOCAL_RETRIEVER_MODE", "bm25").strip().lower()
    if mode == "dense":
        if not corpus_path.is_file():
            raise ValueError("Dense local retrieval requires a single JSON corpus file")
        model_name = os.getenv("RAGAS_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        model, vectors, documents = _dense_index(
            str(corpus_path.resolve()), corpus_path.stat().st_mtime_ns, model_name
        )

        def retrieve_dense(query: str) -> list[Document]:
            query_vector = model.encode(str(query), normalize_embeddings=True)
            scores = vectors @ query_vector
            ranked = sorted(range(len(scores)), key=lambda index: (-float(scores[index]), index))
            return [documents[index] for index in ranked[:top_k]]

        return RunnableLambda(retrieve_dense)
    if mode != "bm25":
        raise ValueError("LOCAL_RETRIEVER_MODE must be 'bm25' or 'dense'")
    records = _read_records(corpus_path)
    documents = [_tokens(search_text) for _, search_text in records]
    langchain_documents = [
        Document(page_content=search_text, metadata=metadata)
        for metadata, search_text in records
    ]

    def retrieve(query: str) -> list[Document]:
        scores = _bm25_scores(str(query), documents)
        ranked = sorted(range(len(scores)), key=lambda index: (-scores[index], index))
        return [
            langchain_documents[index]
            for index in ranked[:top_k]
            if scores[index] > 0
        ]

    return RunnableLambda(retrieve)
