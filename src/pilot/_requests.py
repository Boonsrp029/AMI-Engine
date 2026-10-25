"""Canonical verbatim request slots, without inferring entities or evidence."""
import re


def requested_components(question):
    text = question.strip()
    if not text:
        raise ValueError("A nonempty question is required")
    # Split only explicit new interrogative clauses, preserving compound subjects.
    separator = re.compile(r",?\s+\b(?:and|but)\s+(?=(?:what|which|how|why|when|where|who)\b)|(?<=\?)\s+(?=(?:what|which|how|why|when|where|who)\b)", re.I)
    parts = [part.strip(" ,") for part in separator.split(text) if part.strip(" ,")]
    if len(parts) > 5:
        parts = [text]  # Keep the whole request rather than silently dropping clauses.
    return [{"component_id": f"r{index}", "question_anchor": part} for index, part in enumerate(parts, 1)]
