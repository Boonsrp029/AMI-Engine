"""Reconstruct only exact overlapping chunks on one pinned document page."""
import hashlib
import json


def assemble(records, minimum_overlap=32, maximum_chars=3000):
    if len(records) < 2:
        return None
    for field in ("doc_name", "page_num", "url", "published"):
        if any(r.get(field) != records[0].get(field) for r in records):
            return None
    if not records[0].get("doc_name") or type(records[0].get("page_num")) is not int or records[0]["page_num"] < 0:
        return None
    ordinals = [r["source_id"].rpartition(":") for r in records]
    if any(not sep or not index.isdigit() for _, sep, index in ordinals) or len({prefix for prefix, _, _ in ordinals}) != 1:
        return None
    ordered = sorted(records, key=lambda r: int(r["source_id"].rpartition(":")[2]))
    numbers = [int(r["source_id"].rpartition(":")[2]) for r in ordered]
    if numbers != list(range(numbers[0], numbers[0] + len(numbers))):
        return None
    text, members = "", []
    for record in ordered:
        original = record["content"]
        overlap = 0
        if text:
            overlap = next((size for size in range(min(len(text), len(original)), minimum_overlap - 1, -1)
                            if text[-size:] == original[:size]), 0)
            if not overlap:
                return None
        start = len(text) - overlap
        text += original[overlap:]
        if len(text) > maximum_chars:
            return None
        members.append({"source_id": record["source_id"], "content_sha256": hashlib.sha256(original.encode()).hexdigest(),
            "overlap_chars": overlap, "context_start": start, "context_end": start + len(original)})
        assert text[start:start + len(original)] == original
    provenance = {"method": "exact_overlap_same_page_v1", "members": members,
                  "content_sha256": hashlib.sha256(text.encode()).hexdigest()}
    identity = hashlib.sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()
    return {**ordered[0], "source_id": "context:" + identity[:16], "content": text, "provenance": provenance}
