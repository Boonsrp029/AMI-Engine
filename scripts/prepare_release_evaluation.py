"""Verify pinned sources and freeze new cases/corpora; never runs a model.

Complete publisher snapshots stay in ignored data/external. References are kept
separate from retrieval corpora. A completed output directory is immutable.
"""
import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import ssl
from urllib.request import Request, urlopen

from pypdf import PdfReader

try:
    from scripts._source_text import chunk_text
except ModuleNotFoundError:
    from _source_text import chunk_text


class SourceText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self.skip += 1
        elif not self.skip and tag in {"p", "h1", "h2", "h3", "h4", "li", "div", "section", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.skip = max(0, self.skip - 1)
        elif not self.skip and tag in {"p", "h1", "h2", "h3", "h4", "li", "div", "section"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def normalize(value):
    return re.sub(r"\s+", " ", value).strip()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def html_units(raw, document):
    parser = SourceText()
    parser.feed(raw.decode("utf-8"))
    lines = [line for part in "".join(parser.parts).splitlines() if (line := normalize(part))]
    starts = [i for i, line in enumerate(lines) if line == document["start"]]
    if not starts:
        raise ValueError("Pinned HTML lacks the declared article start")
    start = starts[-1]  # Excludes repeated navigation/article-title copies.
    stop = next((i for i in range(start+1, len(lines)) if lines[i] == document["stop"]), None)
    if stop is None:
        raise ValueError("Pinned HTML lacks the declared article end")
    controls = {"Openexpand", "Chevron down 16"}
    return [{"text": line, "locator": {"kind": "html", "article_paragraph": number,
             "extracted_line": line_index+1}}
            for number, (line_index, line) in enumerate(
                ((i, lines[i]) for i in range(start, stop) if lines[i] not in controls), 1)]


def freeze(spec_path, output, ca_file=None):
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    source_lock_path = spec_path.with_name("source-lock.json")
    lock = json.loads(source_lock_path.read_text(encoding="utf-8"))
    root = Path(spec["dataset_root"])
    if output.exists():
        raise ValueError("Use a new output directory; do not overwrite a frozen or partial package")
    # Verify ALL inputs and locators before creating any frozen output.
    units, documents = [], {}
    for name, document in spec["documents"].items():
        pinned = lock["sources"][name]
        if any(pinned[k] != document[k] for k in ("file", "url", "published")):
            raise ValueError("Source lock disagrees with specification")
        path = root/document["file"]
        if not path.exists():
            request = Request(document["url"], headers={"User-Agent": "AMI-Engine pinned public-source evaluation/1.0"})
            context = ssl.create_default_context(cafile=ca_file)
            with urlopen(request, context=context, timeout=45) as response:
                data = response.read(15_000_001)
            if len(data) > 15_000_000 or hashlib.sha256(data).hexdigest() != pinned["sha256"]:
                raise ValueError("Downloaded source differs from the lock; retain separately for review")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if sha(path) != pinned["sha256"]:
            raise ValueError(f"Pinned source hash mismatch: {name}")
        if document["format"] == "html":
            extracted = html_units(path.read_bytes(), document)
        else:
            extracted = [{"text": normalize(page.extract_text() or ""),
                          "locator": {"kind": "pdf", "page_num": i, "pdf_page": i+1}}
                         for i, page in enumerate(PdfReader(path).pages)]
        for i, unit in enumerate(extracted):
            unit.update(unit_id=f"{name}:unit:{i}", doc_name=name, url=document["url"],
                        published=document["published"], raw_sha256=pinned["sha256"])
        units.extend(extracted)
        documents[name] = {**pinned, "format": document["format"], "unit_count": len(extracted)}

    corpora = {"public": []}
    for unit in units:
        for i, text in enumerate(chunk_text(unit["text"])):
            row = {"feed_id": f"{unit['unit_id']}:{i}", "title": unit["doc_name"],
                   "doc_name": unit["doc_name"], "source": unit["url"], "published": unit["published"],
                   "clean_content": text}
            if unit["locator"]["kind"] == "pdf":
                row["page_num"] = unit["locator"]["page_num"]
            corpora["public"].append(row)
    synthetic = dict(spec["synthetic_corpora"])
    synthetic.update({case["corpus"]: case["records"] for case in spec["preflights"]})
    for corpus_name, records in synthetic.items():
        corpora[corpus_name] = []
        for i, record in enumerate(records):
            assert "SYNTHETIC" in record["text"]
            unit = {"unit_id": f"{record['doc_name']}:unit:0", "text": record["text"],
                    "doc_name": record["doc_name"], "url": f"https://example.invalid/{record['doc_name']}",
                    "published": record["published"], "locator": {"kind": "synthetic", "record": i},
                    "raw_sha256": hashlib.sha256(record["text"].encode()).hexdigest()}
            units.append(unit)
            corpora[corpus_name].append({"feed_id": f"{record['doc_name']}:0", "title": record["doc_name"],
                "doc_name": record["doc_name"], "published": record["published"], "source": unit["url"],
                "clean_content": record["text"]})

    cases = []
    for split, selected in (("heldout", spec["heldout"]), ("preflight", spec["preflights"])):
        for original in selected:
            case = {k: v for k, v in original.items() if k != "records"}
            case["split"] = split
            case["evidence"] = []
            for locator in case["locators"]:
                candidates = [u for u in units if u["doc_name"] == locator["doc_name"] and
                    ("pdf_index" not in locator or u["locator"].get("page_num") == locator["pdf_index"])]
                matches = [u for u in candidates if locator["anchor"] in u["text"]]
                if not matches:
                    raise ValueError(f"Unresolved evidence locator: {case['case_id']}: {locator}")
                unit = matches[-1] if locator.get("occurrence") == "last" else matches[0]
                start = unit["text"].index(locator["anchor"])
                case["evidence"].append({"unit_id": unit["unit_id"], "locator": unit["locator"],
                    "anchor": locator["anchor"], "start": start, "end": start+len(locator["anchor"])})
            cases.append(case)
    if len({c["case_id"] for c in cases}) != len(cases) or len(spec["heldout"]) < 20:
        raise ValueError("Duplicate IDs or fewer than twenty held-out cases")
    old = json.loads(Path("data/pilot/cases.json").read_text(encoding="utf-8"))
    if {c["query"].casefold() for c in old} & {c["query"].casefold() for c in cases}:
        raise ValueError("New set repeats a previous question")
    output.mkdir(parents=True)
    write(output/"cases.json", cases)
    write(output/"source-units.json", units)
    write(output/"sources.json", documents)
    for name, records in corpora.items():
        write(output/"corpora"/(name+".json"), records)
    files = sorted(p for p in output.rglob("*") if p.is_file())
    manifest = {"version": spec["version"], "status": "frozen; no answers generated",
        "spec_sha256": sha(spec_path), "source_lock_sha256": sha(source_lock_path),
        "sha256": {p.relative_to(output).as_posix(): sha(p) for p in files},
        "heldout_count": len(spec["heldout"]), "preflight_count": len(spec["preflights"]),
        "categories": dict(Counter(c["category"] for c in spec["heldout"])),
        "freshness_scope": spec["freshness_scope"], "prior_question_overlap": 0,
        "reference_and_answer_fields_in_corpora": False,
        "source_licensing": "IEA CC BY 4.0 with attribution; publisher snapshots/excerpts retained locally, not redistributed"}
    write(output/"manifest.json", manifest)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=Path("data/pilot/release-2026-10-27/spec.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ca-file", help="Trusted CA bundle if system certificate verification fails; TLS is never disabled")
    args = parser.parse_args(argv)
    result = freeze(args.spec, args.output, args.ca_file)
    print(json.dumps({k: result[k] for k in ("heldout_count", "preflight_count", "categories", "prior_question_overlap")}))


if __name__ == "__main__":
    main()
