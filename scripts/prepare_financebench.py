"""Build a local filing corpus and evaluation set from the pinned FinanceBench sample.

Only the original filing PDFs enter the retriever. Benchmark answers/evidence are
kept in a separate evaluation JSON file to prevent retrieval leakage.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "external" / "financebench"
REVISION = "cc39aeb4afdf33909ee1412188bf89035950c2eb"
FILES = {
    "financebench_open_source.jsonl": "a5a2aa673e573e55675fc3c0f9aa38c1cf59d2abc91edb077534f71f10a71877",
    "financebench_document_information.jsonl": "1c69127783879de8cdadb159d2181f39bc3123b8e0ebf74031c3969d69189575",
}
DOC_NAMES = ("AES_2022_10K", "AMCOR_2023_10K", "AMD_2022_10K")
PDF_SHA256 = {
    "AES_2022_10K": "9c5de2227534c4d6bf3d805f635bad5d82eddf8e4183a85a3d1311b48b50291d",
    "AMCOR_2023_10K": "84d7a0291a12f4e68352750dccda3754c78eefdf06e0b5462046357a1ed53332",
    "AMD_2022_10K": "a3bd74088fae0ad4aa03d04998a1f4c64fd0b3c693841601b0ac49b46cf5c1f4",
}
PILOT_IDS = (
    "financebench_id_01319", "financebench_id_00540",  # Utilities: extraction, numerical
    "financebench_id_00799", "financebench_id_01148",  # Materials: numerical, extraction
    "financebench_id_00222", "financebench_id_00995",  # Technology: logical, extraction
)


def _download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "AMI-Engine evaluation research/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read(30_000_001)
    if len(data) > 30_000_000:
        raise ValueError(f"Source exceeds 30 MB limit: {url}")
    path.write_bytes(data)


def _read_jsonl(name: str) -> list[dict]:
    path = SOURCE / name
    if not path.exists():
        _download(f"https://raw.githubusercontent.com/patronus-ai/financebench/{REVISION}/data/{name}", path)
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != FILES[name]:
        raise ValueError(f"Unexpected SHA-256 for {path}: {actual}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _chunks(text: str, size: int = 900, overlap: int = 120) -> list[str]:
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


def main() -> None:
    questions = _read_jsonl("financebench_open_source.jsonl")
    metadata = {row["doc_name"]: row for row in _read_jsonl("financebench_document_information.jsonl")}
    source_shas = {}
    corpus = []
    selected = [row for row in questions if row["doc_name"] in DOC_NAMES]
    if len(selected) != 14:
        raise ValueError(f"Expected 14 selected questions, found {len(selected)}")
    for doc_name in DOC_NAMES:
        source_url = metadata[doc_name]["doc_link"]
        pdf_path = SOURCE / "pdfs" / f"{doc_name}.pdf"
        if not pdf_path.exists():
            print(f"Downloading {doc_name}", flush=True)
            _download(source_url, pdf_path)
        if not pdf_path.read_bytes().startswith(b"%PDF"):
            raise ValueError(f"Not a PDF: {pdf_path}")
        source_shas[doc_name] = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        if source_shas[doc_name] != PDF_SHA256[doc_name]:
            raise ValueError(f"Unexpected SHA-256 for {pdf_path}: {source_shas[doc_name]}")
        reader = PdfReader(str(pdf_path))
        print(f"Extracting {doc_name}: {len(reader.pages)} pages", flush=True)
        for page_num, page in enumerate(reader.pages):
            for chunk_num, content in enumerate(_chunks(page.extract_text() or "")):
                corpus.append({
                    "feed_id": f"{doc_name}:{page_num}:{chunk_num}",
                    "title": doc_name,
                    "company": metadata[doc_name]["company"],
                    "sector": metadata[doc_name]["gics_sector"],
                    "source": source_url,
                    "doc_name": doc_name,
                    "page_num": page_num,
                    "clean_content": content,
                })
    if not corpus:
        raise ValueError("PDF text extraction produced no corpus")
    dataset = []
    for row in selected:
        dataset.append({
            "case_id": row["financebench_id"],
            "query": row["question"],
            "reference": row["answer"],
            "doc_name": row["doc_name"],
            "question_type": row["question_type"],
            "question_reasoning": row["question_reasoning"],
            "evidence_pages": sorted({item["evidence_page_num"] for item in row.get("evidence", [])}),
        })
    out = SOURCE / "prepared"
    out.mkdir(parents=True, exist_ok=True)
    (out / "filing_chunks.json").write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    (out / "evaluation_cases.json").write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    pilot = [row for case_id in PILOT_IDS for row in dataset if row["case_id"] == case_id]
    if len(pilot) != len(PILOT_IDS):
        raise ValueError("Pilot selection does not match the pinned benchmark revision")
    (out / "pilot_cases.json").write_text(json.dumps(pilot, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps({
        "financebench_revision": REVISION,
        "source_jsonl_sha256": FILES,
        "pdf_sha256": source_shas,
        "documents": list(DOC_NAMES),
        "question_count": len(dataset),
        "pilot_case_ids": list(PILOT_IDS),
        "chunk_count": len(corpus),
        "license": "CC BY-NC 4.0 (FinanceBench sample); check source filing terms separately",
    }, indent=2), encoding="utf-8")
    print(f"Prepared {len(dataset)} questions and {len(corpus)} filing chunks in {out}")


if __name__ == "__main__":
    main()
