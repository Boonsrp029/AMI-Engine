"""Preparation failures cannot overwrite evidence or leak answer keys into retrieval."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts.prepare_release_evaluation import freeze, html_units


def test_article_boundaries_exclude_navigation_scripts_and_keep_unicode():
    raw = ("<h1>Report</h1><div>Navigation</div><h1>Report</h1>"
           "<p>Thailand’s value is 12.5%.</p><script>ReferenceAnswerLeak()</script>"
           "<h2>End of article</h2><p>Footer</p>").encode()
    units = html_units(raw, {"start": "Report", "stop": "End of article"})
    assert [u["text"] for u in units] == ["Report", "Thailand’s value is 12.5%."]
    assert all(u["locator"]["kind"] == "html" for u in units)
    with pytest.raises(ValueError, match="article start"):
        html_units(b"<html><script>browser challenge</script></html>", {"start": "Report", "stop": "End"})
    with pytest.raises(ValueError, match="article end"):
        html_units(b"<h1>Report</h1><p>Missing boundary</p>", {"start": "Report", "stop": "End"})


def fixture_spec(tmp_path):
    raw = b"<h1>Fixture report</h1><p>A synthetic value is 12.5%.</p><h2>End</h2>"
    (tmp_path/"fixture.html").write_bytes(raw)
    doc = {"file": "fixture.html", "url": "https://example.invalid/fixture", "published": "2025-01-01",
           "format": "html", "start": "Fixture report", "stop": "End"}
    spec = {"version": "synthetic-preparation-test", "dataset_root": str(tmp_path), "documents": {"FIXTURE": doc},
            "heldout": [{"case_id": f"test-{i}", "category": "answerable", "expected_action": "answer",
                         "corpus": "public", "query": f"Synthetic preparation test question {i}?",
                         "reference": "NeverRetrievedReferenceAnswer", "checks": ["synthetic"],
                         "locators": [{"doc_name": "FIXTURE", "anchor": "12.5%"}]} for i in range(20)],
            "preflights": [], "synthetic_corpora": {}, "freshness_scope": "synthetic test only"}
    lock = {"sources": {"FIXTURE": {k: doc[k] for k in ("file", "url", "published")}}}
    lock["sources"]["FIXTURE"]["sha256"] = hashlib.sha256(raw).hexdigest()
    spec_path = tmp_path/"spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    (tmp_path/"source-lock.json").write_text(json.dumps(lock), encoding="utf-8")
    return spec_path


def test_frozen_hashes_and_reference_separation_with_immutable_outputs(tmp_path):
    spec_path = fixture_spec(tmp_path)
    output = tmp_path/"frozen"
    manifest = freeze(spec_path, output)
    assert manifest["heldout_count"] == 20
    corpus = (output/"corpora/public.json").read_text(encoding="utf-8")
    assert "NeverRetrievedReferenceAnswer" not in corpus and '"reference"' not in corpus
    for name, expected in manifest["sha256"].items():
        assert hashlib.sha256((output/name).read_bytes()).hexdigest() == expected
    for case in json.loads((output/"cases.json").read_text(encoding="utf-8")):
        evidence = case["evidence"][0]
        unit = next(u for u in json.loads((output/"source-units.json").read_text(encoding="utf-8"))
                    if u["unit_id"] == evidence["unit_id"])
        assert unit["text"][evidence["start"]:evidence["end"]] == "12.5%"
    before = (output/"cases.json").read_bytes()
    with pytest.raises(ValueError, match="overwrite"):
        freeze(spec_path, output)
    assert (output/"cases.json").read_bytes() == before


def test_bad_source_hash_or_locator_fails_before_frozen_output_exists(tmp_path):
    spec_path = fixture_spec(tmp_path)
    path = tmp_path/"fixture.html"
    original = path.read_bytes()
    path.write_bytes(original + b"tamper")
    output = tmp_path/"frozen"
    with pytest.raises(ValueError, match="hash mismatch"):
        freeze(spec_path, output)
    assert not output.exists()
    path.write_bytes(original)
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    spec["heldout"][0]["locators"][0]["anchor"] = "not in source"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    with pytest.raises(ValueError, match="Unresolved evidence locator"):
        freeze(spec_path, output)
    assert not output.exists()
