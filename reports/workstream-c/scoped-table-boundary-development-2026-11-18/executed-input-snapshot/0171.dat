"""Read-only, corpus-pinned retrieval callback for ami-subtasks-v1.

The adapter deliberately keeps only its configured path as instance state so
it can be sent to the stored runner's spawned worker. Each call reads a fresh
snapshot and uses the existing local BM25 tokenizer and scorer.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from urllib.parse import urlparse

from src.agents.local_retriever import _bm25_scores, _read_records, _tokens
from .contracts import Result, Source, digest


_MAX_SOURCES = 5


def _content(row: dict) -> str:
    value = row.get("clean_content") or row.get("raw_content") or row.get("aggregated_context")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Corpus row has no searchable source content")
    return value


def _url(row: dict) -> str:
    value = row.get("url") or row.get("source")
    if value in (None, ""):
        return ""
    if not isinstance(value, str):
        raise ValueError("Corpus URL metadata must be text")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Corpus source URLs must not embed credentials")
    return value


def _read_snapshot(path: Path):
    if not path.is_file():
        raise ValueError("Configured corpus must be a single readable JSON file")
    raw_bytes = path.read_bytes()
    sha = hashlib.sha256(raw_bytes).hexdigest()
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Configured corpus is not valid UTF-8 JSON") from exc
    rows = payload if isinstance(payload, list) else [payload]
    if not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Corpus must contain source-record objects")

    # _read_records is the project's canonical metadata normalization and BM25
    # document builder. Fail closed on rows it would silently skip so a pinned
    # corpus cannot change meaning through partial ingestion.
    for row in rows:
        _content(row)
    normalized = _read_records(path)
    if len(normalized) != len(rows):
        raise ValueError("Corpus row normalization did not preserve every record")
    if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
        raise ValueError("Corpus changed while the local snapshot was loading")

    layer = path.parent.name.removesuffix("_level")
    source_map = {}
    documents = []
    for index, ((metadata, search_text), row) in enumerate(zip(normalized, rows, strict=True), 1):
        expected_content = _content(row)
        expected_id = str(row.get("feed_id") or f"{layer}:{index}")
        source_id = str(metadata.get("feed_id"))
        expected_search = f"{metadata.get('title', '')} {expected_content}".strip()
        if source_id != expected_id or search_text != expected_search:
            raise ValueError("Local retriever normalization disagrees with source records")
        if source_id in source_map:
            raise ValueError("Corpus source IDs must be unique")
        title = metadata.get("title") or ""
        if not isinstance(title, str):
            raise ValueError("Corpus title metadata must be text")
        published = row.get("published")
        if published is not None and not isinstance(published, str):
            raise ValueError("Corpus published metadata must be text")
        doc_name = row.get("doc_name")
        if doc_name is not None and not isinstance(doc_name, str):
            raise ValueError("Corpus document-name metadata must be text")
        page_num = row.get("page_num")
        if page_num is not None and (type(page_num) is not int or page_num < 0):
            raise ValueError("Corpus page metadata must be a zero-based nonnegative integer")
        source_map[source_id] = {
            "source_id": source_id,
            "content": expected_content,
            "content_sha256": digest(expected_content),
            "corpus_sha256": sha,
            "role": "support",
            "title": title,
            # `source` in the current export is a publisher label. Only a
            # separately supplied absolute HTTP(S) URL is exposed as a URL.
            "url": _url(row),
            "published": published,
            "doc_name": doc_name,
            "page_num": page_num,
        }
        documents.append(_tokens(search_text))
    if not source_map:
        raise ValueError("No searchable source records found in local corpus")
    return sha, source_map, documents


def _check_active(context):
    if context.cancelled():
        raise TimeoutError("Subtask was cancelled or its deadline expired")


def _dependency_sources(context, snapshot_sources):
    declared = context.task.dependencies
    dependencies = context.dependencies
    if not declared or tuple(result.subtask_id for result in dependencies) != declared:
        raise ValueError("Source inspection requires its declared completed dependencies")
    candidates = {}
    for result in dependencies:
        if result.identity != context.identity:
            raise ValueError("Dependency belongs to a different run, attempt, plan, or corpus")
        for source in result.sources:
            previous = candidates.get(source.source_id)
            if previous is not None and previous.model_dump(exclude={"role"}) != source.model_dump(exclude={"role"}):
                raise ValueError("Dependency source identity collision")
            if previous is None or source.role == "support":
                candidates[source.source_id] = source

    selected = []
    for source_id in context.task.source_ids:
        dependency_source = candidates.get(source_id)
        if dependency_source is None:
            raise ValueError("Requested inspection source is not in a declared dependency")
        canonical = snapshot_sources.get(source_id)
        if canonical is None:
            raise ValueError("Dependency source no longer exists in the pinned corpus")
        expected = Source(**{**canonical, "role": dependency_source.role})
        if expected.model_dump() != dependency_source.model_dump():
            raise ValueError("Dependency source does not match the pinned corpus record")
        selected.append(expected)
    return tuple(selected)


class LocalBM25Adapter:
    """Picklable callback implementing bounded local retrieve/inspect operations."""

    def __init__(self, corpus_path: str | Path):
        self.corpus_path = str(Path(corpus_path).resolve())

    def __call__(self, context) -> Result:
        started = time.monotonic()
        _check_active(context)
        path = Path(self.corpus_path)
        sha, raw_sources, documents = _read_snapshot(path)
        if sha != context.identity.corpus_sha256:
            raise ValueError("Configured corpus does not match the launched corpus identity")
        _check_active(context)

        if context.task.operation == "retrieve":
            scores = _bm25_scores(context.task.query, documents)
            ranked = sorted(range(len(documents)), key=lambda index: (-scores[index], index))
            ids = list(raw_sources)
            selected = tuple(
                Source(**raw_sources[ids[index]])
                for index in ranked[:_MAX_SOURCES]
                if scores[index] > 0
            )
            outcome = "evidence" if selected else "missing"
            diagnostic = "none" if selected else "no_matching_evidence"
        elif context.task.operation == "inspect_sources":
            selected = _dependency_sources(context, raw_sources)
            outcome = "evidence" if any(source.role == "support" for source in selected) else "missing"
            diagnostic = "none"
        else:  # Pydantic currently prevents this; keep the adapter fail-closed.
            raise ValueError("Unsupported retrieval operation")

        _check_active(context)
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValueError("Configured corpus changed before retrieval could return")
        _check_active(context)
        elapsed = max(0.0, time.monotonic() - started)
        return Result(
            identity=context.identity,
            subtask_id=context.task.subtask_id,
            child_attempt_id=context.child_attempt_id,
            dependencies=context.dependency_refs,
            outcome=outcome,
            sources=selected,
            elapsed_seconds=elapsed,
            diagnostic=diagnostic,
        )
