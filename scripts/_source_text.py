"""Private text chunking shared by the two source-preparation commands."""

from __future__ import annotations

import re


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    result = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        result.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return result

