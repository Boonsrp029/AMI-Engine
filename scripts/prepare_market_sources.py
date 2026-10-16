"""Prepare a dated Thailand/ASEAN market-intelligence evaluation slice.

References are short, manually checked paraphrases of cited pages. Source PDFs
and extracted chunks remain under ignored data/external/market_sources/.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "external" / "market_sources"
DOCUMENTS = {
    "BOT_AUG_2026": {
        "file": "bot_aug_2026.pdf",
        "url": "https://www.bot.or.th/content/dam/bot/documents/en/thai-economy/state-of-thai-economy/monthly-report/macro-2026-08-press.pdf",
        "sha256": "182962527071430875386c1200cfbdfa3aa4d90616dce00f240cb525e5596012",
        "published": "2026-09-30",
    },
    "IEA_SEA_2024": {
        "file": "iea_sea_2024.pdf",
        "url": "https://iea.blob.core.windows.net/assets/ac357b64-0020-421c-98d7-f5c468dadb0f/SoutheastAsiaEnergyOutlook2024.pdf",
        "sha256": "15d45df68f8df43a499ad9ef07910f4f0ba19c6244af107bf7a50e8fa9ecf521",
        "published": "2024-10-21",
    },
}
CASES = [
    {
        "case_id": "bot-aug-2026-exports",
        "doc_name": "BOT_AUG_2026",
        "query": "According to the Bank of Thailand's August 2026 release, what supported merchandise exports and what changed in technology-related exports?",
        "reference": "Merchandise exports excluding gold remained high, supported by the global technology and AI cycle. Technology-related exports moderated after earlier strong growth, while other products increased.",
        "evidence_pages": [0],
        "evidence_terms": ["global technology", "exports of technology-related products moderated"],
        "question_reasoning": "information extraction",
    },
    {
        "case_id": "bot-aug-2026-inflation",
        "doc_name": "BOT_AUG_2026",
        "query": "What drove Thailand's rise in headline and core inflation in August 2026, according to the Bank of Thailand?",
        "reference": "Headline inflation rose with fresh-food prices affected by adverse weather and production costs, and with higher energy prices following global crude oil. Core inflation rose as businesses passed higher costs to consumers.",
        "evidence_pages": [0],
        "evidence_terms": ["fresh food prices", "higher energy prices"],
        "question_reasoning": "multi-factor synthesis",
    },
    {
        "case_id": "bot-aug-2026-demand",
        "doc_name": "BOT_AUG_2026",
        "query": "How did Thai private investment and private consumption change in August 2026, and which activities supported them?",
        "reference": "Private investment improved, especially machinery and equipment supported by the global technology cycle and data-center investment. Private consumption increased slightly, including more spending on services such as hotels and restaurants.",
        "evidence_pages": [0],
        "evidence_terms": ["higher private investment", "Private consumption also increased"],
        "question_reasoning": "multi-factor synthesis",
    },
    {
        "case_id": "iea-sea-2024-electricity",
        "doc_name": "IEA_SEA_2024",
        "query": "In the IEA's Southeast Asia Energy Outlook 2024 STEPS scenario, how is regional electricity demand projected to change by 2035?",
        "reference": "The IEA projects Southeast Asian electricity demand to grow about 4% annually to 2035, rising from over 1,300 TWh to above 2,000 TWh.",
        "evidence_pages": [6],
        "evidence_terms": ["4% annually", "2 000 TWh"],
        "question_reasoning": "numerical extraction",
    },
    {
        "case_id": "iea-sea-2024-nickel",
        "doc_name": "IEA_SEA_2024",
        "query": "What does the IEA report say about Southeast Asia's EV battery-cell capacity and Indonesia and the Philippines' nickel production?",
        "reference": "The region had 16 GWh of EV battery-cell manufacturing capacity and plans for almost 40 GWh more by 2030. Indonesia and the Philippines together produced about 65% of global mined nickel.",
        "evidence_pages": [7],
        "evidence_terms": ["16 GWh", "65%"],
        "question_reasoning": "cross-claim synthesis",
    },
    {
        "case_id": "iea-sea-2024-grids",
        "doc_name": "IEA_SEA_2024",
        "query": "Why does the IEA emphasize Southeast Asian electricity networks and regional interconnections, and what annual investment is projected by 2035?",
        "reference": "Modernized networks and regional links, including the ASEAN Power Grid, help electricity security and flexibility. Annual network investment needs more than double to about USD 22 billion by 2035 in STEPS.",
        "evidence_pages": [7],
        "evidence_terms": ["USD 22 billion", "ASEAN Power Grid"],
        "question_reasoning": "multi-factor synthesis",
    },
]


def _download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "AMI-Engine evaluation research/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read(15_000_001)
    if len(data) > 15_000_000 or not data.startswith(b"%PDF"):
        raise ValueError(f"Unexpected PDF size or content: {url}")
    path.write_bytes(data)


def _chunks(text: str, size: int = 900, overlap: int = 120) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start + size // 2, end)
            if boundary > start:
                end = boundary
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def main() -> None:
    corpus = []
    page_text = {}
    for doc_name, source in DOCUMENTS.items():
        path = SOURCE / source["file"]
        if not path.exists():
            print(f"Downloading {doc_name}", flush=True)
            _download(source["url"], path)
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != source["sha256"]:
            raise ValueError(f"Unexpected source hash for {path}: {actual}")
        reader = PdfReader(str(path))
        print(f"Extracting {doc_name}: {len(reader.pages)} pages", flush=True)
        for page_num, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            page_text[(doc_name, page_num)] = re.sub(r"\s+", " ", text).strip()
            for chunk_num, content in enumerate(_chunks(text)):
                corpus.append({
                    "feed_id": f"{doc_name}:{page_num}:{chunk_num}",
                    "title": doc_name,
                    "source": source["url"],
                    "published": source["published"],
                    "doc_name": doc_name,
                    "page_num": page_num,
                    "clean_content": content,
                })
    for case in CASES:
        evidence = " ".join(page_text[(case["doc_name"], number)] for number in case["evidence_pages"])
        for term in case["evidence_terms"]:
            if term.casefold() not in evidence.casefold():
                raise ValueError(f"Evidence term {term!r} missing for {case['case_id']}")
    out = SOURCE / "prepared"
    out.mkdir(parents=True, exist_ok=True)
    (out / "market_chunks.json").write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    (out / "market_cases.json").write_text(json.dumps(CASES, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps({
        "documents": DOCUMENTS,
        "question_count": len(CASES),
        "chunk_count": len(corpus),
        "reference_method": "manual paraphrases checked against pinned primary-source pages",
        "license_note": "IEA CC BY 4.0; BOT source retained locally for evaluation, not redistributed",
    }, indent=2), encoding="utf-8")
    print(f"Prepared {len(CASES)} cases and {len(corpus)} chunks in {out}")


if __name__ == "__main__":
    main()
