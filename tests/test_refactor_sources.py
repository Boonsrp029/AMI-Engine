"""Source preparation parity using tiny local stand-ins for downloaded PDFs."""

import hashlib
import io
import json
import os
import runpy
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import prepare_financebench, prepare_market_sources


FIXTURE = Path(__file__).parent / "fixtures" / "refactor" / "sources.json"


def observe_sources(root, monkeypatch, kind):
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(root)
    source = Path("sources")
    source.mkdir()
    module = prepare_financebench if kind == "financebench" else prepare_market_sources
    monkeypatch.setattr(module, "SOURCE", source)
    pages = ["First   synthetic sentence about nickel.\nSecond sentence about grids.", ""]
    monkeypatch.setattr(module, "PdfReader", lambda _: SimpleNamespace(pages=[
        SimpleNamespace(extract_text=lambda text=text: text) for text in pages]))
    if kind == "financebench":
        names = module.DOC_NAMES
        questions = [{"financebench_id": f"case-{i}", "doc_name": names[i % 3],
            "question": f"Question {i}?", "answer": f"Reference {i}", "question_type": "extract",
            "question_reasoning": "simple", "evidence": [{"evidence_page_num": 0}]} for i in range(14)]
        metadata = [{"doc_name": name, "doc_link": f"https://example.invalid/{i}.pdf",
                     "company": f"Company {i}", "gics_sector": "Synthetic"} for i, name in enumerate(names)]
        monkeypatch.setattr(module, "_read_jsonl", lambda filename:
                            questions if filename == "financebench_open_source.jsonl" else metadata)
        monkeypatch.setattr(module, "PILOT_IDS", tuple(f"case-{i}" for i in range(6)))
        hashes = {}
        (source / "pdfs").mkdir()
        for name in names:
            data = b"%PDF-synthetic " + name.encode()
            (source / "pdfs" / f"{name}.pdf").write_bytes(data)
            hashes[name] = hashlib.sha256(data).hexdigest()
        monkeypatch.setattr(module, "PDF_SHA256", hashes)
    else:
        documents = {name: dict(metadata) for name, metadata in module.DOCUMENTS.items()}
        cases = []
        for name, metadata in documents.items():
            data = b"%PDF-synthetic " + name.encode()
            (source / metadata["file"]).write_bytes(data)
            metadata["sha256"] = hashlib.sha256(data).hexdigest()
            cases.append({"case_id": name, "doc_name": name, "query": "What about nickel?",
                          "reference": "Synthetic nickel.", "evidence_pages": [0], "evidence_terms": ["nickel"]})
        monkeypatch.setattr(module, "DOCUMENTS", documents)
        monkeypatch.setattr(module, "CASES", cases)
    output = io.StringIO()
    with redirect_stdout(output):
        module.main()
    files = {p.name: p.read_text(encoding="utf-8") for p in sorted((source / "prepared").iterdir())}
    for name, text in files.items():
        assert (source / "prepared" / name).read_bytes() == text.replace("\n", os.linesep).encode("utf-8")
    return {"stdout": output.getvalue().replace(str(source / "prepared"), "sources/prepared"), "files": files}


@pytest.mark.parametrize("kind", ["financebench", "market"])
def test_preparation_matches_original_artifacts(tmp_path, monkeypatch, kind):
    assert observe_sources(tmp_path, monkeypatch, kind) == json.loads(FIXTURE.read_text(encoding="utf-8"))[kind]


@pytest.mark.parametrize("text,size,overlap,expected", [
    ("", 900, 120, []),
    (" \t\n", 900, 120, []),
    ("α\nβ\tγ", 900, 120, ["α β γ"]),
    ("abcdefghijk", 6, 2, ["abcdef", "efghij", "ijk"]),
    ("one two three four", 10, 2, ["one two", "wo three", "ee four"]),
    ("exact-size", 10, 0, ["exact-size"]),
])
def test_chunk_boundaries_and_whitespace(text, size, overlap, expected):
    for module in (prepare_financebench, prepare_market_sources):
        assert module._chunks(text, size, overlap) == expected


@pytest.mark.parametrize("module", [prepare_financebench, prepare_market_sources])
def test_direct_script_import_context(monkeypatch, module):
    # run_path with the script directory on sys.path reproduces direct Python
    # script import resolution without executing its downloading main block.
    monkeypatch.syspath_prepend(str(Path(module.__file__).parent))
    exported = runpy.run_path(module.__file__)
    assert exported["_chunks"]("same  words") == ["same words"]
